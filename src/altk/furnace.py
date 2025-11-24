import logging
from typing import Sequence, Tuple, Union, List, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from numpy.typing import NDArray
from pandas import DataFrame

from altk.utils._exceptions import DataFileInvalid

Number = Union[int, float]
Array2D = NDArray[np.floating]
ZoomAreaLike = Union[Tuple[Number, Number], Tuple[Number, Number, Number, Number]]
FigOrSubFig = Union[Figure, SubFigure]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZoomArea:
    """Normalized zoom area definition.

    Attributes:
        x1 (float): Left boundary in data coordinates.
        y1 (float): Bottom boundary in data coordinates.
        x2 (float): Right boundary in data coordinates.
        y2 (float): Top boundary in data coordinates.
    """

    x1: float
    y1: float
    x2: float
    y2: float


def read_program_data(file: str):
    logger.info(f'Reading from "{file}"')
    df = pd.read_csv(file)
    required = {"temperature", "time"}
    missing = required - set(df.columns)
    logger.debug(f"{missing}")
    logger.debug(f"{set(df.columns)}")
    if missing:
        raise DataFileInvalid(f"Required columns missing: {missing}")

    seq_array = df[["time", "temperature"]].to_numpy()
    return seq_array


def write_program_to_csv():
    pass


def plot_furnace_program(
    fig: FigOrSubFig,
    sequences: Sequence[Array2D],
    zoom_areas: Optional[Sequence[ZoomAreaLike]] = None,
    *,
    colors: Optional[Sequence[str]] = None,
    y_round_digits: int = 6,
) -> None:
    """Plot furnace programs with an optional main + zoom layout.

    This function draws one main furnace program plot and, if requested,
    several zoomed-in subplots arranged below the main axes. Each zoom area
    can be specified either as an explicit (x1, y1, x2, y2) bounding box,
    or only by its horizontal range (x1, x2). In the latter case, the
    vertical limits are determined from all input sequences and then padded.

    For each axes (main and zoom), all sequences are plotted.
    Projection lines from key points to the local x/y axes are drawn with
    de-duplication:
        * Points sharing the same y value share one horizontal projection.
        * Points sharing the same x value share one vertical projection.

    Args:
        fig (FigOrSubFig): Target Matplotlib Figure or SubFigure.
        sequences (Sequence[Array2D]): A list of furnace sequences.
            Each sequence is a NumPy array with shape (N, 2), where
            ``[:, 0]`` is time and ``[:, 1]`` is temperature.
        zoom_areas (Sequence[ZoomAreaLike], optional): A list of zoom
            specifications. Each element can be either
                * (x1, x2), or
                * (x1, y1, x2, y2).
            See module docstring for normalization rules.
        colors (Sequence[str], optional): Optional color cycle override for
            the sequences. If provided, its length may be smaller than the
            number of sequences; colors are cycled.
        y_round_digits (int): Number of decimal digits used when grouping
            y values for horizontal projection de-duplication.

    Returns:
        None: The function draws on the given figure but does not return it.
    """
    if not sequences:
        logger.warning("No sequences provided; nothing will be plotted.")
        return

    _validate_sequences(sequences)

    # Normalize zoom areas if provided.
    normalized_zoom_areas: List[ZoomArea] = []
    if zoom_areas:
        normalized_zoom_areas = _normalize_zoom_areas(
            sequences, zoom_areas, padding_fraction_x=0.2
        )
        # Sort zoom areas by x1 for nicer layout (left to right).
        normalized_zoom_areas.sort(key=lambda area: area.x1)

    if not normalized_zoom_areas:
        # Single-axes case: only main plot.
        ax = fig.add_subplot(111)
        _plot_program_single(
            ax=ax,
            sequences=sequences,
            color_cycle=colors,
            xy_range=None,
            draw_total_time=True,
            draw_projections=True,
            y_round_digits=y_round_digits,
        )
        return

    # Layout: main axes on top, zoom axes in a row below.
    n_zoom = len(normalized_zoom_areas)
    gs = GridSpec(
        2,
        n_zoom,
        height_ratios=[3, 2],
        wspace=0.5
        # figure=fig, # type: ignore[arg-type]
    )
    ax_main = fig.add_subplot(gs[0, :])

    _plot_program_single(
        ax=ax_main,
        sequences=sequences,
        color_cycle=colors,
        xy_range=None,
        draw_total_time=True,
        draw_projections=True,
        y_round_digits=y_round_digits,
    )

    # Draw zoom rectangles on the main axes.
    for area in normalized_zoom_areas:
        rect = Rectangle(
            (area.x1, area.y1),
            width=area.x2 - area.x1,
            height=area.y2 - area.y1,
            fill=False,
            linewidth=1.0,
            linestyle="--",
            alpha=0.7,
        )
        ax_main.add_patch(rect)

    # Create zoom axes and plot.
    zoom_axes: List[Axes] = []
    for i, area in enumerate(normalized_zoom_areas):
        ax_zoom = fig.add_subplot(gs[1, i])
        zoom_axes.append(ax_zoom)
        _plot_program_single(
            ax=ax_zoom,
            sequences=sequences,
            color_cycle=colors,
            xy_range=(area.x1, area.y1, area.x2, area.y2),
            draw_total_time=False,
            draw_projections=True,
            y_round_digits=y_round_digits,
        )

    # Connect main rectangles to zoom axes with lines in figure coordinates.
    for ax_zoom, area in zip(zoom_axes, normalized_zoom_areas):
        _connect_main_and_zoom(fig, ax_main, ax_zoom, area)


def _validate_sequences(sequences: Sequence[Array2D]) -> None:
    """Validate that all sequences are two-column arrays."""
    for idx, seq in enumerate(sequences):
        if seq.ndim != 2 or seq.shape[1] != 2:
            msg = f"Sequence at index {idx} must have shape (N, 2), got {seq.shape}"
            raise ValueError(msg)


def _normalize_zoom_areas(
    sequences: Sequence[Array2D],
    zoom_areas: Sequence[ZoomAreaLike],
    padding_fraction_x: float = 0.0,
    padding_fraction_y: float = 0.1,
) -> List[ZoomArea]:
    """Normalize zoom area definitions into full (x1, y1, x2, y2) boxes.

    If a zoom area is given as (x1, x2), the vertical range is computed
    from all sequences with x in [x1, x2]. After obtaining (x1, x2, y1, y2),
    padding is added in all four directions according to ``padding_fraction``.

    Args:
        sequences (Sequence[Array2D]): Input furnace sequences.
        zoom_areas (Sequence[ZoomAreaLike]): Raw zoom area definitions.
        padding_fraction (float): Fraction by which to expand each side
            of the bounding box.

    Returns:
        List[ZoomArea]: A list of normalized zoom areas.
    """
    all_x = np.concatenate([seq[:, 0] for seq in sequences])
    all_y = np.concatenate([seq[:, 1] for seq in sequences])
    global_xmin, global_xmax = float(all_x.min()), float(all_x.max())
    global_ymin, global_ymax = float(all_y.min()), float(all_y.max())

    normalized: List[ZoomArea] = []

    for area in zoom_areas:
        if len(area) == 2:
            x1_raw, x2_raw = float(area[0]), float(area[1])
            if x2_raw < x1_raw:
                x1_raw, x2_raw = x2_raw, x1_raw

            # Collect all points in this x-range across all sequences.
            xs_in_range: List[float] = []
            ys_in_range: List[float] = []
            for seq in sequences:
                mask = (seq[:, 0] >= x1_raw) & (seq[:, 0] <= x2_raw)
                xs_in_range.extend(seq[mask, 0].tolist())
                ys_in_range.extend(seq[mask, 1].tolist())

            if not ys_in_range:
                # Fallback: use global y range if this x-range contains no point.
                y1_raw, y2_raw = global_ymin, global_ymax
            else:
                y1_raw = float(min(ys_in_range))
                y2_raw = float(max(ys_in_range))

            x1, y1, x2, y2 = x1_raw, y1_raw, x2_raw, y2_raw
        elif len(area) == 4:
            x1_raw,  x2_raw, y1_raw, y2_raw = map(float, area)
            if x2_raw < x1_raw:
                x1_raw, x2_raw = x2_raw, x1_raw
            if y2_raw < y1_raw:
                y1_raw, y2_raw = y2_raw, y1_raw
            x1, y1, x2, y2 = x1_raw, y1_raw, x2_raw, y2_raw
        else:
            raise ValueError(
                f"Zoom area must be either (x1, x2) or (x1, x2, y1, y2). Got {area!r}"
            )

        # Clamp to global ranges to avoid going too far out.
        x1 = max(x1, global_xmin)
        x2 = min(x2, global_xmax)
        y1 = max(y1, global_ymin)
        y2 = min(y2, global_ymax)

        # Expand the box by padding_fraction on all sides.
        dx = (x2 - x1) * padding_fraction_x
        dy = (y2 - y1) * padding_fraction_y

        x1 -= dx
        x2 += dx
        y1 -= dy
        y2 += dy

        normalized.append(ZoomArea(x1=x1, y1=y1, x2=x2, y2=y2))

    return normalized


def _plot_program_single(
    ax: Axes,
    sequences: Sequence[Array2D],
    color_cycle: Optional[Sequence[str]],
    xy_range: Optional[Tuple[float, float, float, float]],
    *,
    draw_total_time: bool,
    draw_projections: bool,
    y_round_digits: int,
) -> None:
    """Plot all sequences on a single axes with optional decorations.

    Args:
        ax (Axes): Target Matplotlib Axes.
        sequences (Sequence[Array2D]): Furnace sequences (N, 2).
        color_cycle (Sequence[str], optional): Optional colors for lines.
        xy_range (tuple[float, float, float, float] | None): Optional
            explicit (x1, y1, x2, y2) range for this axes.
        draw_total_time (bool): Whether to draw a total time arrow on top.
        draw_projections (bool): Whether to draw x/y-axis projection lines.
        y_round_digits (int): Decimal digits used for grouping y values.
    """
    # Draw curves.
    _draw_sequences(ax, sequences, color_cycle=color_cycle)

    # Set ranges: either from given xy_range or from data with a small padding.
    if xy_range is not None:
        x1, y1, x2, y2 = xy_range
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1, y2)
    else:
        all_x = np.concatenate([seq[:, 0] for seq in sequences])
        all_y = np.concatenate([seq[:, 1] for seq in sequences])
        x1, x2 = float(all_x.min()), float(all_x.max())
        y1, y2 = float(all_y.min()), float(all_y.max())
        dx = (x2 - x1) * 0.05
        dy = (y2 - y1) * 0.05
        ax.set_xlim(x1 - dx, x2 + dx)
        ax.set_ylim(y1 - dy, y2 + dy)

    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature")

    if draw_projections:
        _draw_projection_lines(ax, sequences, y_round_digits=y_round_digits)

    if draw_total_time:
        _draw_total_time_arrow(ax)


def _draw_sequences(
    ax: Axes,
    sequences: Sequence[Array2D],
    color_cycle: Optional[Sequence[str]] = None,
) -> None:
    """Draw all furnace sequences on a given axes."""
    if color_cycle is None or not color_cycle:
        for seq in sequences:
            ax.plot(seq[:, 0], seq[:, 1])
    else:
        n_colors = len(color_cycle)
        for i, seq in enumerate(sequences):
            color = color_cycle[i % n_colors]
            ax.plot(seq[:, 0], seq[:, 1], color=color)


def _draw_projection_lines(
    ax: Axes,
    sequences: Sequence[Array2D],
    *,
    y_round_digits: int,
) -> None:
    """Draw de-duplicated projection lines from key points to axes.

    Horizontal lines:
        * Group points by rounded y value.
        * For each group, draw a single line from x = xmin to x = max(x).

    Vertical lines:
        * Group points by rounded x value.
        * For each group, draw a single line from y = ymin to y = max(y).
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_min_axis, y_min_axis = xlim[0], ylim[0]

    # Collect points inside current view to avoid clutter from off-screen data.
    xs: List[float] = []
    ys: List[float] = []
    for seq in sequences:
        xs.extend(seq[:, 0].tolist())
        ys.extend(seq[:, 1].tolist())

    xs_arr = np.asarray(xs, dtype=float)
    ys_arr = np.asarray(ys, dtype=float)

    # Mask to keep only visible (or nearly visible) points.
    mask = (
        (xs_arr >= xlim[0])
        & (xs_arr <= xlim[1])
        & (ys_arr >= ylim[0])
        & (ys_arr <= ylim[1])
    )
    xs_visible = xs_arr[mask]
    ys_visible = ys_arr[mask]

    # Group by y for horizontal projections.
    y_groups: dict[float, float] = {}
    for x, y in zip(xs_visible, ys_visible):
        y_key = round(float(y), y_round_digits)
        if y_key in y_groups:
            y_groups[y_key] = max(y_groups[y_key], float(x))
        else:
            y_groups[y_key] = float(x)

    for y_val, x_max in y_groups.items():
        ax.hlines(
            y=y_val,
            xmin=x_min_axis,
            xmax=x_max,
            linestyles="dashed",
            linewidth=0.8,
            alpha=0.7,
        )

    # Group by x for vertical projections.
    x_groups: dict[float, float] = {}
    for x, y in zip(xs_visible, ys_visible):
        x_key = round(float(x), y_round_digits)  # same precision for simplicity
        if x_key in x_groups:
            x_groups[x_key] = max(x_groups[x_key], float(y))
        else:
            x_groups[x_key] = float(y)

    for x_val, y_max in x_groups.items():
        ax.vlines(
            x=x_val,
            ymin=y_min_axis,
            ymax=y_max,
            linestyles="dashed",
            linewidth=0.8,
            alpha=0.7,
        )


def _draw_total_time_arrow(ax: Axes) -> None:
    """Draw a double-headed arrow showing total time span on the current axes."""
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    # Place the arrow slightly above the top of the axes data range.
    y_arrow = y_max + 0.03 * (y_max - y_min)

    ax.annotate(
        "",
        xy=(x_min, y_arrow),
        xytext=(x_max, y_arrow),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0),
        annotation_clip=False,
    )

    ax.text(
        0.5 * (x_min + x_max),
        y_arrow,
        f"{x_max - x_min:.2f}",
        ha="center",
        va="bottom",
    )


def _connect_main_and_zoom(
    fig: FigOrSubFig,
    ax_main: Axes,
    ax_zoom: Axes,
    area: ZoomArea,
) -> None:
    """Connect a zoom rectangle in the main axes to the zoom subplot.

    Two lines are drawn:
        * From the top-left corner of the zoom rectangle to the top-left corner
          of the zoom axes.
        * From the top-right corner of the zoom rectangle to the top-right
          corner of the zoom axes.

    The lines are drawn in figure coordinates to correctly span between
    different axes.
    """
    # Main axes: data coordinates of rectangle upper corners.
    main_points_data = [(area.x1, area.y1), (area.x2, area.y1)]
    main_points_fig: List[Tuple[float, float]] = []
    for x_data, y_data in main_points_data:
        x_disp, y_disp = ax_main.transData.transform((x_data, y_data))
        x_fig, y_fig = fig.transFigure.inverted().transform((x_disp, y_disp))
        main_points_fig.append((x_fig, y_fig))

    # Zoom axes: axes coordinates of upper corners (0,1) and (1,1).
    zoom_corners_axes = [(0.0, 1.0), (1.0, 1.0)]
    zoom_points_fig: List[Tuple[float, float]] = []
    for x_axes, y_axes in zoom_corners_axes:
        x_disp, y_disp = ax_zoom.transAxes.transform((x_axes, y_axes))
        x_fig, y_fig = fig.transFigure.inverted().transform((x_disp, y_disp))
        zoom_points_fig.append((x_fig, y_fig))

    # Draw lines in figure coordinates.
    for (x0, y0), (x1, y1) in zip(main_points_fig, zoom_points_fig):
        line = Line2D(
            xdata=(x0, x1),
            ydata=(y0, y1),
            transform=fig.transFigure,
            color="0.7",
            linewidth=0.8,
        )
        fig.add_artist(line)

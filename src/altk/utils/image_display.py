from __future__ import annotations

from typing import Literal

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from numpy.typing import NDArray

from altk.typing.image import (
    ImageArray,
    FloatImageArray,
    RgbImageArray,
    RgbChannel,
    _RGB_CHANNEL_INDEX,
    CropBox,
    
)


def normalize_for_display(
    im: ImageArray,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.5,
) -> FloatImageArray:
    """Normalize an image to the 0-1 range for display.

    Args:
        im: Input image array.
        lower_percentile: Lower clipping percentile.
        upper_percentile: Upper clipping percentile.

    Returns:
        Display-normalized image as float32.
    """
    im_float = im.astype(np.float32, copy=False)
    low, high = np.percentile(im_float, [lower_percentile, upper_percentile])
    if high <= low:
        return np.zeros_like(im_float, dtype=np.float32)
    return np.clip((im_float - low) / (high - low), 0.0, 1.0).astype(np.float32)


def make_rgb_overlay(ref: ImageArray, mov: ImageArray) -> RgbImageArray:
    """Create a red/green overlay image from two images.

    Args:
        ref: Reference image shown in the red channel.
        mov: Moving image shown in the green channel.

    Returns:
        RGB overlay image as float32.
    """
    if ref.shape != mov.shape:
        raise ValueError(f"Image shapes must match, got {ref.shape} and {mov.shape}.")

    ref_display = normalize_for_display(ref)
    mov_display = normalize_for_display(mov)
    overlay = np.zeros((*ref_display.shape, 3), dtype=np.float32)
    overlay[..., 0] = ref_display
    overlay[..., 1] = mov_display
    return overlay


def make_rgb_channel_image(im: ImageArray, channel: RgbChannel) -> RgbImageArray:
    """Create an RGB image with signal in one color channel.

    Args:
        im: Input image array.
        channel: RGB channel used for the image signal.

    Returns:
        RGB image as float32.
    """
    im_display = normalize_for_display(im)
    rgb = np.zeros((*im_display.shape, 3), dtype=np.float32)
    rgb[..., _RGB_CHANNEL_INDEX[channel]] = im_display
    return rgb


def show_rgb_channel(
    im: ImageArray,
    channel: RgbChannel,
    ax: Axes | None = None,
) -> Axes:
    """Show an image in a single RGB channel.

    Args:
        im: Input image array.
        channel: RGB channel used for the image signal.
        ax: Optional Matplotlib axes to draw on.

    Returns:
        Matplotlib axes containing the RGB channel image.
    """
    target_ax = ax if ax is not None else plt.subplots()[1]
    target_ax.imshow(make_rgb_channel_image(im, channel))
    target_ax.set_axis_off()
    return target_ax


def show_rgb_overlay(ref: ImageArray, mov: ImageArray, ax: Axes | None = None) -> Axes:
    """Show a red/green overlay image.

    Args:
        ref: Reference image shown in the red channel.
        mov: Moving image shown in the green channel.
        ax: Optional Matplotlib axes to draw on.

    Returns:
        Matplotlib axes containing the overlay.
    """
    target_ax = ax if ax is not None else plt.subplots()[1]
    target_ax.imshow(make_rgb_overlay(ref, mov))
    target_ax.set_axis_off()
    return target_ax


def show_difference_image(
    diff: ImageArray,
    ax: Axes | None = None,
    percentile: float = 99.0,
) -> Axes:
    """Show a difference image with a symmetric diverging colormap.

    Args:
        diff: Difference image.
        ax: Optional Matplotlib axes to draw on.
        percentile: Percentile used to set symmetric color limits.

    Returns:
        Matplotlib axes containing the difference image.
    """
    target_ax = ax if ax is not None else plt.subplots()[1]
    diff_float = diff.astype(np.float32, copy=False)
    limit = float(np.percentile(np.abs(diff_float), percentile))
    if limit == 0.0:
        limit = 1.0

    image = target_ax.imshow(diff_float, cmap="coolwarm", vmin=-limit, vmax=limit)
    target_ax.figure.colorbar(image, ax=target_ax, fraction=0.046, pad=0.04)
    target_ax.set_axis_off()
    return target_ax


def draw_crop_box(
    ax: Axes,
    box: CropBox,
    edgecolor: str = "white",
    linewidth: float = 1.5,
) -> None:
    """Draw a crop box on an axes.

    Args:
        ax: Matplotlib axes to draw on.
        box: Crop box as (y0, y1, x0, x1).
        edgecolor: Rectangle edge color.
        linewidth: Rectangle line width.
    """
    y0, y1, x0, x1 = box
    ax.add_patch(
        Rectangle(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            fill=False,
            edgecolor=edgecolor,
            linewidth=linewidth,
        )
    )

"""Example script for aligned main-region difference visualization."""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from altk.utils.image_display import draw_crop_box, show_difference_image, show_rgb_channel, show_rgb_overlay
from altk.dichroism import (
    CropBox,
    DifferenceMode,
    FloatImageArray,
    ImageArray,
    Offset,
    calc_difference,
    crop_img,
    find_max_intensity_crop_box,
    find_offset,
    read_tif,
    slice_intersection,
)


@dataclass(frozen=True)
class FullDifferenceResult:
    """Container for aligned main-region difference data.

    Args:
        im1: Reference image.
        im2: Second image. Difference is calculated as im2 - im1.
        im1_overlap: Reference image cropped to the aligned overlapping region.
        im2_overlap: Second image cropped to the aligned overlapping region.
        signal: Signal image used for main-region selection.
        crop_box: Main-region crop box in overlap coordinates.
        im1_main: Reference image cropped to the selected main region.
        im2_main: Second image cropped to the selected main region.
        diff: Difference image.
        offset: Offset that aligns im2 to im1.
        window_size: Main-region crop size as (height, width).
        mode: Difference calculation mode.
    """

    im1: ImageArray
    im2: ImageArray
    im1_overlap: ImageArray
    im2_overlap: ImageArray
    signal: FloatImageArray
    crop_box: CropBox
    im1_main: ImageArray
    im2_main: ImageArray
    diff: FloatImageArray
    offset: Offset
    window_size: tuple[int, int]
    mode: DifferenceMode


def calculate_full_difference_data(
    im1: ImageArray,
    im2: ImageArray,
    window_size: tuple[int, int],
    mode: DifferenceMode = "absolute",
) -> FullDifferenceResult:
    """Calculate aligned main-region difference data.

    Args:
        im1: Reference image.
        im2: Second image. Difference is calculated as im2 - im1.
        window_size: Main-region crop size as (height, width).
        mode: Difference calculation mode.

    Returns:
        Full difference result and intermediate images.
    """
    offset = find_offset(im1, im2)
    im1_overlap, im2_overlap = slice_intersection(im1, im2, offset)
    signal = _make_joint_signal(im1_overlap, im2_overlap)
    crop_box = find_max_intensity_crop_box(signal, window_size)
    im1_main = crop_img(im1_overlap, crop_box)
    im2_main = crop_img(im2_overlap, crop_box)
    diff = calc_difference(im1_main, im2_main, mode=mode)

    return FullDifferenceResult(
        im1=im1,
        im2=im2,
        im1_overlap=im1_overlap,
        im2_overlap=im2_overlap,
        signal=signal,
        crop_box=crop_box,
        im1_main=im1_main,
        im2_main=im2_main,
        diff=diff,
        offset=offset,
        window_size=window_size,
        mode=mode,
    )


def plot_full_difference_result(result: FullDifferenceResult) -> Figure:
    """Plot the full aligned main-region difference workflow.

    Args:
        result: Full difference result to plot.

    Returns:
        Matplotlib figure containing the workflow summary.
    """
    fig = plt.figure(figsize=(14, 9))
    gs = GridSpec(3, 4, figure=fig, width_ratios=[1, 1, 1, 1.4])

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, 0])
    ax5 = fig.add_subplot(gs[1, 1])
    ax6 = fig.add_subplot(gs[1, 2])
    ax7 = fig.add_subplot(gs[2, 0])
    ax8 = fig.add_subplot(gs[2, 1])
    ax9 = fig.add_subplot(gs[2, 2])
    ax10 = fig.add_subplot(gs[:, 3])

    show_rgb_channel(result.im1, "red", ax=ax1)
    ax1.set_title("Image 1")

    show_rgb_channel(result.im2, "green", ax=ax2)
    ax2.set_title("Image 2")

    show_rgb_overlay(result.im1, result.im2, ax=ax3)
    ax3.set_title("Before alignment")

    show_rgb_channel(result.im1_overlap, "red", ax=ax4)
    draw_crop_box(ax4, result.crop_box)
    ax4.set_title("Image 1 overlap")

    show_rgb_channel(result.im2_overlap, "green", ax=ax5)
    draw_crop_box(ax5, result.crop_box)
    ax5.set_title("Image 2 overlap")

    show_rgb_overlay(result.im1_overlap, result.im2_overlap, ax=ax6)
    draw_crop_box(ax6, result.crop_box)
    ax6.set_title("Aligned overlap")

    show_rgb_channel(result.im1_main, "red", ax=ax7)
    ax7.set_title("Image 1 main")

    show_rgb_channel(result.im2_main, "green", ax=ax8)
    ax8.set_title("Image 2 main")

    show_rgb_overlay(result.im1_main, result.im2_main, ax=ax9)
    ax9.set_title("Main overlay")

    show_difference_image(result.diff, ax=ax10)
    ax10.set_title(f"Difference ({result.mode}): im2 - im1")

    fig.suptitle(
        "Full difference workflow: "
        f"offset dy={result.offset[0]}, dx={result.offset[1]}, "
        f"window={result.window_size[0]}x{result.window_size[1]}"
    )
    fig.tight_layout()
    return fig


def show_full_difference(
    file1: str | PathLike[str],
    file2: str | PathLike[str],
    window_size: tuple[int, int],
    mode: DifferenceMode = "absolute",
) -> None:
    """Show aligned main-region difference between two image files.

    Args:
        file1: Reference image path.
        file2: Second image path. Difference is calculated as file2 - file1.
        window_size: Main-region crop size as (height, width).
        mode: Difference calculation mode.
    """
    im1 = read_tif(file1)
    im2 = read_tif(file2)
    result = calculate_full_difference_data(
        im1,
        im2,
        window_size=window_size,
        mode=mode,
    )
    plot_full_difference_result(result)
    plt.show()


def _make_joint_signal(im1: ImageArray, im2: ImageArray) -> FloatImageArray:
    """Create a joint signal map for main-region selection.

    Args:
        im1: Reference image.
        im2: Second image.

    Returns:
        Joint signal image as float32.
    """
    return (im1.astype("float32", copy=False) + im2.astype("float32", copy=False))


def main() -> None:
    """Run the full difference example."""
    show_full_difference(
        "./data/20260514_05_60K_785nm.tif",
        "./data/20260514_06_110K_785nm.tif",
        window_size=(1024, 1024),
        mode="relative",
    )


if __name__ == "__main__":
    main()

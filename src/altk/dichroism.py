from __future__ import annotations

from os import PathLike
from typing import cast, Literal

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import shift
from scipy.signal import correlate
from tifffile import imread

from altk.utils.image_display import CropBox, FloatImageArray, ImageArray, ImageSlice, ImageSlices

Offset = tuple[int, int]
DifferenceMode = Literal["absolute", "relative"]

def read_tif(path: str | PathLike[str]) -> ImageArray:
    """Read a TIFF image file.

    Args:
        path: Path to the TIFF file.

    Returns:
        The image as a NumPy array.
    """
    return cast(ImageArray, imread(path))


def normalize_img(im: ImageArray) -> FloatImageArray:
    """Normalize an image for cross-correlation.

    Args:
        im: Input image array.

    Returns:
        Zero-mean, unit-variance image as float32.
    """
    im_float = im.astype(np.float32, copy=False)
    std = float(np.std(im_float))
    if std == 0.0:
        raise ValueError("Cannot normalize an image with zero standard deviation.")
    return (im_float - float(np.mean(im_float))) / std


def find_offset(ref: ImageArray, mov: ImageArray, normalize: bool = True) -> Offset:
    """Find the integer-pixel shift needed to align a moving image to a reference.

    Args:
        ref: Reference image.
        mov: Moving image.
        normalize: Whether to normalize both images before cross-correlation.

    Returns:
        Offset as (dy, dx). Applying this offset to `mov` aligns it to `ref`.
    """
    ref_corr = normalize_img(ref) if normalize else ref.astype(np.float32, copy=False)
    mov_corr = normalize_img(mov) if normalize else mov.astype(np.float32, copy=False)

    corr = correlate(ref_corr, mov_corr, mode="full", method="fft")
    peak_y, peak_x = np.unravel_index(np.argmax(corr), corr.shape)
    zero_y = mov_corr.shape[0] - 1
    zero_x = mov_corr.shape[1] - 1
    return int(peak_y - zero_y), int(peak_x - zero_x)


def shift_img(im: ImageArray, offset: Offset) -> FloatImageArray:
    """Shift an image by a y/x offset.

    Args:
        im: Input image array.
        offset: Shift as (dy, dx).

    Returns:
        Shifted image as float32.
    """
    return cast(
        FloatImageArray,
        shift(
            im.astype(np.float32, copy=False),
            shift=offset,
            order=3,
            mode="constant",
            cval=0.0,
        ),
    )


def get_intersection_slices(
    im1: ImageArray,
    im2: ImageArray,
    offset: Offset,
) -> ImageSlices:
    """Get slices for the overlapping aligned region of two images.

    Args:
        im1: Reference image.
        im2: Moving image before shifting.
        offset: Shift as (dy, dx). This is the offset that would align im2 to im1.

    Returns:
        Slices for im1 and im2. Applying these slices gives aligned overlapping regions.
    """
    height = min(im1.shape[0], im2.shape[0])
    width = min(im1.shape[1], im2.shape[1])
    dy, dx = offset

    if abs(dy) >= height or abs(dx) >= width:
        raise ValueError(
            f"Offset {offset} leaves no overlapping region for image shape "
            f"{im1.shape} and {im2.shape}."
        )

    im1_y0 = max(dy, 0)
    im1_y1 = height + min(dy, 0)
    im2_y0 = max(-dy, 0)
    im2_y1 = height - max(dy, 0)

    im1_x0 = max(dx, 0)
    im1_x1 = width + min(dx, 0)
    im2_x0 = max(-dx, 0)
    im2_x1 = width - max(dx, 0)

    im1_slice = (slice(im1_y0, im1_y1), slice(im1_x0, im1_x1))
    im2_slice = (slice(im2_y0, im2_y1), slice(im2_x0, im2_x1))
    return im1_slice, im2_slice


def slice_intersection(
    im1: ImageArray,
    im2: ImageArray,
    offset: Offset,
) -> tuple[ImageArray, ImageArray]:
    """Slice the overlapping aligned region from two original images.

    Args:
        im1: Reference image.
        im2: Moving image before shifting.
        offset: Shift as (dy, dx). This is the offset that would align im2 to im1.

    Returns:
        Cropped im1 and im2 arrays from their aligned overlapping region.
    """
    if im1.shape != im2.shape:
        raise ValueError(f"Image shapes must match, got {im1.shape} and {im2.shape}.")

    im1_slice, im2_slice = get_intersection_slices(im1, im2, offset)
    return im1[im1_slice], im2[im2_slice]


def crop_img(im: ImageArray, box: CropBox) -> ImageArray:
    """Crop an image by a crop box.

    Args:
        im: Input image array.
        box: Crop box as (y0, y1, x0, x1).

    Returns:
        Cropped image array.
    """
    y0, y1, x0, x1 = box
    if y0 < 0 or x0 < 0 or y1 > im.shape[0] or x1 > im.shape[1]:
        raise ValueError(f"Crop box {box} is outside image shape {im.shape}.")
    if y0 >= y1 or x0 >= x1:
        raise ValueError(f"Crop box {box} has no positive area.")
    return im[y0:y1, x0:x1]


def find_max_intensity_crop_box(
    im: ImageArray,
    window_size: tuple[int, int],
) -> CropBox:
    """Find a fixed-size crop box with the maximum total intensity.

    Args:
        im: Input image array.
        window_size: Crop size as (height, width).

    Returns:
        Crop box as (y0, y1, x0, x1).
    """
    height, width = im.shape[:2]
    window_height, window_width = window_size
    if window_height <= 0 or window_width <= 0:
        raise ValueError(f"Window size must be positive, got {window_size}.")
    if window_height > height or window_width > width:
        raise ValueError(
            f"Window size {window_size} is larger than image shape {im.shape}."
        )

    signal = im.astype(np.float64, copy=False)
    integral = np.pad(signal.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))
    window_sums = (
        integral[window_height:, window_width:]
        - integral[:-window_height, window_width:]
        - integral[window_height:, :-window_width]
        + integral[:-window_height, :-window_width]
    )
    y0, x0 = np.unravel_index(np.argmax(window_sums), window_sums.shape)
    return int(y0), int(y0 + window_height), int(x0), int(x0 + window_width)


def calc_difference(
    im1: ImageArray,
    im2: ImageArray,
    mode: DifferenceMode = "absolute",
    eps: float = 1e-6,
) -> FloatImageArray:
    """Calculate the difference between two images.

    Args:
        im1: Reference image.
        im2: Second image. The output is calculated as im2 - im1.
        mode: Difference mode. "absolute" returns im2 - im1.
            "relative" returns (im2 - im1) / (im2 + im1 + eps).
        eps: Small value to avoid division by zero in relative mode.

    Returns:
        Difference image as float32.
    """
    if im1.shape != im2.shape:
        raise ValueError(f"Image shapes must match, got {im1.shape} and {im2.shape}.")

    im1_float = im1.astype(np.float32, copy=False)
    im2_float = im2.astype(np.float32, copy=False)

    if mode == "absolute":
        diff = _calc_absolute_difference(im1_float, im2_float)
    elif mode == "relative":
        diff = _calc_relative_difference(im1_float, im2_float, eps)
    else:
        raise ValueError(f'"{mode}" not a valid mode.')
    return diff


def _calc_relative_difference(
    im1: FloatImageArray,
    im2: FloatImageArray,
    eps: float,
) -> FloatImageArray:
    """Calculate the relative difference im2 - im1 normalized by total signal.

    Args:
        im1: Reference image as float32.
        im2: Second image as float32.
        eps: Small value to avoid division by zero.

    Returns:
        Relative difference image as float32.
    """
    return ((im2 - im1) / (im2 + im1 + eps)).astype(np.float32, copy=False)


def _calc_absolute_difference(
    im1: FloatImageArray,
    im2: FloatImageArray,
) -> FloatImageArray:
    """Calculate the absolute difference im2 - im1.

    Args:
        im1: Reference image as float32.
        im2: Second image as float32.

    Returns:
        Absolute difference image as float32.
    """
    return (im2 - im1).astype(np.float32, copy=False)

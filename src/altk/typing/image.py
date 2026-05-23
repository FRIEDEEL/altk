from typing import Literal
import numpy as np
from numpy.typing import NDArray

ImageArray = NDArray[np.generic]
FloatImageArray = NDArray[np.float32]
ImageSlice = tuple[slice, slice]
ImageSlices = tuple[ImageSlice, ImageSlice]
CropBox = tuple[int, int, int, int]


RgbImageArray = NDArray[np.float32]
RgbChannel = Literal["red", "green", "blue"]
_RGB_CHANNEL_INDEX: dict[RgbChannel, int] = {"red": 0, "green": 1, "blue": 2}
import pandas as pd
from matplotlib.axes import Axes
from pandas import DataFrame
from altk.utils._exceptions import DataFileInvalid
import numpy as np

import logging

from typing import Sequence, Tuple

logger = logging.getLogger(__name__)


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
    logger.debug(f"Shape of array: {seq_array.shape}")
    return seq_array

def write_program_to_csv():
    pass


def plot_furnace_program(ax: Axes, seq: np.ndarray, zoom_areas: Sequence[Tuple[int, int]] = []):
    time_accumulated = seq[:,0]
    temperature = seq[:, 1]

    if len(zoom_areas) > 0:
        _plot_furnace_program_with_zooms(time_accumulated, temperature, zoom_areas)
        

def _plot_furnace_program_with_zooms(time:np.ndarray, temperature:np.ndarray, zoom_areas):
    pass

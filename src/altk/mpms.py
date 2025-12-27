import pandas as pd
from pandas import DataFrame
from matplotlib.axes import Axes

import numpy as np

import logging
from typing import Union, Literal

from altk.utils._exceptions import DataFileInvalid

logger = logging.getLogger(__name__)

COL_T = "Temperature (K)"
COL_H = "Field (Oe)"
COL_M = "Long Moment (emu)"


def read_mpms_data_to_df(file: str) -> DataFrame:
    """Read .dat datafile from mpms.

    Args:
        file (str): the data file

    Returns:
        Union[DataFrame,np.ndarray]: Numpy array or Pandas Dataframe with data.
            The return type is assigned with parameter.
            Useful columns:
                Field (Oe)
                Temperature (K)
                Long Moment (emu)

    Raises:
        FileNotFoundError: File of the given file path is not found.
        StartPositionNotFound: Data start line does not exist in this file.
    """
    logger.info(f'Reading from "{file}".')
    with open(file, "r") as f:
        for i, line in enumerate(f):
            if line.strip() == "[Data]":
                data_start = i + 1
                break
        else:
            raise DataFileInvalid('Data start position "[Data]" not found.')
    df = pd.read_csv(file, skiprows=data_start)
    return df


def read_mpms_data_to_np(file: str) -> np.ndarray:
    """Read mpms data to numpy.ndarray

    Args:
        file (str): The data file

    Returns:
        np.ndarray: The transposed data in ndarray.
        
        Line assignment as follows
            0: Field, in Oe
            1: Temperature, in K
            2: Long Moment(Magnetisation), in emu.
    """
    df_data = read_mpms_data_to_df(file)
    data = df_data[["Field (Oe)", "Temperature (K)", "Long Moment (emu)"]].to_numpy().T
    return data


def plot_MT(ax: Axes, df: DataFrame, **kwargs):
    """Plot magnetization (M) - temperature (T).

    Args:
        ax (Axes): ax to plot
        df (DataFrame): data to plot
    """
    ax.plot(df[COL_T], df[COL_M], **kwargs)
    ax.set_xlabel("T (K)")
    ax.set_ylabel("M (emu)")


def plot_MH(ax: Axes, df: DataFrame, **kwargs):
    """Plot magnetization (M) - magnetic field (H).

    Args:
        ax (Axes): ax to plot
        df (DataFrame): data to plot
    """
    ax.plot(df[COL_H], df[COL_M], **kwargs)
    ax.set_xlabel("H (Oe)")
    ax.set_ylabel("M (emu)")

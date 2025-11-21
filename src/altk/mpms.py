import pandas as pd
from pandas import DataFrame
from matplotlib.axes import Axes

import logging

from altk.utils._exceptions import DataFileInvalid

logger = logging.getLogger(__name__)

def read_mpms_data(file: str) -> DataFrame:
    """Read .dat datafile from mpms.

    Args:
        file (str): the data file

    Returns:
        pd.DataFrame: Pandas Dataframe with data.
            Useful columns:
                Field (Oe)
                Temperature (K)
                Long Moment (emu)

    Raises:
        FileNotFoundError: File of the given file path is not found.
        StartPositionNotFound: Data start line does not exist in this file.
    """
    logger.info(f"Reading from \"{file}\".")
    with open(file, "r") as f:
        for i, line in enumerate(f):
            if line.strip() == "[Data]":
                data_start = i + 1
                break
        else:
            raise DataFileInvalid("Data start position \"[Data]\" not found.")
    df = pd.read_csv(file, skiprows=data_start)
    return df

def plot_MT(ax: Axes, df: DataFrame, **kwargs):
    """Plot magnetization (M) - temperature (T).

    Args:
        ax (Axes): ax to plot
        df (DataFrame): data to plot
    """
    ax.plot(df['Temperature (K)'], df['Long Moment (emu)'], **kwargs)
    ax.set_xlabel("T (K)")
    ax.set_ylabel("M (emu)")

def plot_MH(ax: Axes, df: DataFrame, **kwargs):
    """Plot magnetization (M) - magnetic field (H).

    Args:
        ax (Axes): ax to plot
        df (DataFrame): data to plot
    """
    ax.plot(df['Field (Oe)'], df['Long Moment (emu)'], **kwargs)
    ax.set_xlabel("H (Oe)")
    ax.set_ylabel("M (emu)")

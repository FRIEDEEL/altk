import pandas as pd
from matplotlib.axes import Axes
from pandas import DataFrame
from altk.utils._exceptions import DataFileInvalid

import logging

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
    return df

def write_program_to_csv():
    pass


def plot_furnace_program(ax: Axes, df: DataFrame, **plot_kwargs):
    if "step" in df.columns:
        df = df.sort_values(by="step")
    time_accumulated = [df["time"].iloc[0:i].sum() for i in range(len(df) + 1)] # calc accumulated time len+1
    logger.info(time_accumulated) 

    temp_ = pd.concat([pd.Series([0]), df["temperature"]]) # add a 0 - point to plot
    logger.info(f"temp_: {temp_}")

    ax.plot(time_accumulated, temp_, **plot_kwargs)

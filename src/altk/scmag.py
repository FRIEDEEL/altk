import pandas as pd
from pandas import DataFrame
from matplotlib.axes import Axes


import numpy as np

import logging
from typing import Union, Literal

from altk.utils._exceptions import DataFileInvalid

import logging

logger = logging.getLogger(__name__)

def read_scmag_data_to_df(file: str):
    """Read .dat datafile from scmag datafile (.dat). # TODO: change this

    Args:
        file (str): The data file. No validation check.

    Returns:
        Union[DataFrame,np.ndarray]: Numpy array or Pandas Dataframe with data.
            The return type is assigned with parameter.
            Useful columns:
                Field (Oe)
                Temperature (K)
                Long Moment (emu)
            Note: name strs of these columns are stored as COL_T, COL_H and COL_M
                in mpms.py.

    Raises:
        FileNotFoundError: File of the given file path is not found.
        StartPositionNotFound: Data start line does not exist in this file.
    """
    logger.info(f'Reading from "{file}".')
    with open(file, "r") as f:
        for i, line in enumerate(f):
            if line.strip() == "#Data:":
                data_start = i + 1
                break
        else:
            raise DataFileInvalid('Data start position "[Data]" not found.')
    df = pd.read_csv(file, skiprows=data_start)
    return df
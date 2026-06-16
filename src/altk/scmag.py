import pandas as pd
from pandas import DataFrame
from matplotlib.axes import Axes


import numpy as np

import logging
from typing import Union, Literal, Mapping

from altk.utils._exceptions import DataFileInvalid
from altk.typing.path import DataFile

import logging

logger = logging.getLogger(__name__)

COL_T = "Temperature (K)"
COL_I = "I (A)"
COL_P = "P (C)"
COL_TIME = "Time (s)"


class ScmagSample:
    def __init__(
        self, electrode_area: float | None = None, thickness: float | None = None
    ) -> None:
        self.electrode_area = electrode_area
        self.thickness = thickness
        pass

    @property
    def electrode_area(self):
        if self._electrode_area is None:
            raise ValueError("Empty electrode area. Please set value.")
        return self._electrode_area

    @electrode_area.setter
    def electrode_area(self, value: float | None):
        if value is not None and value <= 0:
            raise ValueError(f"Electrode area should be larger than 0. Got {value}")
        else:
            self._electrode_area = value
        pass

    @property
    def thickness(self):
        if self._thickness is None:
            raise ValueError("Empty thickness value. Please set value.")
        return self._thickness

    @thickness.setter
    def thickness(self, value: float | None):
        if value is not None and value <= 0:
            raise ValueError(f"Sample thickness should be larger than 0. Got {value}")
        else:
            self._thickness = value

    # aliases
    @property
    def A(self):
        return self.electrode_area

    @property
    def d(self):
        return self.thickness


class ScmagData:
    def __init__(
        self,
        data: DataFrame,
        sample: ScmagSample | None = None,
    ) -> None:
        self._data = data

    @classmethod
    def from_file(cls, file: DataFile):
        data = read_scmag_data_to_df(file)
        return cls(data=data)

    @property
    def data(self):
        return self._data

    @property
    def temperature(self):
        return self.data[COL_T]

    @property
    def time(self):
        return self.data[COL_TIME]

    @property
    def current(self):
        return self.data[COL_I]

    @property
    def charge(self):
        return self.data[COL_P]

    # aliases
    ...

    def set_sample(self, sample: ScmagSample):
        pass


def read_scmag_data_to_df(file: DataFile):
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

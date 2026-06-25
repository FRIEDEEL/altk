from __future__ import annotations
import pandas as pd
from pandas import DataFrame


import numpy as np

import logging
from typing import Self

from altk.utils._exceptions import DataFileInvalid
from altk.typing.path import DataFile

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
        """The area of gold-coated electrode, in µm^2."""
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
        """The thickness of sample, in µm."""
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
        self.data = data
        self.sample = sample

    @classmethod
    def from_file(cls, file: DataFile, sample: ScmagSample | None = None):
        data = read_scmag_data_to_df(file)
        return cls(data=data, sample=sample)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value: DataFrame):
        self._data = value

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

    @property
    def sample(self):
        if self._sample is None:
            raise ValueError("Empty sample info. Please set sample info.")
        return self._sample

    @sample.setter
    def sample(self, value: ScmagSample | None):
        self._sample = value

    def set_sample(self, sample: ScmagSample) -> Self:
        self.sample = sample
        return self

    @property
    def polarization(self):
        A = self.sample.electrode_area
        return self.charge / A

    @property
    def current_density(self):
        A = self.sample.electrode_area
        return self.current / A

    # aliases

    @property
    def T(self):
        return self.temperature

    @property
    def t(self):
        return self.time

    @property
    def I(self):
        return self.current

    @property
    def Q(self):
        return self.charge

    @property
    def J(self):
        return self.current_density

    @property
    def P(self):
        return self.polarization

    ...

    def interpolate_on_T(self, target_T_col: pd.Series) -> ScmagData:
        new_data = pd.DataFrame()
        cols = self.data.columns
        for col in cols:
            if col == COL_T:
                new_data[COL_T] = target_T_col
            else:
                new_col = pd.Series(
                    np.interp(target_T_col, self.data[COL_T], self.data[col].to_numpy())
                )
                new_data[col] = new_col
        new_scmag_data = ScmagData(data = new_data, sample = self._sample)
        return new_scmag_data


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

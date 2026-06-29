from __future__ import annotations
import pandas as pd
from pandas import DataFrame, Series


import numpy as np

import logging
from typing import Self, Literal, Iterable

from altk.utils._exceptions import DataFileInvalid
from altk.typing.path import DataFile

logger = logging.getLogger(__name__)

COL_T = "Temperature (K)"
COL_I = "I (A)"
COL_P = "P (C)"
COL_TIME = "Time (s)"
COL_MTIME = "Machine_Time (s)"
COL_H = "Field (Oe)"
COL_SENSOR = "Sensor (Ohm)"
COL_POLARIZATION = "Polarization (C/m^2)"
COL_CURRENT_DENSITY = "Current Density (A/m^2)"
COL_BETA = "Beta (K/s)"
COL_I_OVER_BETA = "I/Beta (C/K)"
COL_J_OVER_BETA = "J/Beta (C/m^2/K)"

type ColName = Literal[
    "Temperature (K)",
    "I (A)",
    "P (C)",
    "Time (s)",
    "Machine_Time (s)",
    "Field (Oe)",
    "Sensor (Ohm)",
    "Polarization (C/m^2)",
    "Current Density (A/m^2)",
    "Beta (K/s)",
    "I/Beta (C/K)",
    "J/Beta (C/m^2/K)",
]
type ColNames = Iterable[ColName]
type QuantityName = Literal[
    "T",
    "t",
    "I",
    "Q",
    "P",
    "J",
    "beta",
    "I_beta",
    "J_beta",
]
type QuantityNames = Iterable[QuantityName]

class ScmagSample:
    def __init__(
        self, electrode_area: float | None = None, thickness: float | None = None
    ) -> None:
        self.electrode_area = electrode_area
        self.thickness = thickness
        pass

    @classmethod
    def from_um(
        cls, electrode_area: float | None = None, thickness: float | None = None
    ) -> Self:
        """ScmagSample, but units in µm instead of SI.
        Caution: unit is still SI inside
        """
        if electrode_area is not None:
            A = electrode_area * 1e-12
        else:
            A = electrode_area
        if thickness is not None:
            d = thickness * 1e-6
        else:
            d = thickness
        return cls(A, d)

    @property
    def electrode_area(self):
        """The area of gold-coated electrode, in m^2."""
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
        """The thickness of sample, in m."""
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
        if COL_POLARIZATION in self.data.columns:
            return self.data[COL_POLARIZATION]
        A = self.sample.electrode_area
        return self.charge / A

    @property
    def current_density(self):
        if COL_CURRENT_DENSITY in self.data.columns:
            return self.data[COL_CURRENT_DENSITY]
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

    @property
    def I_beta(self) -> Series:
        if COL_I_OVER_BETA in self.data.columns:
            return self.data[COL_I_OVER_BETA]
        return self.current_per_beta()

    @property
    def J_beta(self) -> Series:
        if COL_J_OVER_BETA in self.data.columns:
            return self.data[COL_J_OVER_BETA]
        return self.current_density_per_beta()

    @property
    def beta(self) -> Series:
        if COL_BETA in self.data.columns:
            return self.data[COL_BETA]
        beta = np.gradient(
            self.temperature.to_numpy(),
            self.time.to_numpy(),
        )
        return pd.Series(beta, index=self.data.index, name=COL_BETA)

    def current_per_beta(self, beta_min: float | None = None) -> Series:
        beta = self.beta
        if beta_min is not None:
            beta = beta.mask(beta.abs() < beta_min)
        return self.current / beta

    def current_density_per_beta(self, beta_min: float | None = None) -> Series:
        beta = self.beta
        if beta_min is not None:
            beta = beta.mask(beta.abs() < beta_min)
        return self.current_density / beta

    def with_beta_columns(self, beta_min: float | None = None) -> ScmagData:
        new_data = self.data.copy()
        new_data[COL_BETA] = self.beta
        new_data[COL_I_OVER_BETA] = self.current_per_beta(beta_min=beta_min)
        if self._sample is not None:
            new_data[COL_J_OVER_BETA] = self.current_density_per_beta(
                beta_min=beta_min
            )
        return ScmagData(data=new_data, sample=self._sample)

    def interpolate_on_temperature(
        self,
        target_temperature: pd.Series,
        cols: ColNames = (COL_I, COL_P, COL_TIME),
    ) -> ScmagData:
        source_data = self.data.sort_values(COL_T)
        source_T = source_data[COL_T].to_numpy()
        target_T = target_temperature.to_numpy()
        target_T = target_T[(target_T >= source_T.min()) & (target_T <= source_T.max())]

        new_data = pd.DataFrame({COL_T: target_T})
        for col in cols:
            if col == COL_T:
                continue
            new_data[col] = np.interp(target_T, source_T, source_data[col].to_numpy())

        return ScmagData(data=new_data, sample=self._sample)


def _resolve_quantity(data: ScmagData, quantity: QuantityName) -> tuple[ColName, Series]:
    """Resolve a public quantity name to its output column name and values."""
    if quantity == "T":
        return COL_T, data.T
    if quantity == "t":
        return COL_TIME, data.t
    if quantity == "I":
        return COL_I, data.I
    if quantity == "Q":
        return COL_P, data.Q
    if quantity == "P":
        return COL_POLARIZATION, data.P
    if quantity == "J":
        return COL_CURRENT_DENSITY, data.J
    if quantity == "beta":
        return COL_BETA, data.beta
    if quantity == "I_beta":
        return COL_I_OVER_BETA, data.I_beta
    if quantity == "J_beta":
        return COL_J_OVER_BETA, data.J_beta
    raise ValueError(f"Unknown quantity: {quantity}")


def align_on(
    datasets: Iterable[ScmagData],
    *,
    x: QuantityName = "T",
    quantities: QuantityNames = ("I", "Q", "t"),
    reference: int = 0,
) -> list[ScmagData]:
    """Align multiple SCMAG datasets on a shared quantity grid.

    The target grid is taken from the reference dataset, clipped to the common
    range covered by all input datasets. Requested quantities are resolved
    through ScmagData properties, so both raw columns and derived quantities can
    be aligned with the same API.

    Args:
        datasets (Iterable[ScmagData]): Datasets to align.
        x (QuantityName): Quantity used as the alignment axis.
        quantities (QuantityNames): Quantities to interpolate onto the shared
            grid.
        reference (int): Index of the dataset whose x-grid is used as the
            target grid after clipping to the common range.

    Returns:
        list[ScmagData]: New datasets containing the aligned x quantity and
            requested quantities.

    Raises:
        ValueError: If no datasets are passed or the reference index is invalid.
    """
    datasets = list(datasets)
    if len(datasets) == 0:
        raise ValueError("At least one dataset is required.")
    if reference < 0 or reference >= len(datasets):
        raise ValueError(f"Reference index is out of range: {reference}")

    x_col, reference_x = _resolve_quantity(datasets[reference], x)
    x_values = [_resolve_quantity(data, x)[1] for data in datasets]
    x_min = max(float(x_value.min()) for x_value in x_values)
    x_max = min(float(x_value.max()) for x_value in x_values)
    target_x = reference_x[(reference_x >= x_min) & (reference_x <= x_max)].to_numpy()

    aligned_data: list[ScmagData] = []
    for data, source_x_series in zip(datasets, x_values):
        # Sort x and y with the same order before using np.interp.
        source_x = source_x_series.to_numpy()
        order = np.argsort(source_x)
        source_x = source_x[order]

        new_data = pd.DataFrame({x_col: target_x})
        for quantity in quantities:
            if quantity == x:
                continue
            col, series = _resolve_quantity(data, quantity)
            new_data[col] = np.interp(target_x, source_x, series.to_numpy()[order])

        aligned_data.append(ScmagData(data=new_data, sample=data._sample))

    return aligned_data


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

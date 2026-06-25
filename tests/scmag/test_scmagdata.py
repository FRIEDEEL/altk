import pandas as pd
import pytest 

from altk.scmag import (
    COL_H,
    COL_I,
    COL_MTIME,
    COL_P,
    COL_SENSOR,
    COL_T,
    COL_TIME,
    ScmagData,
    ScmagSample,
    read_scmag_data_to_df,
)
from altk.utils._exceptions import DataFileInvalid


@pytest.fixture
def scmag_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_TIME: [0.0, 1.0, 2.0],
            COL_MTIME: [1000.0, 1001.0, 1002.0],
            COL_T: [100.0, 150.0, 200.0],
            COL_H: [80000.0, 80000.0, 80000.0],
            COL_I: [2.0, 4.0, 6.0],
            COL_P: [10.0, 20.0, 30.0],
            COL_SENSOR: [100.0, 110.0, 120.0],
        }
    )


def test_read_scmag_data_to_df_reads_sanitized_file() -> None:
    data = read_scmag_data_to_df("tests/data/sample_scmag_good.dat")

    assert list(data.columns) == [
        COL_TIME,
        COL_MTIME,
        COL_T,
        COL_H,
        COL_I,
        COL_P,
        COL_SENSOR,
    ]
    assert len(data) == 4


def test_read_scmag_data_to_df_raises_for_bad_data_marker() -> None:
    with pytest.raises(DataFileInvalid):
        read_scmag_data_to_df("tests/data/sample_scmag_bad_data_marker.dat")


def test_scmag_sample_validates_positive_values() -> None:
    with pytest.raises(ValueError, match="Electrode area"):
        ScmagSample(electrode_area=0.0)

    with pytest.raises(ValueError, match="Sample thickness"):
        ScmagSample(thickness=-1.0)


def test_scmag_data_exposes_raw_columns_and_aliases(scmag_df: pd.DataFrame) -> None:
    data = ScmagData(scmag_df)

    pd.testing.assert_series_equal(data.temperature, data.T)
    pd.testing.assert_series_equal(data.time, data.t)
    pd.testing.assert_series_equal(data.current, data.I)
    pd.testing.assert_series_equal(data.charge, data.Q)


def test_scmag_data_calculates_polarization_and_current_density(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df, sample=ScmagSample(electrode_area=2.0))

    pd.testing.assert_series_equal(
        data.P,
        pd.Series([5.0, 10.0, 15.0]),
        check_names=False,
    )
    pd.testing.assert_series_equal(
        data.J,
        pd.Series([1.0, 2.0, 3.0]),
        check_names=False,
    )


def test_scmag_data_raises_when_derived_values_need_missing_sample(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df)

    with pytest.raises(ValueError, match="Empty sample info"):
        _ = data.P

    with pytest.raises(ValueError, match="Empty sample info"):
        _ = data.J


def test_scmag_data_from_file_keeps_sample() -> None:
    sample = ScmagSample(electrode_area=2.0)
    data = ScmagData.from_file("tests/data/sample_scmag_good.dat", sample=sample)

    assert data.sample is sample
    assert data.P.iloc[0] == pytest.approx(0.5e-12)


def test_interpolate_on_temperature_clips_target_grid_and_interpolates_default_columns(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df, sample=ScmagSample(electrode_area=2.0))

    interpolated = data.interpolate_on_temperature(
        pd.Series([50.0, 125.0, 175.0, 250.0])
    )

    pd.testing.assert_series_equal(
        interpolated.T,
        pd.Series([125.0, 175.0], name=COL_T),
    )
    pd.testing.assert_series_equal(
        interpolated.I,
        pd.Series([3.0, 5.0], name=COL_I),
    )
    pd.testing.assert_series_equal(
        interpolated.Q,
        pd.Series([15.0, 25.0], name=COL_P),
    )
    pd.testing.assert_series_equal(
        interpolated.t,
        pd.Series([0.5, 1.5], name=COL_TIME),
    )
    assert COL_H not in interpolated.data.columns
    pd.testing.assert_series_equal(
        interpolated.P,
        pd.Series([7.5, 12.5]),
        check_names=False,
    )


def test_interpolate_on_temperature_can_interpolate_explicit_extra_columns(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df)

    interpolated = data.interpolate_on_temperature(
        pd.Series([125.0, 175.0]),
        cols=(COL_I, COL_P, COL_TIME, COL_H),
    )

    pd.testing.assert_series_equal(
        interpolated.data[COL_H],
        pd.Series([80000.0, 80000.0], name=COL_H),
    )


def test_interpolate_on_temperature_sorts_nonmonotonic_temperature_source() -> None:
    data = ScmagData.from_file("tests/data/sample_scmag_nonmonotonic_temperature.dat")

    interpolated = data.interpolate_on_temperature(pd.Series([125.0, 175.0]))

    pd.testing.assert_series_equal(
        interpolated.I,
        pd.Series([1.5e-09, 2.5e-09], name=COL_I),
    )

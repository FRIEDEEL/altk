import pandas as pd
import pytest 

from altk.scmag import (
    COL_BETA,
    COL_CURRENT_DENSITY,
    COL_H,
    COL_I,
    COL_I_OVER_BETA,
    COL_J_OVER_BETA,
    COL_MTIME,
    COL_P,
    COL_POLARIZATION,
    COL_SENSOR,
    COL_T,
    COL_TIME,
    ScmagData,
    ScmagSample,
    align_on,
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


def test_scmag_data_calculates_beta_and_current_per_beta(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df)

    pd.testing.assert_series_equal(
        data.beta,
        pd.Series([50.0, 50.0, 50.0], name=COL_BETA),
    )
    pd.testing.assert_series_equal(
        data.current_per_beta(),
        pd.Series([0.04, 0.08, 0.12]),
        check_names=False,
    )


def test_scmag_data_calculates_current_density_per_beta(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df, sample=ScmagSample(electrode_area=2.0))

    pd.testing.assert_series_equal(
        data.current_density_per_beta(),
        pd.Series([0.02, 0.04, 0.06]),
        check_names=False,
    )


def test_scmag_data_masks_current_per_beta_when_beta_is_too_small(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df)

    result = data.current_per_beta(beta_min=51.0)

    assert result.isna().all()


def test_scmag_data_with_beta_columns_adds_available_derived_columns(
    scmag_df: pd.DataFrame,
) -> None:
    data = ScmagData(scmag_df, sample=ScmagSample(electrode_area=2.0))

    result = data.with_beta_columns()

    assert COL_BETA in result.data.columns
    assert COL_I_OVER_BETA in result.data.columns
    assert COL_J_OVER_BETA in result.data.columns
    pd.testing.assert_series_equal(result.data[COL_BETA], data.beta)
    pd.testing.assert_series_equal(
        result.data[COL_I_OVER_BETA],
        pd.Series([0.04, 0.08, 0.12], name=COL_I_OVER_BETA),
    )
    pd.testing.assert_series_equal(
        result.data[COL_J_OVER_BETA],
        pd.Series([0.02, 0.04, 0.06], name=COL_J_OVER_BETA),
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


def test_align_on_aligns_datasets_on_reference_temperature_grid(
    scmag_df: pd.DataFrame,
) -> None:
    first = ScmagData(scmag_df)
    second = ScmagData(
        pd.DataFrame(
            {
                COL_TIME: [10.0, 11.0, 12.0],
                COL_T: [125.0, 175.0, 225.0],
                COL_I: [10.0, 20.0, 30.0],
                COL_P: [100.0, 200.0, 300.0],
            }
        )
    )

    aligned_first, aligned_second = align_on([first, second], reference=1)

    pd.testing.assert_series_equal(
        aligned_first.T,
        pd.Series([125.0, 175.0], name=COL_T),
    )
    pd.testing.assert_series_equal(aligned_first.T, aligned_second.T)
    pd.testing.assert_series_equal(
        aligned_first.I,
        pd.Series([3.0, 5.0], name=COL_I),
    )
    pd.testing.assert_series_equal(
        aligned_second.I,
        pd.Series([10.0, 20.0], name=COL_I),
    )


def test_align_on_can_align_derived_quantities(scmag_df: pd.DataFrame) -> None:
    sample = ScmagSample(electrode_area=2.0)
    first = ScmagData(scmag_df, sample=sample)
    second = ScmagData(
        pd.DataFrame(
            {
                COL_TIME: [10.0, 11.0, 12.0],
                COL_T: [125.0, 175.0, 225.0],
                COL_I: [10.0, 20.0, 30.0],
                COL_P: [100.0, 200.0, 300.0],
            }
        ),
        sample=sample,
    )

    aligned_first, aligned_second = align_on(
        [first, second],
        quantities=("I_beta", "J_beta"),
        reference=1,
    )

    assert COL_I_OVER_BETA in aligned_first.data.columns
    assert COL_J_OVER_BETA in aligned_first.data.columns
    pd.testing.assert_series_equal(
        aligned_first.data[COL_I_OVER_BETA],
        pd.Series([0.06, 0.10], name=COL_I_OVER_BETA),
    )
    pd.testing.assert_series_equal(
        aligned_first.data[COL_J_OVER_BETA],
        pd.Series([0.03, 0.05], name=COL_J_OVER_BETA),
    )
    pd.testing.assert_series_equal(aligned_first.T, aligned_second.T)


def test_align_on_materializes_derived_quantities_for_property_access(
    scmag_df: pd.DataFrame,
) -> None:
    sample = ScmagSample(electrode_area=2.0)
    first = ScmagData(scmag_df, sample=sample)
    second = ScmagData(
        pd.DataFrame(
            {
                COL_TIME: [10.0, 11.0, 12.0],
                COL_T: [125.0, 175.0, 225.0],
                COL_I: [10.0, 20.0, 30.0],
                COL_P: [100.0, 200.0, 300.0],
            }
        ),
        sample=sample,
    )

    aligned_first, _ = align_on(
        [first, second],
        quantities=("P", "J", "I_beta"),
        reference=1,
    )

    assert COL_POLARIZATION in aligned_first.data.columns
    assert COL_CURRENT_DENSITY in aligned_first.data.columns
    pd.testing.assert_series_equal(
        aligned_first.P,
        pd.Series([7.5, 12.5], name=COL_POLARIZATION),
    )
    pd.testing.assert_series_equal(
        aligned_first.J,
        pd.Series([1.5, 2.5], name=COL_CURRENT_DENSITY),
    )
    pd.testing.assert_series_equal(
        aligned_first.I_beta,
        pd.Series([0.06, 0.10], name=COL_I_OVER_BETA),
    )


def test_align_on_raises_for_empty_datasets() -> None:
    with pytest.raises(ValueError, match="At least one dataset"):
        align_on([])


def test_align_on_raises_for_bad_reference(scmag_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Reference index"):
        align_on([ScmagData(scmag_df)], reference=1)

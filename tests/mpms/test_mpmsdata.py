import pandas as pd
import pytest

from altk.mpms import COL_H, COL_M, COL_T, MpmsData, Sample


@pytest.fixture
def mpms_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            COL_M: [2.0, 4.0],
            COL_T: [10.0, 20.0],
            COL_H: [100.0, 200.0],
        }
    )


def test_mpms_data_from_file_reads_mass_from_metadata() -> None:
    data = MpmsData.from_file("tests/data/sample_mpms_data_file.dat")

    assert data.metadata["WEIGHT"] == "0.177"
    assert data.mass == 0.177
    assert len(data.M) == len(data.data)


def test_mpms_data_calculates_magnetisation_from_mass(mpms_df: pd.DataFrame) -> None:
    data = MpmsData(mpms_df, metadata={"WEIGHT": 2.0})

    expected = pd.Series([1.0, 2.0])

    pd.testing.assert_series_equal(data.M, expected, check_names=False)


def test_mpms_data_allows_missing_sample(mpms_df: pd.DataFrame) -> None:
    data = MpmsData(mpms_df)

    assert data.sample is None


def test_mpms_data_raises_when_mass_requires_missing_sample(
    mpms_df: pd.DataFrame,
) -> None:
    data = MpmsData(mpms_df)

    with pytest.raises(ValueError, match="Sample info is required"):
        _ = data.M


def test_mpms_data_mass_setter_creates_sample(mpms_df: pd.DataFrame) -> None:
    data = MpmsData(mpms_df)

    data.mass = 2.0

    assert data.sample is not None
    assert data.mass == 2.0


def test_mpms_data_explicit_sample_takes_priority_over_metadata(
    mpms_df: pd.DataFrame,
) -> None:
    data = MpmsData(
        mpms_df,
        metadata={"WEIGHT": 2.0},
        sample=Sample(mass=4.0, molar_mass=100.0),
    )

    assert data.mass == 4.0


def test_mpms_data_calculates_molar_magnetisation_from_sample(
    mpms_df: pd.DataFrame,
) -> None:
    data = MpmsData(mpms_df, sample=Sample(mass=2.0, molar_mass=100.0))

    expected = pd.Series([100.0, 200.0])

    pd.testing.assert_series_equal(
        data.molar_magnetisation,
        expected,
        check_names=False,
    )


def test_mpms_data_calculates_molar_susceptibility_from_sample(
    mpms_df: pd.DataFrame,
) -> None:
    data = MpmsData(mpms_df, sample=Sample(mass=2.0, molar_mass=100.0))

    expected = pd.Series([1.0, 1.0])

    pd.testing.assert_series_equal(
        data.molar_susceptibility,
        expected,
        check_names=False,
    )


def test_mpms_data_molar_aliases_match_molar_quantities(
    mpms_df: pd.DataFrame,
) -> None:
    data = MpmsData(mpms_df, sample=Sample(mass=2.0, molar_mass=100.0))

    pd.testing.assert_series_equal(
        data.M_mol,
        data.molar_magnetisation,
        check_names=False,
    )
    pd.testing.assert_series_equal(
        data.chi_mol,
        data.molar_susceptibility,
        check_names=False,
    )

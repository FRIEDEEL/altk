import pandas as pd
import pytest

from altk.mpms import COL_H, COL_M, COL_T, MpmsData


def test_mpms_data_from_file_reads_mass_from_metadata() -> None:
    data = MpmsData.from_file("tests/data/sample_mpms_data_file.dat")

    assert data.metadata["WEIGHT"] == "0.177"
    assert data.mass == 0.177
    assert len(data.M) == len(data.data)


def test_mpms_data_calculates_magnetisation_from_mass() -> None:
    df = pd.DataFrame(
        {
            COL_M: [2.0, 4.0],
            COL_T: [10.0, 20.0],
            COL_H: [100.0, 200.0],
        }
    )
    data = MpmsData(df, metadata={"WEIGHT": 2.0})

    expected = pd.Series([1.0, 2.0])

    pd.testing.assert_series_equal(data.M, expected, check_names=False)


def test_mpms_data_raises_when_mass_is_missing() -> None:
    df = pd.DataFrame(
        {
            COL_M: [2.0],
            COL_T: [10.0],
            COL_H: [100.0],
        }
    )
    data = MpmsData(df)

    with pytest.raises(ValueError, match="Mass has invalid value"):
        _ = data.M

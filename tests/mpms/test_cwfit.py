import pandas as pd
import pytest

from altk.mpms import curie_weiss_fit


def test_curie_weiss_fit_recovers_parameters_from_synthetic_data() -> None:
    temperature = pd.Series([100.0, 150.0, 200.0, 250.0, 300.0])
    curie_constant = 2.5
    weiss_temperature = 35.0
    susceptibility = curie_constant / (temperature - weiss_temperature)

    result = curie_weiss_fit(temperature, susceptibility)

    assert result.curie_constant == pytest.approx(curie_constant)
    assert result.weiss_temperature == pytest.approx(weiss_temperature)
    assert result.r_squared == pytest.approx(1.0)
    pd.testing.assert_series_equal(
        result.fitted,
        susceptibility,
        check_names=False,
    )


def test_curie_weiss_fit_uses_temperature_range() -> None:
    temperature = pd.Series([100.0, 150.0, 200.0, 250.0, 300.0])
    susceptibility = 2.5 / (temperature - 35.0)

    result = curie_weiss_fit(
        temperature,
        susceptibility,
        t_min=150.0,
        t_max=250.0,
    )

    expected_temperature = pd.Series([150.0, 200.0, 250.0], index=[1, 2, 3])

    pd.testing.assert_series_equal(
        result.temperature,
        expected_temperature,
        check_names=False,
    )
    assert list(result.fitted.index) == [1, 2, 3]


def test_curie_weiss_fit_requires_at_least_two_points() -> None:
    temperature = pd.Series([100.0, 150.0])
    susceptibility = pd.Series([0.1, 0.2])

    with pytest.raises(ValueError, match="At least two data points"):
        curie_weiss_fit(temperature, susceptibility, t_min=125.0)

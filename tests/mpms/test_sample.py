import pytest

from altk.mpms import Sample


def test_sample_calculates_amount_from_molar_mass() -> None:
    sample = Sample(mass=2.0, molar_mass=100.0)

    assert sample.amount == 0.02


def test_sample_calculates_amount_from_molar_mass_with_formula() -> None:
    sample = Sample(mass=2.0, molar_mass=100.0, formula="V2O3")

    assert sample.formula == "V2O3"
    assert sample.amount == 0.02


def test_sample_raises_when_amount_needs_missing_molar_mass() -> None:
    sample = Sample(mass=2.0)

    with pytest.raises(ValueError, match="Empty molar mass"):
        _ = sample.amount


def test_sample_formula_without_molar_mass_does_not_calculate_amount_yet() -> None:
    sample = Sample(mass=2.0, formula="V2O3")

    assert sample.formula == "V2O3"
    with pytest.raises(ValueError, match="Empty molar mass"):
        _ = sample.amount

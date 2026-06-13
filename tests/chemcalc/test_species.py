import pytest

from altk.chemcalc import Species, calc_molar_mass, parse_formula


def test_species_strips_formula() -> None:
    species = Species(" VO2 ")

    assert species.formula == "VO2"


def test_species_rejects_empty_formula() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Species(" ")


def test_parse_formula_simple_formula() -> None:
    assert parse_formula("V2O5") == {"V": 2.0, "O": 5.0}


def test_parse_formula_repeated_element_is_accumulated() -> None:
    assert parse_formula("Cu2OSeO3") == {"Cu": 2.0, "O": 4.0, "Se": 1.0}


def test_parse_formula_supports_decimal_counts() -> None:
    assert parse_formula("V0.95O1.05") == {"V": 0.95, "O": 1.05}


def test_parse_formula_does_not_normalize_formula_string() -> None:
    species = Species("V1O2")

    assert species.formula == "V1O2"
    assert species.composition == {"V": 1.0, "O": 2.0}


def test_parse_formula_rejects_invalid_syntax() -> None:
    with pytest.raises(ValueError, match="Invalid formula"):
        parse_formula("2VO")


def test_calc_molar_mass_from_composition() -> None:
    assert calc_molar_mass({"V": 1.0, "O": 2.0}) == pytest.approx(82.9395)


def test_species_molar_mass() -> None:
    assert Species("V2O5").molar_mass == pytest.approx(181.878)


def test_calc_molar_mass_rejects_unknown_element() -> None:
    with pytest.raises(ValueError, match="Unknown element symbol"):
        calc_molar_mass({"Xx": 1.0})


def test_calc_molar_mass_rejects_non_positive_count() -> None:
    with pytest.raises(ValueError, match="Element count must be positive"):
        calc_molar_mass({"V": 0.0})

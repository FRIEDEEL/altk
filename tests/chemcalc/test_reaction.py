import pytest

from altk.chemcalc import Constraint, Reaction, Species


def test_constraint_accepts_supported_units_and_operators() -> None:
    constraint = Constraint("V2O5", "<=", 10.0, "g")

    assert constraint.species == "V2O5"
    assert constraint.operator == "<="
    assert constraint.value == 10.0
    assert constraint.unit == "g"


def test_constraint_rejects_empty_species() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Constraint("", "<=", 10.0, "g")


def test_constraint_rejects_unsupported_operator() -> None:
    with pytest.raises(ValueError, match="Unsupported constraint operator"):
        Constraint("V2O5", ">=", 10.0, "g")  # type: ignore[arg-type]


def test_constraint_rejects_unsupported_unit() -> None:
    with pytest.raises(ValueError, match="Unsupported constraint unit"):
        Constraint("V2O5", "<=", 10.0, "kg")  # type: ignore[arg-type]


def test_constraint_rejects_non_positive_value() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        Constraint("V2O5", "<=", 0.0, "g")


def test_reaction_from_string_parses_reactants_and_products() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2")

    assert reaction.reactants == (Species("V2O5"), Species("V2O3"))
    assert reaction.products == (Species("VO2"),)
    assert reaction.species == (Species("V2O5"), Species("V2O3"), Species("VO2"))


def test_reaction_from_string_sets_default_coefficients() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2")

    assert reaction.coeffs == {"V2O5": 1, "V2O3": 1, "VO2": 1}


def test_reaction_from_string_parses_explicit_integer_coefficients() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}


def test_reaction_from_string_allows_no_space_after_coefficient() -> None:
    reaction = Reaction.from_string("2H2 + O2 -> 2H2O")

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}


def test_reaction_coefficient_accepts_formula_string() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert reaction.coefficient("H2O") == 2


def test_reaction_coefficient_accepts_species() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert reaction.coefficient(Species("O2")) == 1


def test_reaction_requires_arrow() -> None:
    with pytest.raises(ValueError, match="must contain"):
        Reaction.from_string("V2O5 + V2O3")


def test_reaction_rejects_empty_side_token() -> None:
    with pytest.raises(ValueError, match="Invalid reaction side"):
        Reaction.from_string("V2O5 + -> VO2")


def test_reaction_rejects_invalid_species_token() -> None:
    with pytest.raises(ValueError, match="Invalid species token"):
        Reaction.from_string("0.5 O2 -> O")


def test_reaction_rejects_empty_reactants() -> None:
    with pytest.raises(ValueError, match="at least one reactant"):
        Reaction(reactants=(), products=(Species("VO2"),))


def test_reaction_rejects_empty_products() -> None:
    with pytest.raises(ValueError, match="at least one product"):
        Reaction(reactants=(Species("V2O5"),), products=())


def test_reaction_rejects_non_positive_coefficient() -> None:
    with pytest.raises(ValueError, match="coefficient must be positive"):
        Reaction(
            reactants=(Species("H2"),),
            products=(Species("H2O"),),
            coeffs={"H2": 0},
        )


def test_reaction_balance_is_not_implemented_yet() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2")

    with pytest.raises(NotImplementedError, match="balancing"):
        reaction.balance()


def test_reaction_calculate_is_not_implemented_yet() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2")

    with pytest.raises(NotImplementedError, match="calculation"):
        reaction.calculate([Constraint("V2O5", "<=", 10.0, "g")])

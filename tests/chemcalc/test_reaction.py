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
    assert not reaction.is_balanced()


def test_reaction_from_string_parses_explicit_integer_coefficients() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}
    assert reaction.is_balanced()


def test_reaction_from_string_allows_no_space_after_coefficient() -> None:
    reaction = Reaction.from_string("2H2 + O2 -> 2H2O")

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}


def test_reaction_str_formats_current_unbalanced_coefficients() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    assert str(reaction) == "H2 + O2 -> H2O"


def test_reaction_str_formats_explicit_coefficients() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert str(reaction) == "2 H2 + O2 -> 2 H2O"


def test_reaction_str_formats_balanced_coefficients() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2").balance()

    assert str(reaction) == "V2O5 + V2O3 -> 4 VO2"


def test_reaction_coefficient_accepts_formula_string() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert reaction.coefficient("H2O") == 2


def test_reaction_coefficient_accepts_species() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    assert reaction.coefficient(Species("O2")) == 1


def test_reaction_coeffs_returns_copy() -> None:
    reaction = Reaction.from_string("2 H2 + O2 -> 2 H2O")

    coeffs = reaction.coeffs
    coeffs["H2O"] = 3

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}
    assert reaction.coefficient("H2O") == 2


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


def test_reaction_balance_updates_reaction_in_place() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2")

    balanced = reaction.balance()

    assert balanced is reaction
    assert balanced.reactants == reaction.reactants
    assert balanced.products == reaction.products
    assert balanced.coeffs == {"V2O5": 1, "V2O3": 1, "VO2": 4}
    assert reaction.coeffs == {"V2O5": 1, "V2O3": 1, "VO2": 4}
    assert reaction.is_balanced()


def test_reaction_balance_handles_common_combustion_style_reaction() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    balanced = reaction.balance()

    assert balanced is reaction
    assert balanced.coeffs == {"H2": 2, "O2": 1, "H2O": 2}
    assert balanced.is_balanced()


def test_reaction_balance_supports_chaining() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}
    assert reaction.is_balanced()


def test_reaction_created_with_unbalanced_coefficients_is_not_balanced() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    assert reaction.coeffs == {"H2": 1, "O2": 1, "H2O": 1}
    assert not reaction.is_balanced()


def test_reaction_with_manual_balanced_coefficients_is_balanced() -> None:
    reaction = Reaction(
        reactants=(Species("H2"), Species("O2")),
        products=(Species("H2O"),),
        coeffs={"H2": 2, "O2": 1, "H2O": 2},
    )

    assert reaction.is_balanced()


def test_reaction_coeffs_setter_updates_coefficients() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    reaction.coeffs = {"H2": 2, "O2": 1, "H2O": 2}

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}
    assert reaction.is_balanced()


def test_reaction_coeffs_setter_invalidates_balance_cache() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    reaction.coeffs = {"H2": 1, "O2": 1, "H2O": 1}

    assert not reaction.is_balanced()


def test_reaction_coeffs_setter_rejects_non_positive_coefficient() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    with pytest.raises(ValueError, match="coefficient must be positive"):
        reaction.coeffs = {"H2": 0, "O2": 1, "H2O": 1}


def test_reaction_set_coefficient_updates_single_coefficient() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    reaction.set_coefficient("H2", 2)
    reaction.set_coefficient(Species("H2O"), 2)

    assert reaction.coeffs == {"H2": 2, "O2": 1, "H2O": 2}
    assert reaction.is_balanced()


def test_reaction_set_coefficient_invalidates_balance_cache() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    reaction.set_coefficient("H2O", 3)

    assert not reaction.is_balanced()


def test_reaction_calculate_requires_balanced_reaction() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2")

    with pytest.raises(ValueError, match="must be balanced"):
        reaction.calculate([Constraint("V2O5", "<=", 10.0, "g")])

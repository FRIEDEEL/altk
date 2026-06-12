import pytest

from altk.chemcalc import Constraint, Reaction, calculate_reaction


def test_calculate_reaction_with_mass_constraints() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2").balance()

    result = calculate_reaction(
        reaction,
        [
            Constraint("V2O5", "<=", 10.0, "g"),
            Constraint("V2O3", "<=", 5.0, "g"),
        ],
    )

    v2o5 = result.species["V2O5"]
    v2o3 = result.species["V2O3"]
    vo2 = result.species["VO2"]

    assert result.reaction is reaction
    assert result.extent == pytest.approx(5.0 / v2o3.molar_mass)

    assert v2o5.role == "reactant"
    assert v2o5.coefficient == 1
    assert v2o5.available_mass == pytest.approx(10.0)
    assert v2o5.mass == pytest.approx(result.extent * v2o5.molar_mass)
    assert v2o5.remaining_mass == pytest.approx(10.0 - v2o5.mass)
    assert not v2o5.is_limiting

    assert v2o3.role == "reactant"
    assert v2o3.coefficient == 1
    assert v2o3.available_mass == pytest.approx(5.0)
    assert v2o3.mass == pytest.approx(5.0)
    assert v2o3.remaining_mass == pytest.approx(0.0)
    assert v2o3.is_limiting

    assert vo2.role == "product"
    assert vo2.coefficient == 4
    assert vo2.amount == pytest.approx(4 * result.extent)
    assert vo2.mass == pytest.approx(vo2.amount * vo2.molar_mass)
    assert vo2.available_mass is None
    assert vo2.remaining_mass is None
    assert not vo2.is_limiting


def test_reaction_result_str_formats_text_table() -> None:
    reaction = Reaction.from_string("V2O5 + V2O3 -> VO2").balance()
    result = reaction.calculate(
        [
            Constraint("V2O5", "<=", 10.0, "g"),
            Constraint("V2O3", "<=", 5.0, "g"),
        ]
    )

    text = str(result)

    assert text.splitlines()[0] == "V2O5 + V2O3 -> 4 VO2"
    assert "V2O5" in text
    assert "V2O3" in text
    assert "VO2" in text
    assert "constraint" in text
    assert "<=10g" in text
    assert "<=5g" in text
    assert "molar mass/g/mol" in text
    assert "amount/mol" in text
    assert "mass/g" in text


def test_reaction_calculate_delegates_to_calculate_reaction() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    result = reaction.calculate([Constraint("H2", "<=", 2.0, "mol")])

    assert result.reaction is reaction
    assert result.extent == pytest.approx(1.0)
    assert result.species["H2"].amount == pytest.approx(2.0)
    assert result.species["O2"].amount == pytest.approx(1.0)
    assert result.species["H2O"].amount == pytest.approx(2.0)


def test_calculate_reaction_requires_balanced_reaction() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O")

    with pytest.raises(ValueError, match="must be balanced"):
        calculate_reaction(reaction, [Constraint("H2", "<=", 2.0, "mol")])


def test_calculate_reaction_requires_constraints() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    with pytest.raises(ValueError, match="At least one constraint"):
        calculate_reaction(reaction, [])


def test_calculate_reaction_rejects_unknown_constraint_species() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    with pytest.raises(ValueError, match="not in the reaction"):
        calculate_reaction(reaction, [Constraint("CO2", "<=", 1.0, "mol")])


def test_calculate_reaction_rejects_product_constraints_for_now() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    with pytest.raises(NotImplementedError, match="Product constraints"):
        calculate_reaction(reaction, [Constraint("H2O", "<=", 1.0, "mol")])


def test_calculate_reaction_rejects_equal_constraints_for_now() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    with pytest.raises(NotImplementedError, match="Only '<=' constraints"):
        calculate_reaction(reaction, [Constraint("H2", "=", 1.0, "mol")])


def test_calculate_reaction_uses_tighter_duplicate_constraint() -> None:
    reaction = Reaction.from_string("H2 + O2 -> H2O").balance()

    result = calculate_reaction(
        reaction,
        [
            Constraint("H2", "<=", 2.0, "mol"),
            Constraint("H2", "<=", 1.0, "mol"),
        ],
    )

    assert result.species["H2"].available_amount == pytest.approx(1.0)
    assert result.species["H2"].amount == pytest.approx(1.0)
    assert result.extent == pytest.approx(0.5)

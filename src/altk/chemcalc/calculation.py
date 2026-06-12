from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from altk.chemcalc.reaction import Constraint, Reaction
from altk.chemcalc.species import Species

SpeciesRole = Literal["reactant", "product"]


@dataclass(frozen=True)
class SpeciesCalculation:
    """Structured calculation result for one species.

    Args:
        formula (str): Species formula.
        role (SpeciesRole): Species role in the reaction.
        coefficient (int): Stoichiometric coefficient.
        molar_mass (float): Molar mass in g/mol.
        amount (float): Used or produced amount in mol.
        mass (float): Used or produced mass in g.
        available_amount (float | None): Available amount in mol for reactants.
        available_mass (float | None): Available mass in g for reactants.
        remaining_amount (float | None): Remaining amount in mol for reactants.
        remaining_mass (float | None): Remaining mass in g for reactants.
        is_limiting (bool): Whether this reactant limits the reaction extent.

    Returns:
        None: This dataclass stores calculation results.
    """

    formula: str
    role: SpeciesRole
    coefficient: int
    molar_mass: float
    amount: float
    mass: float
    available_amount: float | None = None
    available_mass: float | None = None
    remaining_amount: float | None = None
    remaining_mass: float | None = None
    is_limiting: bool = False


@dataclass(frozen=True)
class ReactionResult:
    """Structured reaction calculation result.

    Args:
        reaction (Reaction): Balanced reaction used for calculation.
        extent (float): Reaction extent in mol.
        species (dict[str, SpeciesCalculation]): Species results keyed by formula.

    Returns:
        None: This dataclass stores reaction calculation results.
    """

    reaction: Reaction
    extent: float
    species: dict[str, SpeciesCalculation]


def calculate_reaction(
    reaction: Reaction,
    constraints: Sequence[Constraint],
) -> ReactionResult:
    """Calculate reaction quantities from constraints.

    Args:
        reaction (Reaction): Balanced reaction object.
        constraints (Sequence[Constraint]): Quantitative constraints.

    Returns:
        ReactionResult: Structured calculation result.
    """
    if not reaction.is_balanced():
        raise ValueError("Reaction must be balanced before calculation.")
    if not constraints:
        raise ValueError("At least one constraint is required for calculation.")

    reactant_formulas = {species.formula for species in reaction.reactants}
    product_formulas = {species.formula for species in reaction.products}
    available_amounts = _constraints_to_available_amounts(
        reaction=reaction,
        constraints=constraints,
        reactant_formulas=reactant_formulas,
        product_formulas=product_formulas,
    )

    possible_extents = {
        formula: amount / reaction.coefficient(formula)
        for formula, amount in available_amounts.items()
    }
    extent = min(possible_extents.values())
    limiting_formulas = {
        formula
        for formula, possible_extent in possible_extents.items()
        if abs(possible_extent - extent) <= 1e-12
    }

    species_results: dict[str, SpeciesCalculation] = {}
    for species in reaction.reactants:
        species_results[species.formula] = _calculate_reactant(
            reaction=reaction,
            species=species,
            extent=extent,
            available_amount=available_amounts.get(species.formula),
            is_limiting=species.formula in limiting_formulas,
        )

    for species in reaction.products:
        species_results[species.formula] = _calculate_product(
            reaction=reaction,
            species=species,
            extent=extent,
        )

    return ReactionResult(
        reaction=reaction,
        extent=extent,
        species=species_results,
    )


def _constraints_to_available_amounts(
    reaction: Reaction,
    constraints: Sequence[Constraint],
    reactant_formulas: set[str],
    product_formulas: set[str],
) -> dict[str, float]:
    """Convert supported constraints to reactant available amounts.

    Args:
        reaction (Reaction): Reaction object.
        constraints (Sequence[Constraint]): Quantitative constraints.
        reactant_formulas (set[str]): Reactant formula set.
        product_formulas (set[str]): Product formula set.

    Returns:
        dict[str, float]: Available reactant amounts in mol.
    """
    available_amounts: dict[str, float] = {}
    all_formulas = reactant_formulas | product_formulas

    for constraint in constraints:
        if constraint.species not in all_formulas:
            raise ValueError(
                f"Constraint species is not in the reaction: {constraint.species}"
            )
        if constraint.species in product_formulas:
            raise NotImplementedError(
                "Product constraints are not supported in this calculation version."
            )
        if constraint.operator != "<=":
            raise NotImplementedError(
                "Only '<=' constraints are supported in this calculation version."
            )

        amount = _constraint_to_amount(reaction, constraint)
        previous_amount = available_amounts.get(constraint.species)
        if previous_amount is None or amount < previous_amount:
            available_amounts[constraint.species] = amount

    if not available_amounts:
        raise ValueError("At least one reactant constraint is required.")

    return available_amounts


def _constraint_to_amount(reaction: Reaction, constraint: Constraint) -> float:
    """Convert one constraint value to mol.

    Args:
        reaction (Reaction): Reaction object.
        constraint (Constraint): Quantitative constraint.

    Returns:
        float: Amount in mol.
    """
    if constraint.unit == "mol":
        return constraint.value
    if constraint.unit == "g":
        species = _find_species(reaction, constraint.species)
        return constraint.value / species.molar_mass
    raise ValueError(f"Unsupported constraint unit: {constraint.unit}")


def _find_species(reaction: Reaction, formula: str) -> Species:
    """Find species by formula.

    Args:
        reaction (Reaction): Reaction object.
        formula (str): Formula to find.

    Returns:
        Species: Matching species.
    """
    for species in reaction.species:
        if species.formula == formula:
            return species
    raise ValueError(f"Species is not in the reaction: {formula}")


def _calculate_reactant(
    reaction: Reaction,
    species: Species,
    extent: float,
    available_amount: float | None,
    is_limiting: bool,
) -> SpeciesCalculation:
    """Calculate reactant quantities.

    Args:
        reaction (Reaction): Reaction object.
        species (Species): Reactant species.
        extent (float): Reaction extent in mol.
        available_amount (float | None): Available amount in mol.
        is_limiting (bool): Whether this reactant limits extent.

    Returns:
        SpeciesCalculation: Reactant calculation result.
    """
    coefficient = reaction.coefficient(species)
    amount = extent * coefficient
    mass = amount * species.molar_mass
    available_mass = (
        available_amount * species.molar_mass if available_amount is not None else None
    )
    remaining_amount = (
        available_amount - amount if available_amount is not None else None
    )
    remaining_mass = (
        remaining_amount * species.molar_mass
        if remaining_amount is not None
        else None
    )

    return SpeciesCalculation(
        formula=species.formula,
        role="reactant",
        coefficient=coefficient,
        molar_mass=species.molar_mass,
        amount=amount,
        mass=mass,
        available_amount=available_amount,
        available_mass=available_mass,
        remaining_amount=remaining_amount,
        remaining_mass=remaining_mass,
        is_limiting=is_limiting,
    )


def _calculate_product(
    reaction: Reaction,
    species: Species,
    extent: float,
) -> SpeciesCalculation:
    """Calculate product quantities.

    Args:
        reaction (Reaction): Reaction object.
        species (Species): Product species.
        extent (float): Reaction extent in mol.

    Returns:
        SpeciesCalculation: Product calculation result.
    """
    coefficient = reaction.coefficient(species)
    amount = extent * coefficient
    mass = amount * species.molar_mass

    return SpeciesCalculation(
        formula=species.formula,
        role="product",
        coefficient=coefficient,
        molar_mass=species.molar_mass,
        amount=amount,
        mass=mass,
    )

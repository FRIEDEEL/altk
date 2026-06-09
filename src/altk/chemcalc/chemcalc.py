from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal, Sequence

ConstraintOperator = Literal["=", "<="]
ConstraintUnit = Literal["g", "mol"]
ReactionSide = Literal["reactant", "product"]
ReactionArrow = "->"
SpeciesCoefficient = tuple[int, "Species"]

@dataclass(frozen=True)
class Constraint:
    """A quantitative constraint for reaction calculation.

    Args:
        species (str): Formula or species key used in the reaction expression.
        operator (ConstraintOperator): Constraint relation. ``=`` fixes the
            reaction extent and ``<=`` sets an upper bound.
        value (float): Constraint value.
        unit (ConstraintUnit): Unit of the constraint value.

    Returns:
        None: This dataclass stores validated constraint data.
    """

    species: str
    operator: ConstraintOperator
    value: float
    unit: ConstraintUnit

    def __post_init__(self) -> None:
        if not self.species:
            raise ValueError("Constraint species must not be empty.")
        if self.operator not in ("=", "<="):
            raise ValueError(f"Unsupported constraint operator: {self.operator}")
        if self.unit not in ("g", "mol"):
            raise ValueError(f"Unsupported constraint unit: {self.unit}")
        if self.value <= 0:
            raise ValueError(f"Constraint value must be positive. Got {self.value}")


@dataclass(frozen=True)
class Species:
    """Chemical species identified by a formula string.

    Args:
        formula (str): Formula used to identify the species.

    Returns:
        None: This dataclass stores validated species data.
    """

    formula: str

    def __post_init__(self) -> None:
        formula = self.formula.strip()
        if not formula:
            raise ValueError("Species formula must not be empty.")
        object.__setattr__(self, "formula", formula)

    @property
    def composition(self) -> dict[str, float]:
        """Element composition parsed from the formula.

        Args:
            None: This property uses the stored formula.

        Returns:
            dict[str, float]: Element symbols mapped to stoichiometric counts.
        """
        return parse_formula(self.formula)

    @property
    def molar_mass(self) -> float:
        """Molar mass of this species in g/mol.

        Args:
            None: This property uses the stored formula composition.

        Returns:
            float: Molar mass in g/mol.
        """
        return calc_molar_mass(self.composition)


def parse_formula(formula: str) -> dict[str, float]:
    """Parse a simple formula into element counts.

    Args:
        formula (str): Formula such as ``V2O5`` or ``VO2``.

    Returns:
        dict[str, float]: Element symbols mapped to stoichiometric counts.
    """
    if not formula:
        raise ValueError("Formula must not be empty.")

    composition: dict[str, float] = {}
    position = 0
    pattern = re.compile(r"([A-Z][a-z]?)(\d*(?:\.\d+)?)")

    for match in pattern.finditer(formula):
        if match.start() != position:
            raise ValueError(f"Invalid formula near: {formula[position:]}")
        element, count_text = match.groups()
        count = float(count_text) if count_text else 1.0
        composition[element] = composition.get(element, 0.0) + count
        position = match.end()

    if position != len(formula):
        raise ValueError(f"Invalid formula near: {formula[position:]}")
    if not composition:
        raise ValueError(f"Invalid formula: {formula}")

    return composition


def calc_molar_mass(composition: dict[str, float]) -> float:
    """Calculate molar mass from element composition.

    Args:
        composition (dict[str, float]): Element symbols mapped to counts.

    Returns:
        float: Molar mass in g/mol.
    """
    raise NotImplementedError("Molar mass backend is not implemented yet.")


@dataclass(frozen=True)
class Reaction:
    """Structured chemical reaction.

    Args:
        reactants (tuple[Species, ...]): Reactant species.
        products (tuple[Species, ...]): Product species.
        coeffs (dict[str, int]): Stoichiometric coefficients keyed by formula.

    Returns:
        None: This dataclass stores validated reaction data.
    """

    reactants: tuple[Species, ...]
    products: tuple[Species, ...]
    coeffs: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.reactants:
            raise ValueError("Reaction must contain at least one reactant.")
        if not self.products:
            raise ValueError("Reaction must contain at least one product.")

        coeffs = dict(self.coeffs)
        for species in self.species:
            coeffs.setdefault(species.formula, 1)
            if coeffs[species.formula] <= 0:
                raise ValueError(
                    f"Reaction coefficient must be positive for {species.formula}."
                )
        object.__setattr__(self, "coeffs", coeffs)

    @property
    def species(self) -> tuple[Species, ...]:
        """All species in reaction order.

        Args:
            None: This property uses reactants and products.

        Returns:
            tuple[Species, ...]: Reactants followed by products.
        """
        return self.reactants + self.products

    @classmethod
    def from_string(cls, text: str) -> Reaction:
        """Build a reaction from a plain expression.

        Args:
            text (str): Reaction expression such as ``V2O5 + V2O3 -> VO2``.

        Returns:
            Reaction: Parsed reaction object.
        """
        if ReactionArrow not in text:
            raise ValueError(f"Reaction expression must contain '{ReactionArrow}'.")

        left, right = text.split(ReactionArrow, maxsplit=1)
        reactants, reactant_coeffs = _parse_reaction_side(left)
        products, product_coeffs = _parse_reaction_side(right)
        return cls(
            reactants=reactants,
            products=products,
            coeffs=reactant_coeffs | product_coeffs,
        )

    def balance(self) -> Reaction:
        """Balance the reaction.

        Args:
            None: This method uses the stored reaction species.

        Returns:
            Reaction: Balanced reaction.
        """
        raise NotImplementedError("Reaction balancing is not implemented yet.")

    def calculate(self, constraints: Sequence[Constraint]) -> None:
        """Calculate structured reaction quantities from constraints.

        Args:
            constraints (Sequence[Constraint]): Quantitative constraints.

        Returns:
            None: Calculation result type is not implemented yet.
        """
        raise NotImplementedError("Reaction calculation is not implemented yet.")

    def coefficient(self, species: Species | str) -> int:
        """Return the coefficient for a species.

        Args:
            species (Species | str): Species object or formula string.

        Returns:
            int: Stoichiometric coefficient.
        """
        formula = species.formula if isinstance(species, Species) else species
        return self.coeffs[formula]


def _parse_reaction_side(text: str) -> tuple[tuple[Species, ...], dict[str, int]]:
    """Parse one side of a reaction expression.

    Args:
        text (str): One reaction side split by ``+``.

    Returns:
        tuple[tuple[Species, ...], dict[str, int]]: Species and coefficients.
    """
    tokens = [part.strip() for part in text.split("+")]
    if any(not token for token in tokens):
        raise ValueError(f"Invalid reaction side: {text}")

    species_list: list[Species] = []
    coeffs: dict[str, int] = {}
    for token in tokens:
        coeff, species = _parse_species_token(token)
        species_list.append(species)
        coeffs[species.formula] = coeff

    return tuple(species_list), coeffs


def _parse_species_token(token: str) -> SpeciesCoefficient:
    """Parse an optional integer coefficient and formula.

    Args:
        token (str): Species token such as ``2 H2O`` or ``H2O``.

    Returns:
        SpeciesCoefficient: Parsed coefficient and species.
    """
    match = re.fullmatch(r"(?:(\d+)\s*)?([A-Za-z][A-Za-z0-9.]*)", token)
    if match is None:
        raise ValueError(f"Invalid species token: {token}")

    coeff_text, formula = match.groups()
    coeff = int(coeff_text) if coeff_text else 1
    return coeff, Species(formula)

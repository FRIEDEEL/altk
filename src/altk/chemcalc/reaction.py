from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Self, Sequence

from chempy import balance_stoichiometry

from altk.chemcalc.species import Species

ConstraintOperator = Literal["=", "<="]
ConstraintUnit = Literal["g", "mol"]
ReactionSide = Literal["reactant", "product"]
ReactionArrow = "->"
SpeciesCoefficient = tuple[int, Species]


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


class Reaction:
    """Structured chemical reaction.

    Args:
        reactants (tuple[Species, ...]): Reactant species.
        products (tuple[Species, ...]): Product species.
        coeffs (dict[str, int] | None): Stoichiometric coefficients keyed by formula.
        _is_balanced (bool): Cached balance state.

    Returns:
        None: This class stores validated reaction data.
    """

    def __init__(
        self,
        reactants: tuple[Species, ...],
        products: tuple[Species, ...],
        coeffs: dict[str, int] | None = None,
        _is_balanced: bool = False,
    ) -> None:
        self.reactants = reactants
        self.products = products
        self._coeffs = {} if coeffs is None else dict(coeffs)
        self._is_balanced = _is_balanced

        if not self.reactants:
            raise ValueError("Reaction must contain at least one reactant.")
        if not self.products:
            raise ValueError("Reaction must contain at least one product.")

        for species in self.species:
            self._coeffs.setdefault(species.formula, 1)
            if self._coeffs[species.formula] <= 0:
                raise ValueError(
                    f"Reaction coefficient must be positive for {species.formula}."
                )

    @property
    def coeffs(self) -> dict[str, int]:
        """Stoichiometric coefficients keyed by formula.

        Args:
            None: This property returns a copy of the stored coefficients.

        Returns:
            dict[str, int]: Coefficient mapping copy.
        """
        return self._coeffs.copy()

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

    def is_balanced(self) -> bool:
        """Return whether this reaction is balanced.

        Args:
            None: This method checks atom balance when no cached result exists.

        Returns:
            bool: True if this reaction is balanced.
        """
        if self._is_balanced:
            return True

        if self._check_balance():
            self._is_balanced = True
            return True

        return False

    def balance(self) -> Self:
        """Balance the reaction.

        Args:
            None: This method uses the stored reaction species.

        Returns:
            Self: This reaction after in-place coefficient update.
        """
        reactant_formulas = {species.formula for species in self.reactants}
        product_formulas = {species.formula for species in self.products}
        reactant_coeffs, product_coeffs = balance_stoichiometry(
            reactant_formulas,
            product_formulas,
        )

        coeffs = {
            species.formula: int(reactant_coeffs[species.formula])
            for species in self.reactants
        }
        coeffs.update(
            {
                species.formula: int(product_coeffs[species.formula])
                for species in self.products
            }
        )

        self._coeffs = coeffs
        self._is_balanced = True
        return self

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
        return self._coeffs[formula]

    def set_coefficient(self, species: Species | str, coefficient: int) -> None:
        """Set a coefficient for a species.

        Args:
            species (Species | str): Species object or formula string.
            coefficient (int): New stoichiometric coefficient.

        Returns:
            None: This method is reserved for later explicit coefficient editing.
        """
        raise NotImplementedError("Manual coefficient setting is not implemented yet.")

    def _check_balance(self) -> bool:
        """Check whether current coefficients conserve all elements.

        Args:
            None: This method uses the stored species and coefficients.

        Returns:
            bool: True if reactant and product element totals match.
        """
        reactant_composition = self._side_composition(self.reactants)
        product_composition = self._side_composition(self.products)

        if reactant_composition.keys() != product_composition.keys():
            return False

        return all(
            abs(reactant_composition[element] - product_composition[element]) <= 1e-12
            for element in reactant_composition
        )

    def _side_composition(self, species_list: tuple[Species, ...]) -> dict[str, float]:
        """Calculate total element composition for one reaction side.

        Args:
            species_list (tuple[Species, ...]): Species on one reaction side.

        Returns:
            dict[str, float]: Element totals weighted by coefficients.
        """
        composition: dict[str, float] = {}
        for species in species_list:
            coefficient = self.coefficient(species)
            for element, count in species.composition.items():
                composition[element] = composition.get(element, 0.0) + (
                    coefficient * count
                )
        return composition


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

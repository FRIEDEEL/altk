from __future__ import annotations

import re
from dataclasses import dataclass


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

"""Generate deterministic synthetic instrument data for public tests."""

from __future__ import annotations

import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "tests" / "data"


def _generate_mpms_data() -> str:
    """Generate a minimal MPMS-compatible synthetic data file.

    Returns:
        str: Complete MPMS test fixture content.
    """
    header = """[Header]
TITLE,Synthetic MPMS Test Data
BYAPP,ALTK Test Fixture,1.0,Summary

INFO, APPNAME, Synthetic Data Generator
INFO, NAME, SyntheticSample
INFO, WEIGHT, 0.100
INFO, AREA, 0.000
INFO, LENGTH, 0.000
INFO, SHAPE,
INFO, COMMENT, Generated data for public tests; not experimental data
INFO, SEQUENCE FILE: synthetic_sequence.seq

[Data]
Field (Oe),Temperature (K),Long Moment (emu)
"""
    temperatures = range(10, 301, 10)
    rows = [
        f"1000.0,{temperature:.1f},{0.016 / temperature:.8f}"
        for temperature in temperatures
    ]
    return header + "\n".join(rows) + "\n"


def _synthetic_pxrd_intensity(two_theta: float) -> float:
    """Calculate a synthetic diffraction intensity.

    Args:
        two_theta (float): Diffraction angle in degrees.

    Returns:
        float: Synthetic intensity in arbitrary units.
    """
    baseline = 120.0 + 0.8 * two_theta
    peaks = (
        (20.0, 1.4, 1050.0),
        (30.0, 1.2, 760.0),
        (38.0, 1.5, 470.0),
        (45.0, 1.3, 350.0),
        (52.0, 1.4, 280.0),
        (59.0, 1.2, 190.0),
        (65.0, 1.5, 120.0),
    )
    intensity = baseline
    for center, width, amplitude in peaks:
        exponent = -((two_theta - center) ** 2) / (2.0 * width**2)
        intensity += amplitude * math.exp(exponent)
    return intensity


def _generate_pxrd_data() -> str:
    """Generate a minimal RAS-compatible synthetic data file.

    Returns:
        str: Complete PXRD test fixture content.
    """
    header = """*RAS_DATA_START
*RAS_HEADER_START
*FILE_COMMENT "Synthetic PXRD pattern for public tests"
*FILE_MEMO "Generated data; not experimental data"
*FILE_OPERATOR "SyntheticGenerator"
*FILE_SAMPLE "SyntheticSample"
*FILE_TYPE "RAS_RAW"
*FILE_VERSION "1.0000000000"
*RAS_HEADER_END
*RAS_INT_START
"""
    rows = []
    for step in range(801):
        two_theta = 10.0 + step * 0.1
        intensity = _synthetic_pxrd_intensity(two_theta)
        rows.append(f"{two_theta:.1f} {intensity:.3f} 1")
    footer = "\n*RAS_INT_END\n*RAS_DATA_END\n"
    return header + "\n".join(rows) + footer


def main() -> None:
    """Write all synthetic test fixtures."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "sample_mpms_data_file.dat").write_text(
        _generate_mpms_data(),
        encoding="ascii",
    )
    (DATA_DIR / "sample_pxrd_ras_data_file.ras").write_text(
        _generate_pxrd_data(),
        encoding="ascii",
    )


if __name__ == "__main__":
    main()

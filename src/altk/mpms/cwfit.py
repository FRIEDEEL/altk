from __future__ import annotations
import numpy as np
from pandas import Series
from dataclasses import dataclass


@dataclass(frozen=True)
class CurieWeissFitResult:
    curie_constant: float
    weiss_temperature: float
    temperature: Series
    fitted: Series
    r_squared: float
    residual: Series


def curie_weiss_fit(
    temperature: Series,
    susceptibility: Series,
    t_min: float | None = None,
    t_max: float | None = None,
) -> CurieWeissFitResult:
    """Fit susceptibility with the Curie-Weiss law.

    Args:
        temperature (Series): Temperature values.
        susceptibility (Series): Susceptibility values.
        t_min (float | None): Minimum temperature used for fitting.
        t_max (float | None): Maximum temperature used for fitting.

    Returns:
        CurieWeissFitResult: Curie-Weiss fitting result.
    """
    fit_mask = np.ones(len(temperature), dtype=bool)
    if t_min is not None:
        fit_mask &= temperature.to_numpy(dtype=np.float64) >= t_min
    if t_max is not None:
        fit_mask &= temperature.to_numpy(dtype=np.float64) <= t_max

    fit_temperature = temperature[fit_mask]
    fit_susceptibility = susceptibility[fit_mask]

    T = fit_temperature.to_numpy(dtype=np.float64)
    chi = fit_susceptibility.to_numpy(dtype=np.float64)

    if len(T) < 2:
        raise ValueError("At least two data points are required for Curie-Weiss fit.")
    if np.any(chi == 0):
        raise ValueError("Susceptibility must be non-zero for Curie-Weiss fit.")

    slope, intercept = np.polyfit(T, 1 / chi, deg=1)
    curie_constant = 1 / slope
    weiss_temperature = -intercept / slope

    fitted_values = curie_constant / (T - weiss_temperature)
    fitted = Series(fitted_values, index=fit_temperature.index)
    residual = fit_susceptibility - fitted

    ss_res = float(np.sum(residual.to_numpy(dtype=np.float64) ** 2))
    ss_tot = float(np.sum((chi - np.mean(chi)) ** 2))
    r_squared = 1.0 if ss_tot == 0 else 1 - ss_res / ss_tot

    return CurieWeissFitResult(
        curie_constant=float(curie_constant),
        weiss_temperature=float(weiss_temperature),
        temperature=fit_temperature,
        fitted=fitted,
        r_squared=r_squared,
        residual=residual,
    )

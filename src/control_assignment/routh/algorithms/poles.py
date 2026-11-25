"""Numerical pole computation (NumPy) and comparison with the Routh result."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

DEFAULT_TOLERANCE = 1e-6


@dataclass
class PolesResult:
    poles: List[complex]
    lhp: List[complex]
    rhp: List[complex]
    on_axis: List[complex]      # |Re| <= tolerance
    tolerance: float
    rhp_count: int


@dataclass
class Verification:
    routh_rhp: int
    numeric_rhp: int
    agrees: bool
    message: str


def compute_poles(coefficients: Sequence[float], tolerance: float = DEFAULT_TOLERANCE) -> PolesResult:
    """Roots of a_n s^n + ... + a_0 (highest power first) via numpy.roots."""
    roots = np.roots([float(c) for c in coefficients])
    cleaned: List[complex] = []
    for r in roots:
        re, im = float(r.real), float(r.imag)
        if abs(re) <= tolerance:
            re = 0.0
        if abs(im) <= tolerance:
            im = 0.0
        cleaned.append(complex(re, im))
    cleaned.sort(key=lambda z: (-z.real, z.imag))  # largest real part first
    lhp = [z for z in cleaned if z.real < 0]
    rhp = [z for z in cleaned if z.real > 0]
    axis = [z for z in cleaned if z.real == 0]
    return PolesResult(cleaned, lhp, rhp, axis, tolerance, len(rhp))


def verify_against_routh(poles: PolesResult, routh_rhp: int) -> Verification:
    agrees = poles.rhp_count == routh_rhp
    if agrees:
        msg = (f"Verified: numerical RHP pole count ({poles.rhp_count}) equals the Routh "
               f"result ({routh_rhp}) with tolerance {poles.tolerance:g}.")
    else:
        msg = (f"MISMATCH: numerical RHP pole count is {poles.rhp_count} but Routh gives "
               f"{routh_rhp} (tolerance {poles.tolerance:g}).")
    if poles.on_axis:
        msg += f" Note: {len(poles.on_axis)} pole(s) lie on the imaginary axis within tolerance."
    return Verification(routh_rhp, poles.rhp_count, agrees, msg)

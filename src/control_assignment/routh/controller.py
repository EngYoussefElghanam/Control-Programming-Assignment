"""Routh controller: the single entry point the GUI (Student 1) calls.

    from control_assignment.routh.controller import solve, parse_polynomial
    result = solve([1, 1, 10, 72, 152, 240])
    result_panel.setHtml(result.html)       # or setPlainText(result.text)

Run from a terminal:  python -m control_assignment.routh.controller "s^5+s^4+10s^3+72s^2+152s+240=0"
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Sequence

from .algorithms.poles import (DEFAULT_TOLERANCE, PolesResult, Verification,
                               compute_poles, verify_against_routh)
from .algorithms.stability import StabilityResult, analyze_stability
from .algorithms.table import (Number, RouthError, RouthTable, build_routh_table,
                               to_fraction)
from .presentation.solution_formatter import format_full_report, format_html


@dataclass
class RouthResult:
    table: RouthTable
    stability: StabilityResult
    poles: PolesResult
    verification: Verification
    text: str
    html: str


def solve(coefficients: Sequence[Number], tolerance: float = DEFAULT_TOLERANCE) -> RouthResult:
    """Full Routh pipeline. Coefficients are highest power first. Raises RouthError."""
    table = build_routh_table(coefficients)
    stability = analyze_stability(table)
    poles = compute_poles([float(c) for c in table.coefficients], tolerance)
    verification = verify_against_routh(poles, stability.rhp_poles)
    return RouthResult(
        table, stability, poles, verification,
        text=format_full_report(table, stability, poles, verification),
        html=format_html(table, stability, poles, verification),
    )


_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def parse_polynomial(text: str) -> List[Fraction]:
    """Parse 's^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0' into [1,1,10,72,152,240].

    Powers that do not appear get coefficient 0 (and are then rejected by the
    Routh validation, as the assignment requires every coefficient).
    """
    s = text.translate(_SUP).replace("−", "-").replace("*", "").replace(" ", "").lower()
    if "=" in s:
        left, right = s.split("=", 1)
        if right not in ("0", "0.0"):
            raise RouthError("The right-hand side must be 0.")
        s = left
    s = re.sub(r"s(\d+)", r"s^\1", s)  # allow s2 as s^2 only if written like "10s2"
    if not s:
        raise RouthError("Empty polynomial.")
    terms = re.findall(r"[+-]?[^+-]+", s)
    if "".join(terms) != s:
        raise RouthError("Could not parse the polynomial.")
    coeffs: dict = {}
    for t in terms:
        m = re.fullmatch(r"([+-]?)(\d*\.?\d*)(?:s(?:\^(\d+))?)?", t)
        if not m or t in ("+", "-"):
            raise RouthError(f"Could not parse term: {t!r}")
        sign, num, pw = m.groups()
        has_s = "s" in t
        if not has_s:
            if not num:
                raise RouthError(f"Could not parse term: {t!r}")
            power = 0
        else:
            power = int(pw) if pw else 1
        value = to_fraction(num) if num else Fraction(1)
        if sign == "-":
            value = -value
        coeffs[power] = coeffs.get(power, Fraction(0)) + value
    n = max(coeffs)
    return [coeffs.get(p, Fraction(0)) for p in range(n, -1, -1)]


def solve_from_text(text: str, tolerance: float = DEFAULT_TOLERANCE) -> RouthResult:
    return solve(parse_polynomial(text), tolerance)


if __name__ == "__main__":
    arg = " ".join(sys.argv[1:]) or "s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240 = 0"
    try:
        print(solve_from_text(arg).text)
    except RouthError as err:
        print(f"Error: {err}")
        sys.exit(1)

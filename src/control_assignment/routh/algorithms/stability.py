"""Stability classification from the first column of the Routh table."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Tuple

from .table import RouthTable


@dataclass
class StabilityResult:
    first_column: List[Fraction]
    row_labels: List[str]
    signs: List[int]                         # +1 / -1
    sign_changes: int
    change_locations: List[Tuple[str, str]]  # (row label before, row label after)
    rhp_poles: int
    is_stable: bool
    classification: str
    explanation: str


def analyze_stability(table: RouthTable) -> StabilityResult:
    col = table.first_column
    signs = [1 if v > 0 else -1 for v in col]  # zeros excluded (special cases)
    locations = [
        (table.row_labels[i], table.row_labels[i + 1])
        for i in range(len(signs) - 1)
        if signs[i] != signs[i + 1]
    ]
    changes = len(locations)
    stable = changes == 0
    if stable:
        explanation = (
            "All first-column entries have the same sign, so there are no sign "
            "changes: 0 right-half-plane poles and the system is stable."
        )
    else:
        where = ", ".join(f"{a}->{b}" for a, b in locations)
        explanation = (
            f"The first column has {changes} sign change(s) (at {where}). "
            f"Each sign change is one right-half-plane pole, so there are "
            f"{changes} RHP pole(s) and the system is unstable."
        )
    return StabilityResult(
        first_column=col, row_labels=list(table.row_labels), signs=signs,
        sign_changes=changes, change_locations=locations, rhp_poles=changes,
        is_stable=stable,
        classification="Stable" if stable else "Unstable",
        explanation=explanation,
    )

"""Routh table construction (Student 5).

Exact rational arithmetic (fractions.Fraction) is used so the table has no
round-off error. Special cases (zero first-column entry / all-zero row) are
outside the assignment scope and raise RouthSpecialCaseError.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import ceil
from typing import Iterable, List, Sequence, Union

Number = Union[int, float, str, Fraction]


class RouthError(ValueError):
    """Invalid input for the Routh criterion."""


class RouthSpecialCaseError(RouthError):
    """A zero first-column entry or an all-zero row was met (not supported)."""


def to_fraction(value: Number) -> Fraction:
    """Convert int/float/str to an exact Fraction (floats via their repr)."""
    if isinstance(value, Fraction):
        return value
    try:
        return Fraction(str(value).strip())
    except (ValueError, ZeroDivisionError) as exc:
        raise RouthError(f"Invalid coefficient: {value!r}") from exc


def fmt(x: Fraction) -> str:
    """Human-readable number: integer if exact, else up to 6 significant digits."""
    if x.denominator == 1:
        return str(int(x))
    return f"{float(x):.6g}"


def fmt_sub(x: Fraction) -> str:
    """Like fmt() but negatives are wrapped in parentheses (for substitutions)."""
    s = fmt(x)
    return f"({s})" if s.startswith("-") else s


def validate_coefficients(coefficients: Iterable[Number]) -> List[Fraction]:
    """Validate the assignment's input rules and return Fractions.

    Coefficients are ordered highest power first: [a_n, ..., a_1, a_0].
    Rules: degree >= 1, every coefficient present (non-zero), all same sign.
    """
    coeffs = [to_fraction(c) for c in coefficients]
    if len(coeffs) < 2:
        raise RouthError("The polynomial must have degree 1 or higher (at least 2 coefficients).")
    if any(c == 0 for c in coeffs):
        raise RouthError(
            "Every coefficient from s^0 to s^n must be non-zero (a missing/zero "
            "coefficient is outside this assignment's scope)."
        )
    if not (all(c > 0 for c in coeffs) or all(c < 0 for c in coeffs)):
        raise RouthError("All coefficients must have the same sign.")
    return coeffs


@dataclass(frozen=True)
class ElementStep:
    """How one table element (rows 3..n+1) was calculated."""
    row_label: str      # e.g. "s^3"
    col: int            # 1-based column
    formula: str        # symbolic, e.g. "(s^4[1]*s^5[2] - s^5[1]*s^4[2]) / s^4[1]"
    substitution: str   # numeric, e.g. "(1*10 - 1*72) / 1"
    value: Fraction


@dataclass
class RouthTable:
    coefficients: List[Fraction]
    degree: int
    row_labels: List[str]
    rows: List[List[Fraction]]
    steps: List[ElementStep]

    @property
    def first_column(self) -> List[Fraction]:
        return [row[0] for row in self.rows]


def build_routh_table(coefficients: Sequence[Number]) -> RouthTable:
    """Build the complete Routh table for a_n s^n + ... + a_0 = 0.

    Row k (k >= 2) element j (0-based):
        (r1[0]*r0[j+1] - r0[0]*r1[j+1]) / r1[0]
    where r1 = row k-1 and r0 = row k-2 (missing entries are 0).
    """
    coeffs = validate_coefficients(coefficients)
    n = len(coeffs) - 1
    labels = [f"s^{n - k}" for k in range(n + 1)]
    # number of meaningful columns in row k
    width = [ceil((n + 1 - k) / 2) for k in range(n + 1)]

    rows: List[List[Fraction]] = [coeffs[0::2], coeffs[1::2]]
    rows[0] = rows[0] + [Fraction(0)] * (width[0] - len(rows[0]))
    rows[1] = rows[1] + [Fraction(0)] * (width[1] - len(rows[1]))
    steps: List[ElementStep] = []

    def at(row: List[Fraction], j: int) -> Fraction:
        return row[j] if j < len(row) else Fraction(0)

    for k in range(2, n + 1):
        r0, r1 = rows[k - 2], rows[k - 1]
        l0, l1 = labels[k - 2], labels[k - 1]
        if r1[0] == 0:
            raise RouthSpecialCaseError(f"Zero first-column entry in row {l1} (special case, not supported).")
        new_row: List[Fraction] = []
        for j in range(width[k]):
            a, b = at(r1, 0), at(r0, 0)
            c, d = at(r1, j + 1), at(r0, j + 1)
            value = (a * d - b * c) / a
            new_row.append(value)
            steps.append(ElementStep(
                row_label=labels[k],
                col=j + 1,
                formula=f"({l1}[1]*{l0}[{j + 2}] - {l0}[1]*{l1}[{j + 2}]) / {l1}[1]",
                substitution=f"({fmt_sub(a)}*{fmt_sub(d)} - {fmt_sub(b)}*{fmt_sub(c)}) / {fmt_sub(a)}",
                value=value,
            ))
        if all(v == 0 for v in new_row):
            raise RouthSpecialCaseError(f"All-zero row {labels[k]} (special case, not supported).")
        rows.append(new_row)

    if rows[-1][0] == 0:
        raise RouthSpecialCaseError("Zero first-column entry in the last row (special case, not supported).")
    return RouthTable(coeffs, n, labels, rows, steps)

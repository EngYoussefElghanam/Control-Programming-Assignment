"""Mason's Gain Formula solver for Signal Flow Graphs."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable

from src.control_assignment.sfg.algorithms.determinant import (
    DeterminantResult,
    LoopInfo,
    PathInfo,
    compute_cofactor,
    compute_determinant,
    normalize_loops,
    normalize_paths,
)

ZERO_TOLERANCE = 1e-12


class ZeroDeterminantError(ZeroDivisionError):
    """Raised when the SFG determinant Δ evaluates to zero (undefined transfer function)."""

    def __init__(self, result: "MasonResult") -> None:
        self.result = result
        super().__init__(
            "Graph determinant Δ = 0: transfer function T = Σ(Mᵢ·Δᵢ) / Δ is undefined."
        )


@dataclass(frozen=True)
class PathTerm:
    """Stores Mᵢ, Δᵢ, and the product Mᵢ · Δᵢ for a single forward path."""

    index: int
    path: PathInfo
    cofactor: DeterminantResult
    product: float
    product_fraction: Fraction


@dataclass(frozen=True)
class MasonResult:
    """Complete mathematical solution of an SFG using Mason's Gain Formula."""

    paths: tuple[PathInfo, ...]
    loops: tuple[LoopInfo, ...]
    determinant: DeterminantResult
    path_terms: tuple[PathTerm, ...]
    numerator: float
    numerator_fraction: Fraction
    transfer_gain: float | None
    transfer_gain_fraction: Fraction | None
    is_singular: bool
    error_message: str | None = None


def solve_masons_gain(
    paths: Iterable[Any],
    loops: Iterable[Any],
    *,
    raise_on_zero_delta: bool = False,
) -> MasonResult:
    """
    Compute the overall SFG transfer function T = Σ(Mᵢ · Δᵢ) / Δ.

    Args:
        paths: Forward paths provided by Student 3.
        loops: Individual feedback loops provided by Student 3.
        raise_on_zero_delta: If True, raises ZeroDeterminantError when Δ == 0;
            otherwise returns a safe MasonResult with is_singular=True.
    """
    norm_paths = tuple(normalize_paths(paths))
    norm_loops = tuple(normalize_loops(loops))

    det_result = compute_determinant(norm_loops, label="Δ")

    terms: list[PathTerm] = []
    num_frac = Fraction(0, 1)

    for idx, path in enumerate(norm_paths, start=1):
        cofactor = compute_cofactor(path, norm_loops, path_index=idx)
        prod_frac = path.gain_fraction * cofactor.value_fraction
        num_frac += prod_frac
        terms.append(
            PathTerm(
                index=idx,
                path=path,
                cofactor=cofactor,
                product=float(prod_frac),
                product_fraction=prod_frac,
            )
        )

    is_singular = (
        det_result.value_fraction == 0
        or abs(det_result.value) <= ZERO_TOLERANCE
    )

    if is_singular:
        result = MasonResult(
            paths=norm_paths,
            loops=norm_loops,
            determinant=det_result,
            path_terms=tuple(terms),
            numerator=float(num_frac),
            numerator_fraction=num_frac,
            transfer_gain=None,
            transfer_gain_fraction=None,
            is_singular=True,
            error_message=(
                "Undefined transfer function: Graph determinant Δ = 0 "
                "(division by zero avoided)."
            ),
        )
        if raise_on_zero_delta:
            raise ZeroDeterminantError(result)
        return result

    gain_frac = num_frac / det_result.value_fraction
    return MasonResult(
        paths=norm_paths,
        loops=norm_loops,
        determinant=det_result,
        path_terms=tuple(terms),
        numerator=float(num_frac),
        numerator_fraction=num_frac,
        transfer_gain=float(gain_frac),
        transfer_gain_fraction=gain_frac,
        is_singular=False,
        error_message=None,
    )
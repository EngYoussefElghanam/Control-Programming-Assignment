"""Graph determinant (Δ) and forward-path cofactor (Δᵢ) calculations for SFGs."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class LoopInfo:
    """Normalized representation of a feedback loop received from Student 3."""

    loop_id: str
    nodes: tuple[Any, ...]
    gain: float
    gain_fraction: Fraction
    branches: tuple[str, ...] = ()

    @property
    def node_set(self) -> frozenset[Any]:
        return frozenset(self.nodes)


@dataclass(frozen=True)
class PathInfo:
    """Normalized representation of a forward path received from Student 3."""

    path_id: str
    nodes: tuple[Any, ...]
    gain: float
    gain_fraction: Fraction
    branches: tuple[str, ...] = ()

    @property
    def node_set(self) -> frozenset[Any]:
        return frozenset(self.nodes)


@dataclass(frozen=True)
class NonTouchingCombination:
    """Represents a set of k mutually non-touching loops and their gain product."""

    order: int
    loops: tuple[LoopInfo, ...]
    product: float
    product_fraction: Fraction

    @property
    def loop_ids(self) -> tuple[str, ...]:
        return tuple(loop.loop_id for loop in self.loops)


@dataclass(frozen=True)
class DeterminantResult:
    """Complete step-by-step breakdown of Δ or Δᵢ."""

    label: str
    active_loops: tuple[LoopInfo, ...]
    excluded_loops: tuple[LoopInfo, ...]
    combinations_by_order: dict[int, tuple[NonTouchingCombination, ...]]
    order_sums: dict[int, float]
    order_sums_fraction: dict[int, Fraction]
    value: float
    value_fraction: Fraction
    max_order: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_order",
            max(self.combinations_by_order.keys(), default=0),
        )


def _to_fraction(value: float | int | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    return Fraction(str(float(value))).limit_denominator(10**9)


def _get_attr(obj: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        if hasattr(obj, key):
            return getattr(obj, key)
    return default


def normalize_loops(raw_loops: Iterable[Any]) -> list[LoopInfo]:
    """Convert Student 3's loop objects or dicts into normalized LoopInfo records."""
    normalized: list[LoopInfo] = []
    for idx, item in enumerate(raw_loops, start=1):
        if isinstance(item, LoopInfo):
            normalized.append(item)
            continue

        loop_id = str(_get_attr(item, "loop_id", "id", "name", default=f"L{idx}"))
        nodes = tuple(_get_attr(item, "nodes", "vertices", default=()))
        if not nodes:
            raise ValueError(f"Loop '{loop_id}' must contain at least one node.")

        raw_gain = _get_attr(item, "gain", "weight", "value", default=None)
        if raw_gain is None:
            raise ValueError(f"Loop '{loop_id}' is missing a numerical gain.")

        branches = tuple(str(b) for b in _get_attr(item, "branches", "edges", default=()))
        gain_frac = _to_fraction(raw_gain)
        normalized.append(
            LoopInfo(
                loop_id=loop_id,
                nodes=nodes,
                gain=float(raw_gain),
                gain_fraction=gain_frac,
                branches=branches,
            )
        )
    return normalized


def normalize_paths(raw_paths: Iterable[Any]) -> list[PathInfo]:
    """Convert Student 3's forward-path objects or dicts into normalized PathInfo records."""
    normalized: list[PathInfo] = []
    for idx, item in enumerate(raw_paths, start=1):
        if isinstance(item, PathInfo):
            normalized.append(item)
            continue

        path_id = str(_get_attr(item, "path_id", "id", "name", default=f"M{idx}"))
        nodes = tuple(_get_attr(item, "nodes", "vertices", default=()))
        if not nodes:
            raise ValueError(f"Forward path '{path_id}' must contain at least one node.")

        raw_gain = _get_attr(item, "gain", "weight", "value", default=None)
        if raw_gain is None:
            raise ValueError(f"Forward path '{path_id}' is missing a numerical gain.")

        branches = tuple(str(b) for b in _get_attr(item, "branches", "edges", default=()))
        gain_frac = _to_fraction(raw_gain)
        normalized.append(
            PathInfo(
                path_id=path_id,
                nodes=nodes,
                gain=float(raw_gain),
                gain_fraction=gain_frac,
                branches=branches,
            )
        )
    return normalized


def loops_touch(loop_a: LoopInfo, loop_b: LoopInfo) -> bool:
    """Two loops touch if they share at least one node."""
    return not loop_a.node_set.isdisjoint(loop_b.node_set)


def loop_touches_path(loop: LoopInfo, path: PathInfo) -> bool:
    """A loop touches a forward path if they share at least one node."""
    return not loop.node_set.isdisjoint(path.node_set)


def find_non_touching_combinations(
    loops: Sequence[LoopInfo],
) -> dict[int, tuple[NonTouchingCombination, ...]]:
    """Find all valid k-tuples (k >= 1) of mutually non-touching loops."""
    n = len(loops)
    if n == 0:
        return {}

    touch_matrix = [
        [loops_touch(loops[i], loops[j]) for j in range(n)]
        for i in range(n)
    ]

    grouped: dict[int, list[NonTouchingCombination]] = {}

    def backtrack(start_idx: int, chosen_indices: list[int]) -> None:
        if chosen_indices:
            order = len(chosen_indices)
            chosen_loops = tuple(loops[i] for i in chosen_indices)
            prod_frac = Fraction(1, 1)
            for lp in chosen_loops:
                prod_frac *= lp.gain_fraction
            grouped.setdefault(order, []).append(
                NonTouchingCombination(
                    order=order,
                    loops=chosen_loops,
                    product=float(prod_frac),
                    product_fraction=prod_frac,
                )
            )

        for next_idx in range(start_idx, n):
            if all(not touch_matrix[next_idx][prev] for prev in chosen_indices):
                chosen_indices.append(next_idx)
                backtrack(next_idx + 1, chosen_indices)
                chosen_indices.pop()

    backtrack(0, [])
    return {order: tuple(combos) for order, combos in sorted(grouped.items())}


def compute_determinant(
    loops: Iterable[Any],
    *,
    label: str = "Δ",
    excluded_loops: Sequence[LoopInfo] = (),
) -> DeterminantResult:
    """
    Compute Δ = 1 - Σ(Lᵢ) + Σ(LᵢLⱼ) - Σ(LᵢLⱼLₖ) + ...
    """
    active = tuple(normalize_loops(loops))
    combos_by_order = find_non_touching_combinations(active)

    order_sums: dict[int, float] = {}
    order_sums_frac: dict[int, Fraction] = {}
    delta_frac = Fraction(1, 1)

    for order, combos in combos_by_order.items():
        s_frac = sum((c.product_fraction for c in combos), Fraction(0, 1))
        order_sums_frac[order] = s_frac
        order_sums[order] = float(s_frac)
        sign = -1 if (order % 2 == 1) else 1
        delta_frac += sign * s_frac

    return DeterminantResult(
        label=label,
        active_loops=active,
        excluded_loops=tuple(excluded_loops),
        combinations_by_order=combos_by_order,
        order_sums=order_sums,
        order_sums_fraction=order_sums_frac,
        value=float(delta_frac),
        value_fraction=delta_frac,
    )


def compute_cofactor(
    path: Any,
    all_loops: Iterable[Any],
    *,
    path_index: int = 1,
) -> DeterminantResult:
    """
    Compute Δᵢ for a forward path by removing all loops that touch the path.
    """
    norm_path = normalize_paths([path])[0]
    norm_loops = normalize_loops(all_loops)

    non_touching: list[LoopInfo] = []
    touching: list[LoopInfo] = []
    for lp in norm_loops:
        if loop_touches_path(lp, norm_path):
            touching.append(lp)
        else:
            non_touching.append(lp)

    return compute_determinant(
        non_touching,
        label=f"Δ{path_index}",
        excluded_loops=touching,
    )
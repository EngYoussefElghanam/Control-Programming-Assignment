

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Sequence

from src.control_assignment.sfg.algorithms.traversal import (
    Loop,
    format_number,
)


@dataclass(frozen=True)
class NonTouchingGroup:
    """k mutually non-touching loops together with their gain product."""

    order: int
    loops: tuple[Loop, ...]
    product: float
    product_fraction: Fraction

    @property
    def loop_ids(self) -> tuple[str, ...]:
        return tuple(lp.loop_id for lp in self.loops)

    @property
    def expression(self) -> str:
        """e.g. ``L1L2 = L1 × L2 = -2 × -8 = 16``."""
        ids = self.loop_ids
        numbers = " × ".join(format_number(lp.gain) for lp in self.loops)
        return (
            f"{''.join(ids)} = {' × '.join(ids)} = {numbers} "
            f"= {format_number(self.product)}"
        )


def loops_touch(loop_a: Any, loop_b: Any) -> bool:
    """True if the two loops share at least one node."""
    return not set(loop_a.nodes).isdisjoint(loop_b.nodes)


def find_non_touching_groups(
    loops: Iterable[Loop],
    *,
    min_order: int = 2,
    max_order: int | None = None,
) -> dict[int, tuple[NonTouchingGroup, ...]]:
    """Return ``{k: groups}`` for every k ≥ ``min_order`` that has at least one group.

    Groups keep the loop order given (L1 before L2 …) and each set appears once.
    """
    seq: Sequence[Loop] = list(loops)
    n = len(seq)
    touch = [[loops_touch(seq[i], seq[j]) for j in range(n)] for i in range(n)]

    grouped: dict[int, list[NonTouchingGroup]] = {}

    def extend(start: int, chosen: list[int]) -> None:
        order = len(chosen)
        if order >= max(min_order, 1):
            prod = Fraction(1, 1)
            for i in chosen:
                prod *= seq[i].gain_fraction
            grouped.setdefault(order, []).append(
                NonTouchingGroup(
                    order=order,
                    loops=tuple(seq[i] for i in chosen),
                    product=float(prod),
                    product_fraction=prod,
                )
            )
        if max_order is not None and order >= max_order:
            return
        for nxt in range(start, n):
            if all(not touch[nxt][prev] for prev in chosen):
                chosen.append(nxt)
                extend(nxt + 1, chosen)
                chosen.pop()

    extend(0, [])
    return {k: tuple(v) for k, v in sorted(grouped.items())}


def sum_products_by_order(
    groups: dict[int, tuple[NonTouchingGroup, ...]],
) -> dict[int, Fraction]:
    """Σ of gain products for each order k (useful for the Δ terms)."""
    return {
        k: sum((g.product_fraction for g in combos), Fraction(0, 1))
        for k, combos in groups.items()
    }
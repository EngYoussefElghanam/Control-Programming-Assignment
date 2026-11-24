

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Sequence


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Branch:
    """A directed branch with a numerical gain."""

    label: str
    source: Any
    target: Any
    gain: float
    gain_fraction: Fraction


@dataclass(frozen=True)
class ForwardPath:
    """A forward path from the input node to the output node (no repeated node)."""

    path_id: str
    nodes: tuple[Any, ...]
    branches: tuple[str, ...]
    branch_gains: tuple[float, ...]
    gain: float
    gain_fraction: Fraction

    @property
    def node_set(self) -> frozenset[Any]:
        return frozenset(self.nodes)

    @property
    def expression(self) -> str:
        """e.g. ``M1 = G0 × G1 × G2 = 1 × 2 × 3 = 6``."""
        return format_gain_expression(
            self.path_id, self.branches, self.branch_gains, self.gain
        )


@dataclass(frozen=True)
class Loop:
    """An individual loop. ``nodes`` is closed: it ends with its first node."""

    loop_id: str
    nodes: tuple[Any, ...]
    branches: tuple[str, ...]
    branch_gains: tuple[float, ...]
    gain: float
    gain_fraction: Fraction

    @property
    def node_set(self) -> frozenset[Any]:
        return frozenset(self.nodes)

    @property
    def expression(self) -> str:
        """e.g. ``L1 = G1 × H1 = 2 × -1 = -2``."""
        return format_gain_expression(
            self.loop_id, self.branches, self.branch_gains, self.gain
        )


# --------------------------------------------------------------------------- #
# Number helpers / formatting
# --------------------------------------------------------------------------- #
def to_fraction(value: float | int | str | Fraction) -> Fraction:
    """Exact Fraction from a user number (floats go through their decimal text)."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError("Branch gain must be numeric, not boolean.")
    if isinstance(value, int):
        return Fraction(value, 1)
    try:
        return Fraction(str(float(value))).limit_denominator(10**9)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numerical gain: {value!r}") from exc


def format_number(value: float) -> str:
    """Compact number text: ``2.0 -> '2'``, ``-0.6667 -> '-0.6667'``."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6g}"


def format_gain_expression(
    name: str,
    labels: Sequence[str],
    gains: Sequence[float],
    total: float,
) -> str:
    """Build ``NAME = w1 × w2 = n1 × n2 = total`` (labels, numbers, result)."""
    labels_txt = " × ".join(labels)
    numbers_txt = " × ".join(format_number(g) for g in gains)
    if len(gains) == 1:
        return f"{name} = {labels_txt} = {format_number(total)}"
    return f"{name} = {labels_txt} = {numbers_txt} = {format_number(total)}"


# --------------------------------------------------------------------------- #
# Input normalisation
# --------------------------------------------------------------------------- #
def _read(obj: Any, *keys: str) -> Any:
    for key in keys:
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
        elif hasattr(obj, key):
            return getattr(obj, key)
    return None


def normalize_branches(raw_branches: Iterable[Any]) -> list[Branch]:
    """Convert dicts/objects into ``Branch`` records (auto-labels missing names)."""
    branches: list[Branch] = []
    used: set[str] = set()
    for idx, item in enumerate(raw_branches, start=1):
        if isinstance(item, Branch):
            branch = item
        else:
            src = _read(item, "from", "source", "start", "from_node")
            dst = _read(item, "to", "target", "end", "to_node")
            gain = _read(item, "gain", "weight", "value")
            if src is None or dst is None:
                raise ValueError(f"Branch #{idx} must define both source and target nodes.")
            if gain is None:
                raise ValueError(f"Branch #{idx} ({src} → {dst}) is missing a gain.")
            label = _read(item, "label", "name", "id") or f"b{idx}"
            frac = to_fraction(gain)
            branch = Branch(str(label), src, dst, float(frac), frac)
        if branch.label in used:
            raise ValueError(f"Duplicate branch label '{branch.label}'.")
        used.add(branch.label)
        branches.append(branch)
    return branches


def _check_nodes(nodes: Sequence[Any], branches: Sequence[Branch]) -> None:
    known = set(nodes)
    for b in branches:
        for end in (b.source, b.target):
            if end not in known:
                raise ValueError(
                    f"Branch '{b.label}' references unknown node '{end}'."
                )


def _gain_product(selected: Sequence[Branch]) -> Fraction:
    prod = Fraction(1, 1)
    for b in selected:
        prod *= b.gain_fraction
    return prod


# --------------------------------------------------------------------------- #
# Forward paths
# --------------------------------------------------------------------------- #
def find_forward_paths(
    nodes: Sequence[Any],
    branches: Iterable[Any],
    input_node: Any,
    output_node: Any,
) -> list[ForwardPath]:
    """Return every forward path ``input_node → output_node`` without repeating a node.

    Parallel branches between the same two nodes yield separate paths.
    Paths are numbered ``M1, M2, …`` in depth-first discovery order
    (deterministic: branches are explored in the order given).
    """
    nodes = list(nodes)
    blist = normalize_branches(branches)
    _check_nodes(nodes, blist)
    if input_node not in nodes:
        raise ValueError(f"Input node '{input_node}' is not in the graph.")
    if output_node not in nodes:
        raise ValueError(f"Output node '{output_node}' is not in the graph.")
    if input_node == output_node:
        raise ValueError("Input and output nodes must be different.")

    outgoing: dict[Any, list[Branch]] = {n: [] for n in nodes}
    for b in blist:
        outgoing[b.source].append(b)

    found: list[ForwardPath] = []
    visited: set[Any] = {input_node}
    node_stack: list[Any] = [input_node]
    branch_stack: list[Branch] = []

    def dfs(current: Any) -> None:
        if current == output_node:
            prod = _gain_product(branch_stack)
            found.append(
                ForwardPath(
                    path_id=f"M{len(found) + 1}",
                    nodes=tuple(node_stack),
                    branches=tuple(b.label for b in branch_stack),
                    branch_gains=tuple(b.gain for b in branch_stack),
                    gain=float(prod),
                    gain_fraction=prod,
                )
            )
            return
        for b in outgoing[current]:
            if b.target in visited:
                continue
            visited.add(b.target)
            node_stack.append(b.target)
            branch_stack.append(b)
            dfs(b.target)
            branch_stack.pop()
            node_stack.pop()
            visited.discard(b.target)

    dfs(input_node)
    return found


# --------------------------------------------------------------------------- #
# Individual loops
# --------------------------------------------------------------------------- #
def find_loops(nodes: Sequence[Any], branches: Iterable[Any]) -> list[Loop]:
    """Return every individual loop (simple directed cycle) exactly once.

    Each cycle is only reported from its lowest-indexed node (by order in
    ``nodes``), so rotations of the same loop are never duplicated.  Self-loops
    (a branch from a node to itself) are included.  Loops are numbered
    ``L1, L2, …`` in discovery order.
    """
    nodes = list(nodes)
    blist = normalize_branches(branches)
    _check_nodes(nodes, blist)

    index = {n: i for i, n in enumerate(nodes)}
    outgoing: dict[Any, list[Branch]] = {n: [] for n in nodes}
    for b in blist:
        outgoing[b.source].append(b)

    found: list[Loop] = []

    for start in nodes:
        start_idx = index[start]
        on_path: set[Any] = {start}
        node_stack: list[Any] = [start]
        branch_stack: list[Branch] = []

        def dfs(current: Any) -> None:
            for b in outgoing[current]:
                if b.target == start:
                    cycle = branch_stack + [b]
                    prod = _gain_product(cycle)
                    found.append(
                        Loop(
                            loop_id=f"L{len(found) + 1}",
                            nodes=tuple(node_stack) + (start,),
                            branches=tuple(x.label for x in cycle),
                            branch_gains=tuple(x.gain for x in cycle),
                            gain=float(prod),
                            gain_fraction=prod,
                        )
                    )
                elif b.target not in on_path and index[b.target] > start_idx:
                    on_path.add(b.target)
                    node_stack.append(b.target)
                    branch_stack.append(b)
                    dfs(b.target)
                    branch_stack.pop()
                    node_stack.pop()
                    on_path.discard(b.target)

        dfs(start)

    return found


def find_paths_and_loops(
    nodes: Sequence[Any],
    branches: Iterable[Any],
    input_node: Any,
    output_node: Any,
) -> tuple[list[ForwardPath], list[Loop]]:
    """Convenience wrapper: ``(forward_paths, loops)``."""
    blist = normalize_branches(branches)
    return (
        find_forward_paths(nodes, blist, input_node, output_node),
        find_loops(nodes, blist),
    )
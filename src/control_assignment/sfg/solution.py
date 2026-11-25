"""Student 2: adapt existing numerical algorithms into display-ready results."""
from dataclasses import dataclass
from math import isfinite

from ..common.exceptions import ValidationError
from .validation import validate_sfg
from .algorithms.traversal import find_paths_and_loops, format_number
from .algorithms.non_touching import find_non_touching_groups
from .algorithms.mason import solve_masons_gain, MasonResult
from .presentation.solution_formatter import format_mason_solution, format_number as exact_number
from .models import SFGInput


@dataclass(frozen=True)
class SFGSolution:
    mason: MasonResult
    paths_text: str
    loops_text: str
    combinations_text: str
    derivation_text: str
    final_text: str
    branch_text: str


def solve_graph(graph: SFGInput) -> SFGSolution:
    """Validate, call the team algorithms, and preserve their numerical steps."""
    validate_sfg(graph)
    if graph.input_node not in graph.nodes or graph.output_node not in graph.nodes:
        raise ValidationError("Input and output must be existing nodes.")
    if any(not isfinite(b.gain) for b in graph.branches):
        raise ValidationError("All gains must be finite numbers.")
    paths, loops = find_paths_and_loops(
        graph.nodes, graph.branch_dicts(), graph.input_node, graph.output_node
    )
    groups = find_non_touching_groups(loops)
    mason = solve_masons_gain(paths, loops)

    def describe(items):
        return "\n\n".join(
            f"{' → '.join(map(str, item.nodes))}\n{item.expression}" for item in items
        ) or "None found."

    combinations = []
    for order, group in groups.items():
        combinations.append(f"{order} mutually non-touching loops ({len(group)})")
        combinations.extend(item.expression for item in group)
        combinations.append("")
    final = ("Undefined (Δ = 0 or within numerical tolerance)" if mason.is_singular
             else exact_number(mason.transfer_gain, mason.transfer_gain_fraction))
    return SFGSolution(
        mason=mason,
        paths_text=describe(paths),
        loops_text=describe(loops),
        combinations_text="\n".join(combinations).strip() or "No mutually non-touching combinations of 2 or more loops.",
        derivation_text=format_mason_solution(mason),
        final_text=final,
        branch_text="\n".join(f"{b.label}: {b.source} → {b.target} = {format_number(b.gain)}" for b in graph.branches),
    )

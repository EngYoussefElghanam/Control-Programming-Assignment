"""Routh controller (Student 5): connects Student 1's panels to the Routh maths.

    result = solve([1, 1, 10, 72, 152, 240])        # pure calculation
    RouthController(input_panel, results_panel)     # GUI wiring (see class)

Terminal:  python -m control_assignment.routh.controller 1 1 10 72 152 240
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Sequence

from .algorithms.poles import (DEFAULT_TOLERANCE, PolesResult, Verification,
                               compute_poles, verify_against_routh)
from .algorithms.stability import StabilityResult, analyze_stability
from ..common.exceptions import ValidationError
from .algorithms.table import Number, RouthError, RouthTable, build_routh_table
from .presentation.solution_formatter import (format_complex, format_equation,
                                               format_full_report, format_html,
                                               format_steps)


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


class RouthController:
    """Wires Student 1's RouthInputPanel to RouthResultsPanel.

    Listens to input_panel.solve_requested (emits a RouthInput), runs solve()
    and fills the results panel via show_result(...) / show_error(...).
    """

    def __init__(self, input_panel, results_panel, tolerance: float = DEFAULT_TOLERANCE):
        self.input_panel = input_panel
        self.results_panel = results_panel
        self.tolerance = tolerance
        self.last_result = None
        input_panel.solve_requested.connect(self.on_solve)

    def on_solve(self, data) -> None:
        try:
            result = solve(data.coefficients, self.tolerance)
        except (RouthError, ValidationError) as err:
            self.last_result = None
            self.results_panel.show_error(str(err))
            return
        self.last_result = result
        t, st, p, v = result.table, result.stability, result.poles, result.verification
        rows = [[float(x) for x in row] for row in t.rows]
        stability_text = (
            f"{st.classification.upper()}  |  sign changes in first column = {st.sign_changes}"
            f"  |  RHP poles (Routh) = {st.rhp_poles}")
        poles_text = (
            "  ".join(f"p{i}={format_complex(z)}" for i, z in enumerate(p.poles, 1))
            + f"  |  numerical RHP poles = {p.rhp_count}  |  "
            + ("agrees with Routh" if v.agrees else "DOES NOT agree with Routh"))
        steps_text = "\n".join([
            f"Characteristic equation: {format_equation(t)}", "",
            format_steps(t), "",
            st.explanation, v.message])
        self.results_panel.show_result(rows, stability_text, poles_text, steps_text)
        table = getattr(self.results_panel, "table", None)
        if table is not None:                      # label rows s^n ... s^0
            table.setVerticalHeaderLabels(t.row_labels)


if __name__ == "__main__":
    from .validation import parse_coefficients
    arg = " ".join(sys.argv[1:]) or "1 1 10 72 152 240"
    try:
        print(solve(parse_coefficients(arg).coefficients).text)
    except (RouthError, ValidationError) as err:
        print(f"Error: {err}")
        sys.exit(1)

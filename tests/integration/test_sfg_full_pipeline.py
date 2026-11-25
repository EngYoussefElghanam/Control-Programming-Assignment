import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
from fractions import Fraction
from pathlib import Path

import pytest
from control_assignment.sfg.models import Branch, SFGInput
from control_assignment.sfg.solution import solve_graph
from control_assignment.common.exceptions import ValidationError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_case(index):
    data = json.loads((FIXTURES / f"sfg_case_{index}.json").read_text())
    return SFGInput(data["nodes"], [Branch(b["from"], b["to"], b["gain"], b["label"]) for b in data["branches"]], "R", "C")


@pytest.mark.parametrize("index,paths,loops,delta,transfer", [
    (1, 8, 5, Fraction(69, 5), Fraction(455, 23)),
    # Case 2's stored expected result omits the cycle X1→X3→X4→X1.
    (2, 2, 5, Fraction(116, 3), Fraction(66, 29)),
])
def test_real_fixture_pipeline(index, paths, loops, delta, transfer):
    graph = load_case(index)
    solution = solve_graph(graph)
    assert len(solution.mason.paths) == paths
    assert len(solution.mason.loops) == loops
    assert solution.mason.determinant.value_fraction == delta
    assert solution.mason.transfer_gain_fraction == transfer
    assert "3 mutually non-touching loops" in solution.combinations_text
    assert "Substitution" in solution.derivation_text and "Mason's Gain Formula" in solution.derivation_text
    assert "×" in solution.paths_text and "×" in solution.loops_text


def test_singular_and_no_path():
    singular = solve_graph(SFGInput(["A", "B"], [Branch("A", "B", 2, "a"), Branch("A", "A", 1, "h")], "A", "B"))
    assert singular.mason.is_singular and "Undefined" in singular.final_text
    disconnected = solve_graph(SFGInput(["A", "B", "C"], [Branch("A", "B", 1, "a")], "A", "C"))
    assert disconnected.mason.transfer_gain == 0


def test_invalid_nonfinite_gain():
    with pytest.raises(ValidationError):
        solve_graph(SFGInput(["A", "B"], [Branch("A", "B", float("nan"), "a")], "A", "B"))


def test_main_window_load_and_solve():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from control_assignment.ui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    controller = window.sfg_controller
    controller.load_graph(FIXTURES / "sfg_case_1.json")
    assert controller.pages.currentIndex() == 1
    assert len(controller.canvas.branch_items) == 13
    assert "455/23" in controller.results.summary.text()
    assert "3 mutually non-touching loops" in controller.results.sections["combinations"].toPlainText()
    window.sfg_input.on_solve()
    assert controller.last_solution.mason.transfer_gain_fraction == Fraction(455, 23)
    window.close()


def test_no_path_with_singular_determinant_is_not_reported_as_zero():
    result = solve_graph(SFGInput(["A", "B"], [Branch("A", "A", 1, "h")], "A", "B"))
    assert result.mason.is_singular
    assert "ERROR" in result.derivation_text
    assert "T = 0" not in result.derivation_text

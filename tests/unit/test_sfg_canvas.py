import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication
from control_assignment.sfg.models import Branch, SFGInput
from control_assignment.sfg.ui.graph_canvas import GraphCanvas


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_graph_draws_every_node_and_branch(app):
    graph = SFGInput(["A", "B", "C", "D"], [Branch("A", "B", 2, "f"), Branch("A", "B", 3, "p"),
                      Branch("B", "A", -1, "h"), Branch("B", "B", .5, "s"), Branch("B", "C", 1, "g")], "A", "C")
    canvas = GraphCanvas()
    canvas.set_graph(graph)
    assert set(canvas.node_items) == set(graph.nodes)
    assert set(canvas.branch_items) == {b.label for b in graph.branches}
    assert canvas.gain_labels["h"].text() == "h = -1"
    assert canvas.branch_items["f"].path() != canvas.branch_items["p"].path()
    assert canvas.branch_items["s"].path().length() > 0
    assert all(canvas.sceneRect().contains(item.sceneBoundingRect()) for item in canvas.scene().items())
    canvas.clear_graph()
    assert not canvas.node_items and not canvas.branch_items


def test_zoom_and_refit(app):
    canvas = GraphCanvas()
    canvas.resize(800, 500)
    canvas.set_graph(SFGInput(["A", "B"], [Branch("A", "B", 1, "a")], "A", "B"))
    original = canvas.transform().m11()
    canvas.zoom(1.2)
    assert canvas.transform().m11() == pytest.approx(original * 1.2)
    canvas.fit_graph()
    assert canvas.transform().m11() == pytest.approx(original)

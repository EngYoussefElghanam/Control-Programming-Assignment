"""Student 2: connect the existing input signal to the SFG solver and views."""
import json
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, QFileDialog, QMessageBox

from ..common.exceptions import ValidationError
from .models import Branch, SFGInput
from .solution import solve_graph
from .ui.graph_canvas import GraphCanvas
from .ui.results_panel import SFGResultsPanel


class SFGController(QWidget):
    def __init__(self, input_panel, parent=None):
        super().__init__(parent)
        self.input_panel = input_panel
        self.canvas = GraphCanvas()
        self.results = SFGResultsPanel()
        self.last_solution = None
        layout = QVBoxLayout(self)
        self.status = QLabel("1. Enter a graph or load a JSON sample.  2. Solve.  3. Inspect graph and calculations.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.pages = QTabWidget()
        input_page = QWidget()
        input_layout = QVBoxLayout(input_page)
        load = QPushButton("Load sample / JSON graph…")
        load.clicked.connect(self.choose_graph)
        input_layout.addWidget(load)
        input_layout.addWidget(input_panel, 1)
        self.pages.addTab(input_page, "1 · Input")
        graph_page = QWidget()
        graph_layout = QVBoxLayout(graph_page)
        actions = QHBoxLayout()
        legend = QLabel("Arrows show direction · labels show branch gain · drag to pan")
        legend.setWordWrap(True)
        actions.addWidget(legend, 1)
        for text, action in (("−", lambda: self.canvas.zoom(1/1.2)), ("+", lambda: self.canvas.zoom(1.2)), ("Fit graph", self.canvas.fit_graph)):
            button = QPushButton(text)
            button.clicked.connect(action)
            actions.addWidget(button)
        graph_layout.addLayout(actions)
        graph_layout.addWidget(self.canvas, 1)
        self.pages.addTab(graph_page, "2 · Graph")
        self.pages.addTab(self.results, "3 · Calculations")
        layout.addWidget(self.pages, 1)
        self.input_panel.solve_requested.connect(self.solve)

    def choose_graph(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load graph", "", "JSON files (*.json)")
        if filename:
            try:
                self.load_graph(filename)
            except (OSError, ValueError, TypeError, KeyError, ValidationError) as exc:
                QMessageBox.warning(self, "Cannot load graph", str(exc))

    def load_graph(self, filename):
        """Load team fixture schema (only input data, never expected answers)."""
        data = json.loads(Path(filename).read_text(encoding="utf-8"))
        nodes = list(data["nodes"])
        if not all(isinstance(n, str) for n in nodes):
            raise ValueError("Node names must be strings.")
        branches = [Branch(b["from"], b["to"], float(b["gain"]), b.get("label", f"b{i}"))
                    for i, b in enumerate(data["branches"], 1)]
        if not nodes:
            raise ValueError("The graph has no nodes.")
        # Case 2 omits endpoints; use conventional R/C names if present.
        graph = SFGInput(nodes, branches, data.get("input_node", "R" if "R" in nodes else nodes[0]),
                         data.get("output_node", "C" if "C" in nodes else nodes[-1]))
        result = solve_graph(graph)
        self.input_panel.nodes = list(graph.nodes)
        self.input_panel.branches = list(graph.branches)
        self.input_panel.refresh_lists()
        self.input_panel.in_box.setCurrentText(graph.input_node)
        self.input_panel.out_box.setCurrentText(graph.output_node)
        self._display(graph, result)

    def solve(self, graph):
        """Handle Solve clicks; do not leave stale results after a failed calculation."""
        try:
            result = solve_graph(graph)
        except (ValidationError, ValueError, ArithmeticError) as exc:
            self.last_solution = None
            self.canvas.clear_graph()
            self.results.clear_results()
            self.status.setText("Cannot solve graph. Check the input.")
            self.pages.setCurrentIndex(0)
            QMessageBox.warning(self, "SFG calculation", str(exc))
            return
        self._display(graph, result)

    def _display(self, graph, result):
        self.canvas.set_graph(graph)
        self.results.show_result(result)
        self.last_solution = result
        self.status.setText(f"Last solved: {graph.input_node} → {graph.output_node}: T = {result.final_text}. Calculations are in tab 3.")
        self.pages.setCurrentIndex(1)
        self.canvas.fit_graph()

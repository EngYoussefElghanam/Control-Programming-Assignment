from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QListWidget, QComboBox, QMessageBox)

from ...common.exceptions import ValidationError
from ...common.numeric import parse_number
from ..models import Branch, SFGInput
from ..validation import validate_sfg


class SFGInputPanel(QWidget):
    solve_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.nodes = []
        self.branches = []

        # --- nodes ---
        self.node_edit = QLineEdit()
        self.node_edit.setPlaceholderText("node name, e.g. X1")
        add_node = QPushButton("Add node")
        del_node = QPushButton("Delete selected")
        self.node_list = QListWidget()
        add_node.clicked.connect(self.add_node)
        del_node.clicked.connect(self.delete_node)

        # --- branches ---
        self.from_box, self.to_box = QComboBox(), QComboBox()
        self.gain_edit = QLineEdit()
        self.gain_edit.setPlaceholderText("gain, e.g. 2 or -1/3")
        add_branch = QPushButton("Add branch")
        del_branch = QPushButton("Delete selected")
        self.branch_list = QListWidget()
        add_branch.clicked.connect(self.add_branch)
        del_branch.clicked.connect(self.delete_branch)

        # --- input / output ---
        self.in_box, self.out_box = QComboBox(), QComboBox()

        solve = QPushButton("Solve")
        solve.clicked.connect(self.on_solve)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nodes"))
        row = QHBoxLayout()
        for w in (self.node_edit, add_node, del_node):
            row.addWidget(w)
        layout.addLayout(row)
        layout.addWidget(self.node_list)

        layout.addWidget(QLabel("Branches (from → to, gain)"))
        row = QHBoxLayout()
        for w in (self.from_box, self.to_box, self.gain_edit, add_branch, del_branch):
            row.addWidget(w)
        layout.addLayout(row)
        layout.addWidget(self.branch_list)

        row = QHBoxLayout()
        for w in (QLabel("Input node:"), self.in_box, QLabel("Output node:"), self.out_box):
            row.addWidget(w)
        layout.addLayout(row)
        layout.addWidget(solve)

    # ---------- helpers ----------
    def show_error(self, message):
        QMessageBox.warning(self, "Input error", message)

    def refresh_boxes(self):
        """Keep the 4 drop-down lists equal to the node list."""
        for box in (self.from_box, self.to_box, self.in_box, self.out_box):
            old = box.currentText()
            box.clear()
            box.addItems(self.nodes)
            if old in self.nodes:
                box.setCurrentText(old)

    def refresh_lists(self):
        self.node_list.clear()
        self.node_list.addItems(self.nodes)
        self.branch_list.clear()
        for b in self.branches:
            self.branch_list.addItem(f"{b.label}:  {b.source} → {b.target}   gain = {b.gain:g}")
        self.refresh_boxes()

    # ---------- buttons ----------
    def add_node(self):
        name = self.node_edit.text().strip()
        if not name:
            return self.show_error("Node name is empty.")
        if name in self.nodes:
            return self.show_error(f"Node '{name}' already exists.")
        self.nodes.append(name)
        self.node_edit.clear()
        self.refresh_lists()

    def delete_node(self):
        row = self.node_list.currentRow()
        if row < 0:
            return
        name = self.nodes.pop(row)
        # a branch cannot exist without its nodes
        self.branches = [b for b in self.branches if name not in (b.source, b.target)]
        self.refresh_lists()

    def add_branch(self):
        try:
            gain = parse_number(self.gain_edit.text(), "Gain")
        except ValidationError as e:
            return self.show_error(str(e))
        if not self.nodes:
            return self.show_error("Add nodes first.")
        label = f"b{len(self.branches) + 1}"
        while label in [b.label for b in self.branches]:   # keep labels unique
            label += "_"
        self.branches.append(Branch(self.from_box.currentText(),
                                    self.to_box.currentText(), gain, label))
        self.gain_edit.clear()
        self.refresh_lists()

    def delete_branch(self):
        row = self.branch_list.currentRow()
        if row >= 0:
            self.branches.pop(row)
            self.refresh_lists()

    def get_input(self):
        return SFGInput(list(self.nodes), list(self.branches),
                        self.in_box.currentText(), self.out_box.currentText())

    def on_solve(self):
        sfg = self.get_input()
        try:
            validate_sfg(sfg)
        except ValidationError as e:
            return self.show_error(str(e))
        self.solve_requested.emit(sfg)

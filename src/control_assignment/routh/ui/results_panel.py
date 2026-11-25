from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QTextEdit)

from ...common.presentation import format_number


class RouthResultsPanel(QWidget):
    """Only shows data. Student 5 calls show_result(...) with the calculated values."""

    def __init__(self):
        super().__init__()
        self.table = QTableWidget()
        self.stability = QLabel("Stability: -")
        self.poles = QLabel("Poles: -")
        self.steps = QTextEdit()
        self.steps.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Routh table"))
        layout.addWidget(self.table)
        layout.addWidget(self.stability)
        layout.addWidget(self.poles)
        layout.addWidget(QLabel("Steps"))
        layout.addWidget(self.steps)

    def show_result(self, rows, stability_text, poles_text, steps_text):
        """rows: list of lists of numbers, e.g. [[1, 3], [2, 4], [1, 0]]."""
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(max(len(r) for r in rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(format_number(value)))
        self.stability.setText("Stability: " + stability_text)
        self.poles.setText("Poles: " + poles_text)
        self.steps.setPlainText(steps_text)

    def show_error(self, message):
        self.stability.setText("Error: " + message)

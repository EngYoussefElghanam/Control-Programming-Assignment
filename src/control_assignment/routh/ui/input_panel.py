from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox)

from ...common.exceptions import ValidationError
from ..validation import parse_coefficients


class RouthInputPanel(QWidget):
    # Student 5 connects to this signal. It sends a valid RouthInput.
    solve_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("1, 2, 3, 4")
        button = QPushButton("Check stability")
        button.clicked.connect(self.on_solve)
        self.edit.returnPressed.connect(self.on_solve)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Coefficients, highest power first.\n"
                                "Example: s^3 + 2s^2 + 3s + 4  →  1, 2, 3, 4"))
        layout.addWidget(self.edit)
        layout.addWidget(button)

    def on_solve(self):
        try:
            data = parse_coefficients(self.edit.text())
        except ValidationError as e:
            QMessageBox.warning(self, "Input error", str(e))
            return
        self.solve_requested.emit(data)

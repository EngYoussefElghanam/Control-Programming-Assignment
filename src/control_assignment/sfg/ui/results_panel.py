"""Read-only, scrollable SFG results; arithmetic stays in the team algorithms."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QTabWidget, QPushButton, QApplication

from ..solution import SFGSolution


class SFGResultsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.summary = QLabel("No solution yet")
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.summary.setStyleSheet("font-size: 18px; font-weight: bold; color: #155e75; padding: 12px; background: #e9f5fa; border-radius: 8px;")
        layout.addWidget(self.summary)
        self.tabs = QTabWidget()
        self.sections = {}
        for key, label in (("paths", "Forward paths"), ("loops", "Loops"),
                           ("combinations", "Non-touching"), ("derivation", "Δ, Δᵢ & Mason"), ("branches", "Branch gains")):
            editor = QPlainTextEdit()
            editor.setReadOnly(True)
            editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            editor.setPlaceholderText("Solve a graph to display the calculations.")
            self.sections[key] = editor
            self.tabs.addTab(editor, label)
        layout.addWidget(self.tabs, 1)
        actions = QHBoxLayout()
        self.copy_button = QPushButton("Copy all calculations")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_all)
        actions.addStretch()
        actions.addWidget(self.copy_button)
        layout.addLayout(actions)

    def clear_results(self):
        self.summary.setText("No solution yet")
        for editor in self.sections.values():
            editor.clear()
        self.copy_button.setEnabled(False)

    def show_result(self, result: SFGSolution):
        self.summary.setText(f"T = {result.final_text}    |    {len(result.mason.paths)} paths · {len(result.mason.loops)} loops")
        for key, value in (("paths", result.paths_text), ("loops", result.loops_text),
                           ("combinations", result.combinations_text), ("derivation", result.derivation_text), ("branches", result.branch_text)):
            editor = self.sections[key]
            editor.setPlainText(value)
            editor.verticalScrollBar().setValue(0)
        self.tabs.setCurrentIndex(0)
        self.copy_button.setEnabled(True)

    def copy_all(self):
        text = [self.summary.text()]
        for i, editor in enumerate(self.sections.values()):
            text.extend((self.tabs.tabText(i), editor.toPlainText()))
        QApplication.clipboard().setText("\n\n".join(text))

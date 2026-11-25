import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    qss = Path(__file__).parent / "ui" / "styles.qss"
    app.setStyleSheet(qss.read_text())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

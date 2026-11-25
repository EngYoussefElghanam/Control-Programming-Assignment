from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout

from ..sfg.ui.input_panel import SFGInputPanel
from ..sfg.controller import SFGController
from ..routh.ui.input_panel import RouthInputPanel
from ..routh.ui.results_panel import RouthResultsPanel
from ..routh.controller import RouthController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Assignment")
        self.resize(900, 650)

        self.sfg_input = SFGInputPanel()
        self.routh_input = RouthInputPanel()
        self.routh_results = RouthResultsPanel()
        self.routh_controller = RouthController(self.routh_input, self.routh_results)

        # Routh tab = input on top, results below
        routh_page = QWidget()
        layout = QVBoxLayout(routh_page)
        layout.addWidget(self.routh_input)
        layout.addWidget(self.routh_results)

        # The 2 tabs are the "choice" between the 2 parts
        self.tabs = QTabWidget()
        self.sfg_controller = SFGController(self.sfg_input)
        self.tabs.addTab(self.sfg_controller, "Signal Flow Graph")
        self.tabs.addTab(routh_page, "Routh Stability")
        self.setCentralWidget(self.tabs)

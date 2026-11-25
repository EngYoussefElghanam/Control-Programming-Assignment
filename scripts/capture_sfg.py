"""Generate actual Qt GUI screenshots of both SFG cases for the team report.

Run from repository root: PYTHONPATH=src python scripts/capture_sfg.py
"""
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication
from control_assignment.ui.main_window import MainWindow

ROOT = Path(__file__).resolve().parents[1]


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setStyleSheet((ROOT / "src/control_assignment/ui/styles.qss").read_text())
    window.resize(1500, 950)
    window.show()
    app.processEvents()
    controller = window.sfg_controller
    window.tabs.setCurrentIndex(0)
    output = ROOT / "docs/report/screenshots/sfg"
    output.mkdir(parents=True, exist_ok=True)

    def capture(name):
        app.processEvents()
        path = output / f"{name}.png"
        if not window.grab().save(str(path)):
            raise OSError(f"Could not save {path}")
        print(path.relative_to(ROOT))

    for case in (1, 2):
        controller.load_graph(ROOT / f"tests/fixtures/sfg_case_{case}.json")
        prefix = f"case_{case}"
        controller.pages.setCurrentIndex(0)
        capture(f"{prefix}_01_input")
        controller.pages.setCurrentIndex(1)
        app.processEvents()
        controller.canvas.fit_graph()
        capture(f"{prefix}_02_graph")
        controller.pages.setCurrentIndex(2)
        for i, (key, editor) in enumerate(controller.results.sections.items(), start=3):
            controller.results.tabs.setCurrentIndex(i-3)
            app.processEvents()
            bar = editor.verticalScrollBar()
            step = max(1, int(bar.pageStep() * .8))
            positions = sorted(set(range(0, bar.maximum()+1, step)) | {bar.maximum()})
            for page, position in enumerate(positions, start=1):
                bar.setValue(position)
                capture(f"{prefix}_{i:02d}_{key}_{page:02d}")
    window.close()


if __name__ == "__main__":
    main()

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"   # no real window needed

from PySide6.QtWidgets import QApplication

from control_assignment.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])


def test_window_has_two_tabs():
    w = MainWindow()
    assert w.tabs.count() == 2


def test_sfg_panel_builds_valid_input_and_emits():
    w = MainWindow()
    p = w.sfg_input
    got = []
    p.solve_requested.connect(got.append)
    for name in ("R", "X1", "C"):
        p.node_edit.setText(name); p.add_node()
    for src, dst, g in (("R", "X1", "1"), ("X1", "C", "2")):
        p.from_box.setCurrentText(src); p.to_box.setCurrentText(dst)
        p.gain_edit.setText(g); p.add_branch()
    p.in_box.setCurrentText("R"); p.out_box.setCurrentText("C")
    p.on_solve()
    assert len(got) == 1 and len(got[0].branches) == 2


def test_routh_panel_emits():
    w = MainWindow()
    got = []
    w.routh_input.solve_requested.connect(got.append)
    w.routh_input.edit.setText("1 2 3 4")
    w.routh_input.on_solve()
    assert got[0].coefficients == [1, 2, 3, 4]


def test_routh_results_show():
    w = MainWindow()
    w.routh_results.show_result([[1, 3], [2, 4], [1, 0]], "Stable", "none in RHP", "steps")
    assert w.routh_results.table.rowCount() == 3

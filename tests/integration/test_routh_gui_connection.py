"""RouthController wiring, tested with fake panels (no Qt needed)."""
from control_assignment.routh.controller import RouthController
from control_assignment.routh.models import RouthInput


class FakeSignal:
    def __init__(self):
        self.slots = []

    def connect(self, fn):
        self.slots.append(fn)

    def emit(self, value):
        for fn in self.slots:
            fn(value)


class FakeInput:
    def __init__(self):
        self.solve_requested = FakeSignal()


class FakeResults:
    def __init__(self):
        self.result = None
        self.error = None

    def show_result(self, rows, stability_text, poles_text, steps_text):
        self.result = (rows, stability_text, poles_text, steps_text)

    def show_error(self, message):
        self.error = message


def make():
    inp, res = FakeInput(), FakeResults()
    return inp, res, RouthController(inp, res)


def test_unstable_example_reaches_results_panel():
    inp, res, _ = make()
    inp.solve_requested.emit(RouthInput([1, 1, 10, 72, 152, 240]))
    rows, stability, poles, steps = res.result
    assert len(rows) == 6 and rows[2][0] == -62
    assert "UNSTABLE" in stability and "RHP poles (Routh) = 2" in stability
    assert "numerical RHP poles = 2" in poles and "agrees" in poles
    assert "(1*10 - 1*72) / 1 = -62" in steps


def test_stable_example():
    inp, res, _ = make()
    inp.solve_requested.emit(RouthInput([1.0, 15.0, 85.0, 225.0, 274.0, 120.0]))
    assert res.result[1].startswith("STABLE")
    assert res.error is None


def test_invalid_input_goes_to_show_error():
    inp, res, _ = make()
    inp.solve_requested.emit(RouthInput([1, 0, 3]))        # missing coefficient
    assert res.result is None and "non-zero" in res.error
    inp.solve_requested.emit(RouthInput([1, -2, 3]))       # mixed signs
    assert "same sign" in res.error

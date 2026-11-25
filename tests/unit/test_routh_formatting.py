from control_assignment.routh.controller import solve


def test_text_report_sections_and_steps():
    r = solve([1, 1, 10, 72, 152, 240])
    for needle in ("Routh table", "Calculation steps", "Stability analysis",
                   "Numerical pole verification", "(1*10 - 1*72) / 1 = -62",
                   "UNSTABLE", "Verified"):
        assert needle in r.text


def test_html_report():
    r = solve([1, 15, 85, 225, 274, 120])
    assert "<table" in r.html and "STABLE" in r.html and "s<sup>5</sup>" in r.html

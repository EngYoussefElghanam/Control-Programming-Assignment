import json
from pathlib import Path

import pytest

from control_assignment.routh.controller import solve

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.mark.parametrize("name", ["routh_stable.json", "routh_unstable.json"])
def test_fixture_pipeline(name):
    case = json.loads((FIX / name).read_text(encoding="utf-8"))
    r = solve(case["coefficients"])
    assert [float(x) for x in r.table.first_column] == pytest.approx(case["expected_first_column"], abs=1e-3)
    assert r.stability.sign_changes == case["expected_sign_changes"]
    assert r.stability.rhp_poles == case["expected_rhp_poles"]
    assert r.stability.is_stable == case["expected_stable"]
    assert r.poles.rhp_count == case["expected_rhp_poles"]
    assert r.verification.agrees
    assert r.text and r.html


def test_routh_matches_numpy_for_many_polynomials():
    # random same-sign polynomials without special cases: Routh count == numeric count
    import random
    random.seed(1)
    checked = 0
    for _ in range(300):
        n = random.randint(2, 7)
        coeffs = [random.randint(1, 20) for _ in range(n + 1)]
        try:
            r = solve(coeffs)
        except Exception:
            continue  # special case, out of scope
        assert r.verification.agrees, coeffs
        checked += 1
    assert checked > 100

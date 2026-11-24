
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from src.control_assignment.sfg.algorithms.determinant import compute_determinant
from src.control_assignment.sfg.algorithms.mason import solve_masons_gain
from src.control_assignment.sfg.algorithms.non_touching import (
    find_non_touching_groups,
    loops_touch,
    sum_products_by_order,
)
from src.control_assignment.sfg.algorithms.traversal import find_paths_and_loops

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sfg_case_1.json"


def _case():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    paths, loops = find_paths_and_loops(
        data["nodes"], data["branches"], data["input_node"], data["output_node"]
    )
    return data, paths, loops


def test_no_loops_or_single_loop_has_no_groups():
    assert find_non_touching_groups([]) == {}
    _, _, loops = _case()
    assert find_non_touching_groups(loops[:1]) == {}


def test_touching_definition_is_shared_node():
    _, _, loops = _case()
    by_id = {l.loop_id: l for l in loops}
    assert loops_touch(by_id["L1"], by_id["L2"])       # share X1, X2
    assert not loops_touch(by_id["L1"], by_id["L4"])   # {X1,X2} vs {X3,X4}


def test_case_1_pairs_and_triplet_match_fixture():
    data, _, loops = _case()
    groups = find_non_touching_groups(loops)
    got = {
        str(k): [{"loops": list(g.loop_ids), "product": g.product} for g in v]
        for k, v in groups.items()
    }
    assert got == data["non_touching"]
    assert len(groups[2]) == 5 and len(groups[3]) == 1


def test_triplet_requires_all_pairs_non_touching():
    _, _, loops = _case()
    triple = find_non_touching_groups(loops)[3][0]
    ids = triple.loop_ids
    for i in range(3):
        for j in range(i + 1, 3):
            assert not loops_touch(triple.loops[i], triple.loops[j])
    assert triple.product == 8
    assert triple.expression == "L1L4L5 = L1 × L4 × L5 = -2 × -8 × 0.5 = 8"
    assert ids == ("L1", "L4", "L5")


def test_min_and_max_order_filters():
    _, _, loops = _case()
    assert set(find_non_touching_groups(loops, min_order=3)) == {3}
    assert set(find_non_touching_groups(loops, max_order=2)) == {2}
    assert set(find_non_touching_groups(loops, min_order=1)) == {1, 2, 3}


def test_sums_by_order():
    _, _, loops = _case()
    sums = sum_products_by_order(find_non_touching_groups(loops))
    assert sums == {2: Fraction(16 - 1 + Fraction(3, 10) - Fraction(3, 5) - 4), 3: Fraction(8)}


def test_handoff_to_student4_matches_expected_results():
    """Student 3's output must plug straight into determinant.py / mason.py."""
    data, paths, loops = _case()
    exp = data["expected"]
    assert compute_determinant(loops).value == exp["determinant"]
    result = solve_masons_gain(paths, loops)
    assert not result.is_singular
    assert result.numerator == exp["numerator"]
    assert str(result.transfer_gain_fraction) == exp["transfer_gain_fraction"]
    for term in result.path_terms:
        assert term.cofactor.value == exp["cofactors"][term.path.path_id]
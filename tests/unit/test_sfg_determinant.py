"""Unit tests for SFG determinant (Δ) and path cofactor (Δᵢ) calculations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.control_assignment.sfg.algorithms.determinant  import (
    LoopInfo,
    PathInfo,
    compute_cofactor,
    compute_determinant,
    find_non_touching_combinations,
    loop_touches_path,
    loops_touch,
    normalize_loops,
    normalize_paths,
)

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "sfg_case_2.json"


def test_empty_loops_determinant_is_one() -> None:
    result = compute_determinant([])
    assert result.value == 1.0
    assert result.max_order == 0
    assert result.combinations_by_order == {}


def test_loop_touch_detection() -> None:
    l1, l2, l3 = normalize_loops(
        [
            {"id": "L1", "nodes": ["A", "B", "A"], "gain": -2},
            {"id": "L2", "nodes": ["B", "C", "B"], "gain": -3},
            {"id": "L3", "nodes": ["D", "E", "D"], "gain": -4},
        ]
    )
    assert loops_touch(l1, l2) is True
    assert loops_touch(l1, l3) is False
    assert loops_touch(l2, l3) is False


def test_non_touching_combinations_up_to_order_three() -> None:
    loops = normalize_loops(
        [
            {"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": -2},
            {"id": "L2", "nodes": ["X3", "X4", "X3"], "gain": -3},
            {"id": "L3", "nodes": ["X5", "X6", "X5"], "gain": -1},
            {"id": "L4", "nodes": ["X1", "X2", "X3", "X4", "X1"], "gain": -4},
        ]
    )
    combos = find_non_touching_combinations(loops)

    assert set(combos.keys()) == {1, 2, 3}
    assert len(combos[1]) == 4
    assert len(combos[2]) == 4
    assert len(combos[3]) == 1
    assert combos[3][0].loop_ids == ("L1", "L2", "L3")
    assert combos[3][0].product == pytest.approx(-6.0)


def test_determinant_and_cofactors_from_fixture() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    det = compute_determinant(data["loops"])
    assert det.value == pytest.approx(data["expected"]["determinant"])

    for path_data in data["forward_paths"]:
        cofactor = compute_cofactor(path_data, data["loops"])
        expected_delta_i = data["expected"]["cofactors"][path_data["id"]]
        assert cofactor.value == pytest.approx(expected_delta_i)


def test_cofactor_excludes_only_touching_loops() -> None:
    path = {"id": "M1", "nodes": ["R", "X1", "X2", "C"], "gain": 5}
    loops = [
        {"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": -2},  # touches M1
        {"id": "L2", "nodes": ["X3", "X4", "X3"], "gain": -3},  # disjoint
        {"id": "L3", "nodes": ["X5", "X6", "X5"], "gain": -4},  # disjoint
    ]
    cofactor = compute_cofactor(path, loops, path_index=1)
    assert [lp.loop_id for lp in cofactor.excluded_loops] == ["L1"]
    assert [lp.loop_id for lp in cofactor.active_loops] == ["L2", "L3"]
    # Δ1 = 1 - (-3 + -4) + (-3 * -4) = 1 + 7 + 12 = 20
    assert cofactor.value == pytest.approx(20.0)


def test_accepts_dataclass_instances_directly() -> None:
    p = PathInfo(path_id="M1", nodes=("R", "C"), gain=10.0, gain_fraction=10)
    l = LoopInfo(loop_id="L1", nodes=("R", "R"), gain=-1.0, gain_fraction=-1)
    assert loop_touches_path(l, p) is True
    assert normalize_paths([p])[0] is p
    assert normalize_loops([l])[0] is l


from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.control_assignment.sfg.algorithms.traversal import (
    find_forward_paths,
    find_loops,
    find_paths_and_loops,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _b(src, dst, gain, label=None):
    d = {"from": src, "to": dst, "gain": gain}
    if label:
        d["label"] = label
    return d


def test_simple_chain_single_path_and_gain():
    paths = find_forward_paths(["A", "B", "C"], [_b("A", "B", 2, "w1"), _b("B", "C", 3, "w2")], "A", "C")
    assert len(paths) == 1
    assert paths[0].nodes == ("A", "B", "C")
    assert paths[0].gain == 6
    assert paths[0].expression == "M1 = w1 × w2 = 2 × 3 = 6"


def test_no_path_returns_empty():
    assert find_forward_paths(["A", "B", "C"], [_b("A", "B", 1)], "A", "C") == []


def test_parallel_branches_give_separate_paths():
    paths = find_forward_paths(["A", "B"], [_b("A", "B", 2, "p"), _b("A", "B", 5, "q")], "A", "B")
    assert sorted(p.gain for p in paths) == [2, 5]


def test_forward_paths_never_repeat_a_node():
    nodes = ["A", "B", "C", "D"]
    branches = [_b("A", "B", 1), _b("B", "C", 1), _b("C", "B", 1), _b("C", "D", 1)]
    paths = find_forward_paths(nodes, branches, "A", "D")
    assert [p.nodes for p in paths] == [("A", "B", "C", "D")]


def test_self_loop_and_two_node_loop():
    loops = find_loops(["A", "B"], [_b("A", "A", 0.5, "s"), _b("A", "B", 2, "f"), _b("B", "A", -1, "h")])
    assert len(loops) == 2
    by_nodes = {frozenset(l.nodes): l for l in loops}
    assert by_nodes[frozenset({"A"})].gain == 0.5
    assert by_nodes[frozenset({"A", "B"})].gain == -2


def test_each_loop_reported_once_regardless_of_start_node():
    # 3-cycle A→B→C→A must appear a single time.
    loops = find_loops(["A", "B", "C"], [_b("A", "B", 1), _b("B", "C", 1), _b("C", "A", 1)])
    assert len(loops) == 1
    assert loops[0].nodes[0] == loops[0].nodes[-1]


def test_two_distinct_loops_through_same_nodes():
    loops = find_loops(["A", "B"], [_b("A", "B", 1, "a"), _b("B", "A", 2, "b"), _b("B", "A", 3, "c")])
    assert sorted(l.gain for l in loops) == [2, 3]


def test_fractional_gain_is_exact():
    loops = find_loops(["A", "B"], [_b("A", "B", 1), _b("B", "A", -0.1)])
    assert str(loops[0].gain_fraction) == "-1/10"


@pytest.mark.parametrize(
    "bad",
    [
        dict(nodes=["A", "B"], branches=[_b("A", "Z", 1)], i="A", o="B"),
        dict(nodes=["A", "B"], branches=[_b("A", "B", 1)], i="Q", o="B"),
        dict(nodes=["A", "B"], branches=[_b("A", "B", 1)], i="A", o="A"),
        dict(nodes=["A", "B"], branches=[_b("A", "B", 1, "x"), _b("B", "A", 1, "x")], i="A", o="B"),
        dict(nodes=["A", "B"], branches=[{"from": "A", "to": "B"}], i="A", o="B"),
    ],
)
def test_invalid_input_raises_value_error(bad):
    with pytest.raises(ValueError):
        find_forward_paths(bad["nodes"], bad["branches"], bad["i"], bad["o"])


def test_case_1_fixture_paths_and_loops():
    data = _load("sfg_case_1.json")
    paths, loops = find_paths_and_loops(
        data["nodes"], data["branches"], data["input_node"], data["output_node"]
    )
    assert [(p.path_id, p.nodes, p.branches, p.gain) for p in paths] == [
        (p["id"], tuple(p["nodes"]), tuple(p["branches"]), p["gain"])
        for p in data["forward_paths"]
    ]
    assert [(l.loop_id, l.nodes, l.branches, l.gain) for l in loops] == [
        (l["id"], tuple(l["nodes"]), tuple(l["branches"]), l["gain"])
        for l in data["loops"]
    ]
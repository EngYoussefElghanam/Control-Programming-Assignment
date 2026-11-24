"""Unit tests for Mason's Gain Formula solver."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from src.control_assignment.sfg.algorithms.mason import ZeroDeterminantError, solve_masons_gain

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "sfg_case_2.json"


def test_standard_negative_feedback_loop() -> None:
    """T = G / (1 + G*H) for G = 10, H = 0.5 -> T = 10 / 6 = 5/3."""
    paths = [{"id": "M1", "nodes": ["R", "E", "C"], "gain": 10.0}]
    loops = [{"id": "L1", "nodes": ["E", "C", "E"], "gain": -5.0}]

    res = solve_masons_gain(paths, loops)
    assert res.is_singular is False
    assert res.determinant.value == pytest.approx(6.0)
    assert res.path_terms[0].cofactor.value == pytest.approx(1.0)
    assert res.transfer_gain == pytest.approx(10.0 / 6.0)
    assert res.transfer_gain_fraction == Fraction(5, 3)


def test_sfg_case_2_fixture() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    res = solve_masons_gain(data["forward_paths"], data["loops"])

    assert res.is_singular is False
    assert res.determinant.value == pytest.approx(data["expected"]["determinant"])
    assert res.numerator == pytest.approx(data["expected"]["numerator"])
    assert res.transfer_gain == pytest.approx(data["expected"]["transfer_gain"])
    assert str(res.transfer_gain_fraction) == data["expected"]["transfer_gain_fraction"]


def test_zero_determinant_handled_safely_by_default() -> None:
    """Positive unity feedback loop (L1 = +1) produces Δ = 1 - 1 = 0 without crashing."""
    paths = [{"id": "M1", "nodes": ["R", "X1", "C"], "gain": 4.0}]
    loops = [{"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": 1.0}]

    res = solve_masons_gain(paths, loops)
    assert res.is_singular is True
    assert res.determinant.value == pytest.approx(0.0)
    assert res.transfer_gain is None
    assert res.transfer_gain_fraction is None
    assert res.error_message is not None
    assert "Δ = 0" in res.error_message


def test_zero_determinant_raises_when_requested() -> None:
    paths = [{"id": "M1", "nodes": ["R", "X1", "C"], "gain": 4.0}]
    loops = [
        {"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": 0.5},
        {"id": "L2", "nodes": ["X3", "X4", "X3"], "gain": 0.5},
    ]
    # Δ = 1 - (0.5 + 0.5) + (0.5 * 0.5) = 0.25 (non-zero)
    assert solve_masons_gain(paths, loops, raise_on_zero_delta=True).is_singular is False

    # Now make L1 = 1.0, L2 = 0.0 -> Δ = 0
    loops_singular = [{"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": 1.0}]
    with pytest.raises(ZeroDeterminantError) as exc_info:
        solve_masons_gain(paths, loops_singular, raise_on_zero_delta=True)
    assert exc_info.value.result.is_singular is True


def test_no_forward_paths_returns_zero_gain() -> None:
    loops = [{"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": -2.0}]
    res = solve_masons_gain([], loops)
    assert res.is_singular is False
    assert res.determinant.value == pytest.approx(3.0)
    assert res.transfer_gain == pytest.approx(0.0)
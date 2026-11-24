"""Unit tests for step-by-step Mason's Gain Formula solution formatting."""

from __future__ import annotations

import json
from pathlib import Path

from src.control_assignment.sfg.algorithms.mason import solve_masons_gain
from src.control_assignment.sfg.presentation.solution_formatter import format_mason_solution

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "sfg_case_2.json"


def test_formatted_output_contains_all_required_sections() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    res = solve_masons_gain(data["forward_paths"], data["loops"])
    output = format_mason_solution(res)

    # Check structural headings and required intermediate steps
    assert "=== Forward Paths ===" in output
    assert "=== Feedback Loops ===" in output
    assert "=== Δ Calculation ===" in output
    assert "[2 Non-Touching Loops]" in output
    assert "[3 Non-Touching Loops]" in output
    assert "L1 · L2 · L3" in output
    assert "=== Δ1 Calculation ===" in output
    assert "=== Δ2 Calculation ===" in output
    assert "Excluded touching loops:" in output
    assert "Product M1 · Δ1 = 24 × 2 = 48" in output
    assert "Product M2 · Δ2 = 20 × 2 = 40" in output
    assert "=== Mason's Gain Formula ===" in output
    assert "Formula     : T = (M1·Δ1 + M2·Δ2) / Δ" in output
    assert "Substitution: T = (48 + 40) / 32" in output
    assert "Intermediate: T = 88 / 32" in output
    assert "Final Result: T = 11/4 (2.75)" in output


def test_formatted_output_for_zero_determinant() -> None:
    paths = [{"id": "M1", "nodes": ["R", "X1", "C"], "gain": 3.0}]
    loops = [{"id": "L1", "nodes": ["X1", "X2", "X1"], "gain": 1.0}]
    res = solve_masons_gain(paths, loops)
    output = format_mason_solution(res)

    assert "Result      : Δ = 0" in output
    assert "ERROR — Undefined transfer function" in output
    assert "division by zero avoided" in output
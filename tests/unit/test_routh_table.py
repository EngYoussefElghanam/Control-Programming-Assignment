from fractions import Fraction

import pytest

from control_assignment.routh.algorithms.table import (
    RouthError, RouthSpecialCaseError, build_routh_table, validate_coefficients)


def test_assignment_example_table():
    t = build_routh_table([1, 1, 10, 72, 152, 240])
    assert t.row_labels == ["s^5", "s^4", "s^3", "s^2", "s^1", "s^0"]
    assert t.rows[0] == [1, 10, 152]
    assert t.rows[1] == [1, 72, 240]
    assert t.rows[2] == [-62, -88]
    assert t.rows[3][0] == Fraction(-62 * 72 + 88, -62)
    assert float(t.rows[3][0]) == pytest.approx(70.5806, abs=1e-4)
    assert t.rows[3][1] == 240
    assert float(t.rows[4][0]) == pytest.approx(122.823, abs=1e-3)
    assert t.rows[5] == [240]


def test_even_degree_shape():
    t = build_routh_table([1, 2, 3, 2, 1])  # (s^2+s+1)^2
    assert [len(r) for r in t.rows] == [3, 2, 2, 1, 1]
    assert t.first_column == [1, 2, 2, 1, 1]


def test_steps_contain_formula_and_substitution():
    t = build_routh_table([1, 1, 10, 72, 152, 240])
    first = t.steps[0]
    assert first.row_label == "s^3" and first.col == 1
    assert first.substitution == "(1*10 - 1*72) / 1"
    assert first.value == -62
    assert len(t.steps) == 6  # 2 + 2 + 1 + 1


def test_decimal_coefficients_are_exact():
    t = build_routh_table([1, "0.5", "0.25"])
    assert t.rows[2] == [Fraction(1, 4)]


def test_negative_all_same_sign_allowed():
    t = build_routh_table([-1, -3, -2])
    assert all(v < 0 for v in t.first_column)


@pytest.mark.parametrize("bad", [[1], [], [1, 0, 3], [1, -2, 3]])
def test_invalid_inputs(bad):
    with pytest.raises(RouthError):
        validate_coefficients(bad)


def test_invalid_text():
    with pytest.raises(RouthError):
        build_routh_table([1, "abc", 2])


def test_special_case_zero_first_column_rejected():
    # s^4 + s^3 + s^2 + s + 1 -> same-sign but gives a zero first-column entry
    with pytest.raises(RouthSpecialCaseError):
        build_routh_table([1, 1, 1, 1, 1])

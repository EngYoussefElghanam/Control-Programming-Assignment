import pytest

from control_assignment.routh.algorithms.poles import compute_poles, verify_against_routh


def test_unstable_poles():
    p = compute_poles([1, 1, 10, 72, 152, 240])
    assert p.rhp_count == 2
    assert sorted(round(z.real, 6) for z in p.rhp) == [2.0, 2.0]
    assert sorted(round(z.imag, 6) for z in p.rhp) == [-4.0, 4.0]
    assert len(p.lhp) == 3


def test_stable_poles():
    p = compute_poles([1, 15, 85, 225, 274, 120])
    assert p.rhp_count == 0
    assert [round(z.real) for z in p.poles] == [-1, -2, -3, -4, -5]


def test_repeated_roots_within_tolerance():
    p = compute_poles([1, 2, 3, 2, 1])  # (s^2+s+1)^2, repeated LHP roots
    assert p.rhp_count == 0


def test_axis_poles_not_counted_as_rhp():
    p = compute_poles([1, 0, 4])  # +-2j
    assert p.rhp_count == 0 and len(p.on_axis) == 2


def test_verification_agree_and_mismatch():
    p = compute_poles([1, 1, 10, 72, 152, 240])
    assert verify_against_routh(p, 2).agrees
    v = verify_against_routh(p, 1)
    assert not v.agrees and "MISMATCH" in v.message

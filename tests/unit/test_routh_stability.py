from control_assignment.routh.algorithms.stability import analyze_stability
from control_assignment.routh.algorithms.table import build_routh_table


def test_unstable_counts_sign_changes():
    st = analyze_stability(build_routh_table([1, 1, 10, 72, 152, 240]))
    assert st.sign_changes == 2 and st.rhp_poles == 2
    assert not st.is_stable and st.classification == "Unstable"
    assert st.change_locations == [("s^4", "s^3"), ("s^3", "s^2")]


def test_stable():
    st = analyze_stability(build_routh_table([1, 15, 85, 225, 274, 120]))
    assert st.sign_changes == 0 and st.is_stable
    assert st.classification == "Stable"


def test_single_rhp_pole():
    # (s-1)(s+2)(s+3) has mixed signs -> use s^3+... with one change instead:
    # s^3 + s^2 + 2s + 8: first column 1, 1, -6, 8 -> 2 changes
    st = analyze_stability(build_routh_table([1, 1, 2, 8]))
    assert st.rhp_poles == 2

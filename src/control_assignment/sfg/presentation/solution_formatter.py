"""Detailed step-by-step mathematical formatter for Mason's Gain Formula."""

from __future__ import annotations

from fractions import Fraction

from ..algorithms.determinant import DeterminantResult
from ..algorithms.mason import MasonResult


def format_number(value: float, frac: Fraction | None = None) -> str:
    """Format a number cleanly, showing exact simplified fraction when non-integer."""
    if frac is not None:
        if frac.denominator == 1:
            return str(frac.numerator)
        return f"{frac.numerator}/{frac.denominator} ({float(frac):.6g})"
    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    return f"{value:.6g}"


def _signed_term(value: float, frac: Fraction) -> str:
    text = format_number(value, frac)
    return f"({text})" if frac < 0 else text


def format_determinant_steps(det: DeterminantResult) -> str:
    """
    Format the original formula, symbolic terms, numerical substitution,
    intermediate sums, and final value for Δ or Δᵢ.
    """
    lines: list[str] = []
    lines.append(f"=== {det.label} Calculation ===")

    if det.excluded_loops:
        excluded_str = ", ".join(
            f"{lp.loop_id} (nodes: {' -> '.join(map(str, lp.nodes))})"
            for lp in det.excluded_loops
        )
        lines.append(f"Excluded touching loops: {excluded_str}")
    elif det.label != "Δ":
        lines.append("Excluded touching loops: None (no loops touch this forward path)")

    if not det.active_loops:
        lines.append(f"Formula: {det.label} = 1 (no active feedback loops)")
        lines.append(f"Result : {det.label} = 1")
        return "\n".join(lines)

    # 1. Symbolic expansion
    symbolic_parts = ["1"]
    for order in range(1, det.max_order + 1):
        combos = det.combinations_by_order[order]
        sign = "-" if order % 2 == 1 else "+"
        combo_exprs = ["".join(c.loop_ids) for c in combos]
        grouped = " + ".join(combo_exprs)
        symbolic_parts.append(f"{sign} ({grouped})")
    lines.append(f"Formula     : {det.label} = {' '.join(symbolic_parts)}")

    # 2. Detailed list of non-touching loop combinations
    for order in range(1, det.max_order + 1):
        combos = det.combinations_by_order[order]
        label = "Individual Loops" if order == 1 else f"{order} Non-Touching Loops"
        lines.append(f"  [{label}]")
        for combo in combos:
            ids = " · ".join(combo.loop_ids)
            vals = " × ".join(
                _signed_term(lp.gain, lp.gain_fraction) for lp in combo.loops
            )
            prod_str = format_number(combo.product, combo.product_fraction)
            if order == 1:
                lines.append(f"    {ids} = {prod_str}")
            else:
                lines.append(f"    {ids} = {vals} = {prod_str}")
        sum_str = format_number(
            det.order_sums[order], det.order_sums_fraction[order]
        )
        lines.append(f"    Sum(order {order}) = {sum_str}")

    # 3. Numerical substitution
    sub_parts = ["1"]
    for order in range(1, det.max_order + 1):
        sign = "-" if order % 2 == 1 else "+"
        s_val = _signed_term(
            det.order_sums[order], det.order_sums_fraction[order]
        )
        sub_parts.append(f"{sign} {s_val}")
    lines.append(f"Substitution: {det.label} = {' '.join(sub_parts)}")

    # 4. Final value
    final_str = format_number(det.value, det.value_fraction)
    lines.append(f"Result      : {det.label} = {final_str}")
    return "\n".join(lines)


def format_mason_solution(result: MasonResult) -> str:
    """Format the complete Mason's Gain Formula derivation from inputs to T(s)."""
    sections: list[str] = []

    # Section 1: Forward Paths & Loops summary
    header_lines = ["=== Forward Paths ==="]
    if not result.paths:
        header_lines.append("No forward paths found (numerator = 0).")
    for idx, p in enumerate(result.paths, start=1):
        nodes_str = " -> ".join(map(str, p.nodes))
        gain_str = format_number(p.gain, p.gain_fraction)
        branch_part = f" [{' × '.join(p.branches)}]" if p.branches else ""
        header_lines.append(
            f"  M{idx} ({p.path_id}): {nodes_str}{branch_part} = {gain_str}"
        )

    header_lines.append("\n=== Feedback Loops ===")
    if not result.loops:
        header_lines.append("No feedback loops found.")
    for lp in result.loops:
        nodes_str = " -> ".join(map(str, lp.nodes))
        gain_str = format_number(lp.gain, lp.gain_fraction)
        branch_part = f" [{' × '.join(lp.branches)}]" if lp.branches else ""
        header_lines.append(
            f"  {lp.loop_id}: {nodes_str}{branch_part} = {gain_str}"
        )
    sections.append("\n".join(header_lines))

    # Section 2: Graph Determinant Δ
    sections.append(format_determinant_steps(result.determinant))

    # Section 3: Path Cofactors Δᵢ and Products Mᵢ·Δᵢ
    for term in result.path_terms:
        sections.append(format_determinant_steps(term.cofactor))
        m_str = _signed_term(term.path.gain, term.path.gain_fraction)
        d_str = _signed_term(
            term.cofactor.value, term.cofactor.value_fraction
        )
        p_str = format_number(term.product, term.product_fraction)
        sections.append(
            f"Product M{term.index} · Δ{term.index} = {m_str} × {d_str} = {p_str}"
        )

    # Section 4: Mason's Gain Formula Final Assembly
    final_lines = ["=== Mason's Gain Formula ==="]
    if not result.path_terms:
        final_lines.append("Formula: T = Σ(Mᵢ · Δᵢ) / Δ")
        if result.is_singular:
            final_lines.append(f"Result : ERROR — {result.error_message}")
        else:
            final_lines.append("Result : T = 0 (no forward paths from input to output)")
        sections.append("\n".join(final_lines))
        return "\n\n".join(sections)

    sym_terms = " + ".join(f"M{t.index}·Δ{t.index}" for t in result.path_terms)
    final_lines.append(f"Formula     : T = ({sym_terms}) / Δ")

    num_terms = " + ".join(
        _signed_term(t.product, t.product_fraction) for t in result.path_terms
    )
    delta_str = _signed_term(
        result.determinant.value, result.determinant.value_fraction
    )
    final_lines.append(f"Substitution: T = ({num_terms}) / {delta_str}")

    num_sum_str = format_number(result.numerator, result.numerator_fraction)
    delta_clean = format_number(
        result.determinant.value, result.determinant.value_fraction
    )
    final_lines.append(f"Intermediate: T = {num_sum_str} / {delta_clean}")

    if result.is_singular:
        final_lines.append(f"Result      : ERROR — {result.error_message}")
    else:
        assert result.transfer_gain is not None
        assert result.transfer_gain_fraction is not None
        simplified = format_number(
            result.transfer_gain, result.transfer_gain_fraction
        )
        final_lines.append(f"Final Result: T = {simplified}")

    sections.append("\n".join(final_lines))
    return "\n\n".join(sections)
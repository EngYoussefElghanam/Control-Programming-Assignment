"""Text / HTML formatting of the Routh solution, for the GUI and the report."""
from __future__ import annotations

import html
import re

from ..algorithms.poles import PolesResult, Verification
from ..algorithms.stability import StabilityResult
from ..algorithms.table import RouthTable, fmt


def format_equation(table: RouthTable) -> str:
    n = table.degree
    terms = []
    for i, c in enumerate(table.coefficients):
        p = n - i
        cs = fmt(c)
        if p == 0:
            terms.append(cs)
        else:
            head = "" if cs == "1" else cs
            terms.append(f"{head}s" + (f"^{p}" if p > 1 else ""))
    return " + ".join(terms) + " = 0"


def format_complex(z: complex) -> str:
    if z.imag == 0:
        return f"{z.real:.6g}"
    sign = "+" if z.imag > 0 else "-"
    return f"{z.real:.6g} {sign} {abs(z.imag):.6g}j"


def _loc(z: complex) -> str:
    return "RHP" if z.real > 0 else ("imaginary axis" if z.real == 0 else "LHP")


def format_table(table: RouthTable) -> str:
    ncols = max(len(r) for r in table.rows)
    cells = [[fmt(v) for v in r] + [""] * (ncols - len(r)) for r in table.rows]
    w = max(6, max(len(c) for r in cells for c in r))
    return "\n".join(
        f"{lab:>4} | " + "  ".join(f"{c:>{w}}" for c in r)
        for lab, r in zip(table.row_labels, cells)
    )


def format_steps(table: RouthTable) -> str:
    lines = ["First two rows come from the coefficients (alternating).",
             "Every other element = (a*d - b*c) / a, where a, b = first elements of the",
             "previous row and of the row two above; c, d = the next elements to their right.", ""]
    for s in table.steps:
        head = f"{s.row_label}[{s.col}] "
        lines.append(f"{head}= {s.formula}")
        lines.append(f"{'':>{len(head)}}= {s.substitution} = {fmt(s.value)}")
    return "\n".join(lines)


def format_stability(st: StabilityResult) -> str:
    col = ", ".join(f"{l}: {fmt(v)}" for l, v in zip(st.row_labels, st.first_column))
    signs = " ".join("+" if s > 0 else "-" for s in st.signs)
    return (f"First column -> {col}\nSigns -> {signs}\n"
            f"Sign changes = {st.sign_changes}\nRHP poles (Routh) = {st.rhp_poles}\n"
            f"Classification: {st.classification.upper()}\n{st.explanation}")


def format_poles(p: PolesResult, v: Verification) -> str:
    lines = [f"Poles (numpy.roots), tolerance {p.tolerance:g}:"]
    for i, z in enumerate(p.poles, 1):
        lines.append(f"  p{i} = {format_complex(z)}   [{_loc(z)}]")
    lines.append(f"Numerical RHP poles = {p.rhp_count}")
    lines.append(v.message)
    return "\n".join(lines)


def format_full_report(table, st, poles, ver) -> str:
    bar = "=" * 60
    sub = "-" * 60
    return "\n".join([
        bar, "ROUTH STABILITY CRITERION", bar,
        f"Characteristic equation: {format_equation(table)}", "",
        "1) Routh table", sub, format_table(table), "",
        "2) Calculation steps", sub, format_steps(table), "",
        "3) Stability analysis", sub, format_stability(st), "",
        "4) Numerical pole verification", sub, format_poles(poles, ver),
    ])


# ---------------------------------------------------------------- HTML
def _sup(text: str) -> str:
    return re.sub(r"s\^(\d+)", r"s<sup>\1</sup>", html.escape(text))


def format_html(table, st, poles, ver) -> str:
    e = html.escape
    ncols = max(len(r) for r in table.rows)
    rows_html = []
    for lab, r in zip(table.row_labels, table.rows):
        tds = "".join(f"<td align='right'>{e(fmt(v))}</td>" for v in r) + "<td></td>" * (ncols - len(r))
        rows_html.append(f"<tr><th>{_sup(lab)}</th>{tds}</tr>")
    steps_html = "".join(
        f"<li><b>{_sup(s.row_label)}[{s.col}]</b> = {_sup(s.formula)}<br>"
        f"&nbsp;&nbsp;= {e(s.substitution)} = <b>{e(fmt(s.value))}</b></li>"
        for s in table.steps)
    colr = "#1b8a3a" if st.is_stable else "#c0392b"
    poles_html = "".join(
        f"<li>p{i} = {e(format_complex(z))} <i>({_loc(z)})</i></li>"
        for i, z in enumerate(poles.poles, 1))
    vcol = "#1b8a3a" if ver.agrees else "#c0392b"
    return f"""
<h3>Characteristic equation</h3><p>{_sup(format_equation(table))}</p>
<h3>Routh table</h3>
<table border="1" cellspacing="0" cellpadding="6">{''.join(rows_html)}</table>
<h3>Calculation steps</h3>
<p>Element = (a&middot;d &minus; b&middot;c) / a, with a, b the first elements of the previous row
and of the row two above, and c, d the next elements to their right.</p>
<ol>{steps_html}</ol>
<h3>Stability</h3>
<p>Sign changes in the first column: <b>{st.sign_changes}</b><br>
RHP poles (Routh): <b>{st.rhp_poles}</b><br>
Result: <b style="color:{colr}">{st.classification.upper()}</b></p><p>{e(st.explanation)}</p>
<h3>Numerical poles</h3><ul>{poles_html}</ul>
<p>Numerical RHP poles: <b>{poles.rhp_count}</b></p>
<p style="color:{vcol}"><b>{e(ver.message)}</b></p>
"""

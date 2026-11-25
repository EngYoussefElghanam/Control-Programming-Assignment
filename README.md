# Control Assignment: Signal Flow Graphs and Routh Stability

CSE 341 (Fundamentals of Control Systems), Alexandria University, Faculty of Engineering, Computer and Systems Engineering Department.

A desktop app with two tools:

- a **Signal Flow Graph solver** that uses Mason's gain formula, and
- a **Routh stability checker** that also finds the poles with NumPy.

Both tools show every formula, every step, the numbers put into each formula, and the final answer.

## Contents

- [How to run](#how-to-run)
- [How to use it](#how-to-use-it)
- [Example results](#example-results)
- [Graph file format (JSON)](#graph-file-format-json)
- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Running the tests](#running-the-tests)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)
- [Built with](#built-with)
- [Team](#team)

## How to run

You need **Python 3.10 or newer**.

1. **Get the code**

   ```bash
   git clone https://github.com/EngYoussefElghanam/Control-Programming-Assignment
   cd Control-Programming-Assignment
   ```

2. **(Optional) Make a virtual environment**

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. **Install the libraries** (PySide6 and NumPy)

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the program** (run it from the `src` folder)

   ```bash
   cd src
   python -m control_assignment
   ```

A window called **Control Assignment** opens with two tabs: *Signal Flow Graph* and *Routh Stability*.

> On macOS / Linux you may need to type `python3` instead of `python`.

## How to use it

### Part 1: Signal Flow Graph

1. Add your nodes (for example `R`, `X1`, `X2`, `C`) with **Add node**. Names must be different.
2. Add branches: choose *from* and *to*, type the gain (`2`, `-0.5`, or `-1/3`), then press **Add branch**. A gain cannot be 0. A branch from a node to itself is allowed (a self-loop).
3. Choose the **input node** and the **output node**, then press **Solve**.
4. Or press **Load sample / JSON graph...** and pick one of the ready examples:
   - `tests/fixtures/sfg_case_1.json` (8 forward paths, 5 loops)
   - `tests/fixtures/sfg_case_2.json` (2 forward paths, 5 loops)

You then get three pages:

| Page | What you see |
| --- | --- |
| 1 · Input | Your nodes and branches |
| 2 · Graph | The drawn graph. Zoom with + / −, drag to move, press "Fit graph" to see everything. |
| 3 · Calculations | The final T, then five small tabs (see below) |

The five tabs on the Calculations page:

| Tab | What it shows |
| --- | --- |
| Forward paths | Each path and its gain as a product, like `M1 = G1 × G2 × G3 = 6` |
| Loops | Each loop and its gain as a product |
| Non-touching | Groups of 2, 3, or more loops that do not touch, with their products |
| Δ, Δᵢ & Mason | The full step-by-step calculation of Δ, each Δᵢ, each MᵢΔᵢ, and the final T |
| Branch gains | The list of all your branches |

Press **Copy all calculations** to copy everything as text.

### Part 2: Routh Stability

1. Type the coefficients, highest power first. For `s^5 + s^4 + 10s^3 + 72s^2 + 152s + 240` type: `1 1 10 72 152 240`.
2. Press **Check stability** (or Enter).
3. You get:
   - the Routh table (rows `s^n` down to `s^0`),
   - **STABLE** or **UNSTABLE**, with the number of sign changes,
   - all poles calculated with NumPy,
   - a check that the NumPy right-half-plane count agrees with Routh,
   - the formula and numbers used for every table element.

You can also run Part 2 in the terminal (from the `src` folder):

```bash
python -m control_assignment.routh.controller 1 1 10 72 152 240
```

**Input rules for Part 2:** every coefficient from `s^0` to `s^n` must be there (no zeros) and all must have the same sign. Special cases (a zero in the first column or a row of zeros) are not supported, and the program shows a message.

## Example results

These are the results of the ready examples, so you can check that the program works.

### Signal flow graphs

| Example | Forward paths | Loops | Δ | T |
| --- | --- | --- | --- | --- |
| `sfg_case_1.json` | 8 | 5 | 69/5 (13.8) | 455/23 (19.7826) |
| `sfg_case_2.json` | 2 | 5 | 116/3 (38.6667) | 66/29 (2.27586) |

### Routh stability

| Example | Equation | Sign changes | Result | Poles |
| --- | --- | --- | --- | --- |
| `routh_stable.json` | s⁵ + 15s⁴ + 85s³ + 225s² + 274s + 120 = 0 | 0 | Stable | −1, −2, −3, −4, −5 |
| `routh_unstable.json` | s⁵ + s⁴ + 10s³ + 72s² + 152s + 240 = 0 | 2 | Unstable (2 RHP poles) | 2 ± 4j, −1 ± 1.73205j, −3 |

Routh table of the unstable example:

| Row | Column 1 | Column 2 | Column 3 |
| --- | --- | --- | --- |
| s⁵ | 1 | 10 | 152 |
| s⁴ | 1 | 72 | 240 |
| s³ | −62 | −88 | |
| s² | 70.5806 | 240 | |
| s¹ | 122.823 | | |
| s⁰ | 240 | | |

## Graph file format (JSON)

A graph file is plain JSON. You can make your own and load it with **Load sample / JSON graph...**.

```json
{
  "input_node": "R",
  "output_node": "C",
  "nodes": ["R", "X1", "C"],
  "branches": [
    { "from": "R",  "to": "X1", "gain": 2,  "label": "G1" },
    { "from": "X1", "to": "C",  "gain": 3,  "label": "G2" },
    { "from": "X1", "to": "R",  "gain": -1, "label": "H1" }
  ]
}
```

- `nodes` is the list of node names (strings).
- Each branch needs `from`, `to`, and `gain`. `label` is optional (a name like `b1` is used if it is missing). Labels must be different from each other.
- `input_node` and `output_node` are optional. If they are missing, the program uses `R` and `C` when those nodes exist, or the first and last node.
- Gains cannot be 0.

## What it does

**Part 1: Signal Flow Graph**
- Draws the signal flow graph with nodes, arrows, and gains
- Finds all forward paths (M1, M2, ...) and all loops (L1, L2, ...)
- Finds all groups of non-touching loops
- Calculates Δ and each Δᵢ, showing every term
- Applies Mason's formula and gives T as a fraction and a decimal
- Uses exact fractions, so there are no rounding errors
- Says "undefined" if Δ = 0 instead of crashing

**Part 2: Routh Stability**
- Builds the full Routh table with the formula and numbers for each element
- Counts sign changes in the first column to decide stable or unstable
- Finds all poles numerically and checks the right-half-plane count against Routh

## How it works

### Signal flow graph formulas

- **Δ = 1 − (sum of loop gains) + (sum of products of 2 non-touching loops) − (sum of products of 3 non-touching loops) + ...**
- **Δᵢ** is Δ calculated again after removing every loop that touches forward path i. If no loop is left, Δᵢ = 1.
- **T = (M₁Δ₁ + M₂Δ₂ + ... + MₘΔₘ) / Δ**

Two loops "touch" if they share at least one node.

### Routh table

The first two rows are the coefficients, taken one by one in turn. Every other element is:

```
element = (a·d − b·c) / a
```

where `a` and `b` are the first numbers of the row just above and of the row above that, and `c` and `d` are the numbers to their right. A missing number counts as 0.

Each sign change in the first column is one pole in the right half plane. No sign change means the system is stable.

### Main algorithms

| Job | Method |
| --- | --- |
| Forward paths | Depth-first search with backtracking, never using a node twice in one path |
| Loops | Depth-first search that counts each loop only once, from its first node |
| Non-touching loops | Backtracking with a table of which loops touch |
| Δ, Δᵢ, T | Exact fraction arithmetic (Python `Fraction`) |
| Poles | `numpy.roots`, tiny values (under 1e-6) treated as zero |

## Project structure

```
src/control_assignment/
  app.py, __main__.py       starts the program
  ui/main_window.py         the window with the two tabs
  common/                   small shared helpers
  sfg/                      Part 1
    ui/                     input screen, graph drawing, results screen
    algorithms/             paths and loops, non-touching loops, Δ, Mason
    controller.py           connects the screen to the maths
    presentation/           writes the step-by-step text
  routh/                    Part 2
    ui/                     input screen and results screen
    algorithms/             Routh table, stability, poles
    controller.py           connects the screen to the maths
    presentation/           writes the step-by-step text
tests/
  unit/                     tests for each algorithm
  integration/              tests for the full pipeline and the GUI
  fixtures/                 the ready example graphs and equations (JSON)
docs/                       report, user guide, demo plan
scripts/capture_sfg.py      helper to capture screenshots of the SFG results
```

## Running the tests

From the project folder:

```bash
pip install -r requirements-dev.txt
pytest
```

The tests check the paths, loops, non-touching groups, Δ, Mason's formula, the Routh table, the stability result, the poles, the input checks, and that the GUI starts and connects correctly.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| `No module named control_assignment` | You are not in the `src` folder. Run `cd src` first, then `python -m control_assignment`. |
| `No module named PySide6` or `numpy` | Run `pip install -r requirements.txt` again. Make sure the virtual environment is active. |
| `python` is not found | Try `python3`, or install Python 3.10 or newer. |
| On Linux: Qt "platform plugin" error | Install the system Qt libraries (for example `libxcb-cursor0` on Ubuntu) and try again. |
| "Cannot solve graph" message | Check that the input and output nodes are different, that every branch uses existing nodes, and that no gain is 0. |
| Routh error about zero or mixed signs | Use only non-zero coefficients with the same sign. Special cases are not supported. |

## Limits

- Part 1 uses only numerical gains (no symbols like `s` or `G(s)`).
- A gain of 0 is not allowed.
- Part 2 does not handle the special cases (a zero in the first column or a row of all zeros).
- The graph is drawn automatically. You cannot move the nodes by hand.

## Built with

Python 3, [PySide6](https://doc.qt.io/qtforpython-6/) (Qt GUI), [NumPy](https://numpy.org/) (poles).

## Team

| # | Name | University ID |
| --- | --- | --- |
| 1 | Abdullah Ahmed Mohamed Mohamed | 24010411 |
| 2 | Adham Bhaaeldin Mohamed Mohamed | 24010092 |
| 3 | Moaz Gaballah Ahmed Mohamed | 24010732 |
| 4 | Mohamed Mahmoad Mohamed Ismail | 24010650 |
| 5 | Youssef Diaa Abelmohsen Mahmoad | 24010851 |
| 6 | Youssef Mohamed Mahmoad Abelhamed | 24010876 |

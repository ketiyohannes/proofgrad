"""Spec for orangesRotting: minutes until no fresh orange remains, or -1 if some never rot.

Domain: rectangular grids with 1..6 rows and columns (statement allows up to 10) whose
cells are 0, 1 or 2. The oracle simulates the process minute by minute, as defined.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "orangesRotting"

CLARIFICATIONS = ["If there are no fresh oranges at the start, return 0."]


def simulate(grid):
    g = [row[:] for row in grid]
    rows, cols = len(g), len(g[0])
    minutes = 0
    while True:
        if not any(1 in row for row in g):
            return minutes
        to_rot = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if g[r][c] == 1
            and any(
                0 <= r + dr < rows and 0 <= c + dc < cols and g[r + dr][c + dc] == 2
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
        ]
        if not to_rot:
            return -1
        for r, c in to_rot:
            g[r][c] = 2
        minutes += 1


@st.composite
def grids(draw, values=(0, 1, 2), max_side=6):
    rows = draw(st.integers(min_value=1, max_value=max_side))
    cols = draw(st.integers(min_value=1, max_value=max_side))
    weights = draw(st.sampled_from([(0, 1, 2), (1, 1, 2), (0, 1, 1, 1, 2), (1, 1, 1, 1, 1, 2), (0, 2), (1,), (0, 0, 1, 2)]))
    pool = [v for v in weights if v in values] or list(values)
    return [[draw(st.sampled_from(pool)) for _ in range(cols)] for _ in range(rows)]


@prop("The result equals the number of minutes of the rotting process, or -1 if some fresh orange never rots.", grid=grids())
def matches_simulation(f, grid):
    assert f(grid) == simulate(grid)


@prop("Grids with no fresh orange give 0.", grid=grids(values=(0, 2)))
def no_fresh_gives_zero(f, grid):
    assert f(grid) == 0


@prop("Grids with fresh oranges but no rotten orange give -1.", grid=grids(values=(0, 1)))
def no_rotten_gives_minus_one(f, grid):
    if any(1 in row for row in grid):
        assert f(grid) == -1
    else:
        assert f(grid) == 0


@prop("A single row of fresh oranges with one rotten end takes (length - 1) minutes.", n=st.integers(min_value=1, max_value=10),
      left=st.booleans())
def single_row_chain(f, n, left):
    row = [2] + [1] * (n - 1) if left else [1] * (n - 1) + [2]
    assert f([row]) == n - 1


@prop("Transposing or mirroring the grid does not change the answer.", grid=grids(),
      kind=st.sampled_from(["transpose", "flip_rows", "flip_cols"]))
def symmetry_invariant(f, grid, kind):
    if kind == "transpose":
        other = [list(col) for col in zip(*grid)]
    elif kind == "flip_rows":
        other = grid[::-1]
    else:
        other = [row[::-1] for row in grid]
    assert f(other) == f(grid)

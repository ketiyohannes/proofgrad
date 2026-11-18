"""Spec for orangesRotting: minutes until no fresh orange remains, or -1 if some never rot.

Domain: grid is a non-empty rectangular list of lists with values in {0, 1, 2}.
Each minute every fresh orange 4-adjacent to a rotten one becomes rotten (simultaneously).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "orangesRotting"

CLARIFICATIONS = [
    "Return 0 if there are no fresh oranges at the start (including a grid with no oranges at all).",
]


@st.composite
def grids(draw, max_side=6, values=(0, 1, 2)):
    rows = draw(st.integers(min_value=1, max_value=max_side))
    cols = draw(st.integers(min_value=1, max_value=max_side))
    pools = [list(values), [v for v in values if v != 0] or list(values)]
    if 1 in values:
        pools.append(list(values) + [1, 1, 1])  # mostly fresh oranges
    cell = st.sampled_from(draw(st.sampled_from(pools)))
    return [draw(st.lists(cell, min_size=cols, max_size=cols)) for _ in range(rows)]


def simulate(grid):
    g = [row[:] for row in grid]
    rows, cols = len(g), len(g[0])
    minutes = 0
    while True:
        fresh = [(r, c) for r in range(rows) for c in range(cols) if g[r][c] == 1]
        if not fresh:
            return minutes
        newly = [(r, c) for r, c in fresh
                 if any(0 <= r + dr < rows and 0 <= c + dc < cols and g[r + dr][c + dc] == 2
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if not newly:
            return -1
        for r, c in newly:
            g[r][c] = 2
        minutes += 1


@prop("The result equals the number of simultaneous rotting minutes, or -1 if some fresh orange never rots.",
      grid=grids())
def matches_simulation(f, grid):
    assert f(grid) == simulate(grid)


@prop("A grid with no fresh oranges needs 0 minutes.", grid=grids(values=(0, 2)))
def no_fresh_is_zero(f, grid):
    assert f(grid) == 0


@prop("Fresh oranges with no rotten orange anywhere give -1.", grid=grids(values=(0, 1)))
def no_rotten_is_impossible(f, grid):
    if any(1 in row for row in grid):
        assert f(grid) == -1


@prop("In a single row starting with a rotten orange followed by k fresh ones, the answer is k.",
      k=st.integers(min_value=0, max_value=20), vertical=st.booleans())
def chain_takes_k_minutes(f, k, vertical):
    row = [2] + [1] * k
    grid = [[v] for v in row] if vertical else [row]
    assert f(grid) == k


@prop("A fresh orange walled off by empty cells makes the answer -1.", grid=grids(max_side=4))
def isolated_fresh_impossible(f, grid):
    cols = len(grid[0])
    # The new last column holds a fresh orange whose only neighbours are an empty column and other fresh cells.
    padded = [row[:cols] + [0, 1] for row in grid]
    assert f(padded) == -1


@prop("The result is an int that is -1 or non-negative.", grid=grids())
def result_type(f, grid):
    r = f(grid)
    assert isinstance(r, int) and r >= -1

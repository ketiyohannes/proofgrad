"""Spec for min_path_sum: minimum total cost of a right/down path from the top-left to the bottom-right cell.

Domain: non-empty rectangular grids of non-negative integers (both endpoint cells are counted),
plus the empty grid [] exercised by the unit tests.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_path_sum"

CLARIFICATIONS = [
    "The path cost includes both the starting and the ending cell.",
    "Return 0 for an empty grid.",
]


@st.composite
def grids(draw, max_side=5):
    m = draw(st.integers(min_value=1, max_value=max_side))
    n = draw(st.integers(min_value=1, max_value=max_side))
    hi = draw(st.sampled_from([1, 9, 1000]))
    return [draw(st.lists(st.integers(min_value=0, max_value=hi), min_size=n, max_size=n)) for _ in range(m)]


def all_path_sums(grid, i=0, j=0):
    m, n = len(grid), len(grid[0])
    here = grid[i][j]
    if i == m - 1 and j == n - 1:
        return [here]
    out = []
    if i + 1 < m:
        out += [here + s for s in all_path_sums(grid, i + 1, j)]
    if j + 1 < n:
        out += [here + s for s in all_path_sums(grid, i, j + 1)]
    return out


@prop("The result is an int equal to the minimum over all right/down paths of the summed cell costs.", g=grids())
def matches_brute_force(f, g):
    r = f(g)
    assert isinstance(r, int)
    assert r == min(all_path_sums(g))


@prop("A single row or a single column has only one path: the sum of all cells.",
      cells=st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=10), column=st.booleans())
def single_line(f, cells, column):
    g = [[c] for c in cells] if column else [cells]
    assert f(g) == sum(cells)


@prop("Transposing the grid does not change the minimum path sum.", g=grids())
def transpose_invariant(f, g):
    t = [list(col) for col in zip(*g)]
    assert f(g) == f(t)


@prop("The result is at least the two corner cells combined and at most the cost of any one path (e.g. right-then-down).", g=grids())
def bounds(f, g):
    r = f(g)
    corners = g[0][0] + (g[-1][-1] if len(g) * len(g[0]) > 1 else 0)
    right_then_down = sum(g[0]) + sum(row[-1] for row in g[1:])
    assert corners <= r <= right_then_down


@prop("A 1x1 grid returns its cell and an empty grid returns 0.", v=st.integers(min_value=0, max_value=10**6))
def degenerate(f, v):
    assert f([[v]]) == v
    assert f([]) == 0

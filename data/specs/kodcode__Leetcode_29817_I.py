"""Spec for num_islands: number of 4-connected components of '1' cells in a grid of '0'/'1' strings.

Domain: rectangular grids of the single-character strings '0' and '1' with at least one row and
column, plus the empty grid [] exercised by the unit tests.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "num_islands"

CLARIFICATIONS = [
    "Cells are the strings '1' and '0'. Return 0 for an empty grid.",
    "Diagonally adjacent cells are not connected.",
]


@st.composite
def grids(draw, max_side=7):
    m = draw(st.integers(min_value=1, max_value=max_side))
    n = draw(st.integers(min_value=1, max_value=max_side))
    p = draw(st.sampled_from([0.0, 0.3, 0.5, 0.7, 1.0]))
    return [[("1" if draw(st.floats(min_value=0, max_value=1, exclude_max=True)) < p else "0") for _ in range(n)] for _ in range(m)]


def count_components(grid):
    m, n = len(grid), len(grid[0]) if grid else 0
    parent = {(i, j): (i, j) for i in range(m) for j in range(n) if grid[i][j] == "1"}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for (i, j) in list(parent):
        for (a, b) in ((i + 1, j), (i, j + 1)):
            if (a, b) in parent:
                parent[find((a, b))] = find((i, j))
    return len({find(c) for c in parent})


@prop("The result is an int equal to the number of 4-connected groups of '1' cells.", g=grids())
def matches_components(f, g):
    r = f(g)
    assert isinstance(r, int)
    assert r == count_components(g)


@prop("Transposing or mirroring the grid does not change the island count.", g=grids())
def symmetry_invariant(f, g):
    base = f(g)
    assert f([list(col) for col in zip(*g)]) == base
    assert f([row[::-1] for row in g]) == base
    assert f(g[::-1]) == base


@prop("A checkerboard of '1' cells has one island per '1' (diagonals do not connect).",
      m=st.integers(min_value=1, max_value=7), n=st.integers(min_value=1, max_value=7), parity=st.integers(min_value=0, max_value=1))
def checkerboard(f, m, n, parity):
    g = [["1" if (i + j) % 2 == parity else "0" for j in range(n)] for i in range(m)]
    assert f(g) == sum(row.count("1") for row in g)


@prop("An all-'1' grid is one island and an all-'0' grid has none.",
      m=st.integers(min_value=1, max_value=8), n=st.integers(min_value=1, max_value=8))
def uniform_grids(f, m, n):
    assert f([["1"] * n for _ in range(m)]) == 1
    assert f([["0"] * n for _ in range(m)]) == 0


@prop("Separating rows of land with a row of water adds their island counts.", a=grids(), b=grids())
def disjoint_union(f, a, b):
    n = max(len(a[0]), len(b[0]))
    pad = lambda g: [row + ["0"] * (n - len(row)) for row in g]
    combined = pad(a) + [["0"] * n] + pad(b)
    assert f(combined) == f(a) + f(b)


@prop("An empty grid has 0 islands.", dummy=st.just(None))
def empty_grid(f, dummy):
    assert f([]) == 0

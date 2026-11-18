"""Spec for num_islands: the number of 4-directionally connected components of '1' cells.

Domain: rectangular grids of '1'/'0' strings with 1..7 rows and 1..7 columns, plus the empty grid [].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "num_islands"

CLARIFICATIONS = [
    "Return an int; an empty grid ([]) has 0 islands.",
]


@st.composite
def grids(draw):
    n = draw(st.integers(1, 7))
    m = draw(st.integers(1, 7))
    density = draw(st.sampled_from([0.0, 0.3, 0.5, 0.7, 1.0]))
    cells = draw(st.lists(st.floats(0, 1), min_size=n * m, max_size=n * m))
    return [["1" if cells[i * m + j] < density else "0" for j in range(m)] for i in range(n)]


def count_components(g):
    n, m = len(g), len(g[0])
    label = {}
    for i in range(n):
        for j in range(m):
            if g[i][j] == "1":
                label[(i, j)] = (i, j)
    changed = True
    while changed:
        changed = False
        for (i, j) in list(label):
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (i + di, j + dj)
                if q in label and label[q] < label[(i, j)]:
                    label[(i, j)] = label[q]
                    changed = True
    return len(set(label.values()))


@prop("The result is an int equal to the number of 4-connected groups of land cells.", g=grids())
def matches_definition(f, g):
    r = f(g)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == count_components(g)


@prop("A grid with no land has 0 islands.", n=st.integers(1, 8), m=st.integers(1, 8))
def all_water(f, n, m):
    assert f([["0"] * m for _ in range(n)]) == 0


@prop("A grid made entirely of land is one island.", n=st.integers(1, 8), m=st.integers(1, 8))
def all_land(f, n, m):
    assert f([["1"] * m for _ in range(n)]) == 1


@prop("Diagonally touching land cells form separate islands (checkerboard).", n=st.integers(1, 7), m=st.integers(1, 7))
def checkerboard(f, n, m):
    g = [["1" if (i + j) % 2 == 0 else "0" for j in range(m)] for i in range(n)]
    assert f(g) == sum(1 for i in range(n) for j in range(m) if (i + j) % 2 == 0)


@prop("Transposing or mirroring the grid does not change the count.", g=grids())
def symmetry_invariant(f, g):
    base = f(g)
    assert f([list(col) for col in zip(*g)]) == base
    assert f([row[::-1] for row in g]) == base
    assert f(g[::-1]) == base


@prop("The empty grid has 0 islands.", dummy=st.just(None))
def empty_grid(f, dummy):
    assert f([]) == 0

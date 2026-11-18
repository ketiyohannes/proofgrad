"""Spec for num_distinct_regions: number of 4-connected components of '1' cells in a grid of '0'/'1' characters.

Domain: rectangular lists of lists of the single-character strings '0' and '1'; [] and [[]] are allowed (answer 0).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "num_distinct_regions"

CLARIFICATIONS = ["The grid is a list of rows of '0'/'1' strings; an empty grid ([] or [[]]) has 0 regions. Return an int."]


@st.composite
def grids(draw, max_side=7):
    m = draw(st.integers(1, max_side))
    n = draw(st.integers(1, max_side))
    p = draw(st.sampled_from([0.2, 0.5, 0.8]))
    cells = draw(st.lists(st.floats(0, 1), min_size=m * n, max_size=m * n))
    return [["1" if cells[i * n + j] < p else "0" for j in range(n)] for i in range(m)]


def count_components(grid):
    """Union-find over '1' cells, joining right and down neighbours."""
    if not grid or not grid[0]:
        return 0
    m, n = len(grid), len(grid[0])
    parent = {(i, j): (i, j) for i in range(m) for j in range(n) if grid[i][j] == "1"}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for (i, j) in list(parent):
        for nb in ((i + 1, j), (i, j + 1)):
            if nb in parent:
                parent[find(nb)] = find((i, j))
    return len({find(c) for c in parent})


@prop("The count equals the number of 4-connected groups of '1' cells (diagonal neighbours are not connected).", grid=grids())
def matches_component_count(f, grid):
    assert f(grid) == count_components(grid)


@prop("Transposing or mirroring the grid does not change the count.", grid=grids())
def symmetry_invariant(f, grid):
    r = f(grid)
    assert isinstance(r, int)
    assert f([list(col) for col in zip(*grid)]) == r
    assert f([row[::-1] for row in grid]) == r


@prop("A checkerboard of '1's (only diagonal contacts) has one region per '1' cell.", m=st.integers(1, 7), n=st.integers(1, 7), parity=st.integers(0, 1))
def checkerboard(f, m, n, parity):
    grid = [["1" if (i + j) % 2 == parity else "0" for j in range(n)] for i in range(m)]
    assert f(grid) == sum(row.count("1") for row in grid)


@prop("An all-'0' grid has 0 regions and an all-'1' grid has 1.", m=st.integers(1, 8), n=st.integers(1, 8))
def uniform_grids(f, m, n):
    assert f([["0"] * n for _ in range(m)]) == 0
    assert f([["1"] * n for _ in range(m)]) == 1


@prop("Empty grids [] and [[]] have 0 regions.", dummy=st.just(None))
def empty_grids(f, dummy):
    assert f([]) == 0
    assert f([[]]) == 0

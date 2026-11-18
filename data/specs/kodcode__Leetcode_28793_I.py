"""Spec for max_vegetables_harvested: largest total obtainable by harvesting at most k cells.

Domain: non-empty rectangular grids of positive integers; k >= 0 (possibly larger than the
number of cells). Each step harvests one whole cell, and a cell can be harvested only once.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_vegetables_harvested"

CLARIFICATIONS = [
    "Each step harvests the entire amount of one cell, and each cell can be harvested at most once.",
    "If k exceeds the number of cells, every cell is harvested; k = 0 gives 0.",
]


@st.composite
def grids(draw, max_side=4, max_val=20):
    m = draw(st.integers(min_value=1, max_value=max_side))
    n = draw(st.integers(min_value=1, max_value=max_side))
    shape = draw(st.sampled_from(["random", "small", "equal"]))
    if shape == "equal":
        v = draw(st.integers(min_value=1, max_value=max_val))
        return [[v] * n for _ in range(m)]
    hi = 3 if shape == "small" else max_val
    return [draw(st.lists(st.integers(min_value=1, max_value=hi), min_size=n, max_size=n)) for _ in range(m)]


@st.composite
def grid_and_k(draw):
    g = draw(grids(max_side=3))
    cells = len(g) * len(g[0])
    k = draw(st.one_of(st.integers(min_value=0, max_value=cells), st.integers(min_value=0, max_value=cells + 5)))
    return g, k


def best(grid, k):
    cells = [v for row in grid for v in row]
    k = min(k, len(cells))
    return max(sum(c) for c in combinations(cells, k))


@prop("The result is an int equal to the best total over every choice of at most k distinct cells.", case=grid_and_k())
def matches_brute_force(f, case):
    g, k = case
    r = f(g, k)
    assert isinstance(r, int)
    assert r == best(g, k)


@prop("With k at least the number of cells, the whole garden is harvested.",
      g=grids(), extra=st.integers(min_value=0, max_value=10))
def harvest_everything(f, g, extra):
    k = len(g) * len(g[0]) + extra
    assert f(g, k) == sum(map(sum, g))


@prop("Harvesting k = 0 cells gives 0, and k = 1 gives the largest cell.", g=grids())
def zero_and_one(f, g):
    assert f(g, 0) == 0
    assert f(g, 1) == max(map(max, g))


@prop("One more step never lowers the total, and adds at most the largest cell.", case=grid_and_k())
def monotone_in_k(f, case):
    g, k = case
    a, b = f(g, k), f(g, k + 1)
    assert a <= b <= a + max(map(max, g))


@prop("Rearranging the grid's shape (same cells as one row or one column) does not change the result.", case=grid_and_k())
def shape_invariant(f, case):
    g, k = case
    flat = [v for row in g for v in row]
    assert f([flat], k) == f(g, k) == f([[v] for v in flat], k)

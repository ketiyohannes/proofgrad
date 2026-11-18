"""Spec for place_targets: n targets on an n x n grid, one per row and column, each on a cell with even x + y.

Domain: odd n with 1 <= n < 1000 (kept <= 199 for speed, plus the boundary 999). Any valid placement
is accepted.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "place_targets"

CLARIFICATIONS = [
    "Return a list of n (x, y) pairs using 1-based coordinates; any valid placement and order is accepted.",
]

odd_n = st.one_of(st.integers(0, 99).map(lambda k: 2 * k + 1), st.sampled_from([1, 3, 5, 997, 999]))


def pairs(f, n):
    result = f(n)
    assert isinstance(result, list)
    out = []
    for p in result:
        x, y = p
        out.append((x, y))
    return out


@prop("Exactly n targets are returned, each a pair of integers.", n=odd_n)
def has_n_targets(f, n):
    result = pairs(f, n)
    assert len(result) == n
    assert all(isinstance(x, int) and isinstance(y, int) for x, y in result)


@prop("Every coordinate lies within the grid, 1..n.", n=odd_n)
def within_grid(f, n):
    assert all(1 <= x <= n and 1 <= y <= n for x, y in pairs(f, n))


@prop("Every target is on a special cell (x + y even).", n=odd_n)
def on_special_cells(f, n):
    assert all((x + y) % 2 == 0 for x, y in pairs(f, n))


@prop("Every row holds exactly one target.", n=odd_n)
def one_per_row(f, n):
    assert sorted(x for x, _ in pairs(f, n)) == list(range(1, n + 1))


@prop("Every column holds exactly one target.", n=odd_n)
def one_per_column(f, n):
    assert sorted(y for _, y in pairs(f, n)) == list(range(1, n + 1))

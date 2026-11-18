"""Spec for minimum_paint_applications: fewest 2-cell roller applications that cover every cell of an N x M board.

Domain: 1 <= N, M <= 100. Each application covers two cells; applications may overlap already
painted cells, so a board with an odd number of cells is still coverable (the unit tests give
1 for a 1 x 1 board and 5 for 3 x 3).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "minimum_paint_applications"

CLARIFICATIONS = [
    "Applications may overlap cells that are already painted (a strip may even hang over the board edge), so every board size can be fully covered.",
    "Return the count as an int.",
]

dims = st.integers(1, 100)


def can_cover(n, m, k):
    """k strips cover at most 2k cells, and with overlap allowed 2k >= n*m cells is always enough."""
    return 2 * k >= n * m


def minimum(n, m):
    k = 0
    while not can_cover(n, m, k):
        k += 1
    return k


@prop("The result is an int equal to the fewest applications that can cover all N*M cells.", n=dims, m=dims)
def matches_definition(f, n, m):
    r = f(n, m)
    assert isinstance(r, int)
    assert r == minimum(n, m)


@prop("The applications cover the board: twice the result is at least N*M.", n=dims, m=dims)
def enough_paint(f, n, m):
    assert 2 * f(n, m) >= n * m


@prop("No fewer applications suffice: twice (result - 1) is less than N*M.", n=dims, m=dims)
def not_wasteful(f, n, m):
    assert 2 * (f(n, m) - 1) < n * m


@prop("Swapping N and M does not change the answer.", n=dims, m=dims)
def symmetric(f, n, m):
    assert f(n, m) == f(m, n)


@prop("Boards with an odd number of cells need one extra application for the leftover cell.",
      n=st.integers(0, 49).map(lambda k: 2 * k + 1), m=st.integers(0, 49).map(lambda k: 2 * k + 1))
def odd_area(f, n, m):
    assert f(n, m) == (n * m - 1) // 2 + 1

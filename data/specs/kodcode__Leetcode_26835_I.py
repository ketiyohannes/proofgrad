"""Spec for is_valid_triangle: True iff each pair of sides sums to strictly more than the third.

Domain: arbitrary integers (zero and negative sides are allowed and must give False).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_valid_triangle"

CLARIFICATIONS = [
    "Return a bool. The inequalities are strict: sides whose two smaller values sum exactly to the largest do not form a valid triangle.",
]

side = st.one_of(st.integers(-5, 20), st.integers(-10**6, 10**6), st.integers(0, 3))


def valid(a, b, c):
    return a + b > c and a + c > b and b + c > a


@prop("The result is a bool matching the strict triangle inequality for all three pairs.", a=side, b=side, c=side)
def matches_definition(f, a, b, c):
    r = f(a, b, c)
    assert isinstance(r, bool)
    assert r == valid(a, b, c)


@prop("The answer does not depend on the order of the sides.", a=side, b=side, c=side)
def order_invariant(f, a, b, c):
    r = f(a, b, c)
    assert f(b, c, a) == r and f(c, a, b) == r and f(b, a, c) == r and f(a, c, b) == r and f(c, b, a) == r


@prop("Degenerate triangles (two sides summing exactly to the third) are invalid.", x=st.integers(0, 10**6), y=st.integers(0, 10**6))
def degenerate_invalid(f, x, y):
    assert f(x, y, x + y) is False
    assert f(x + y, x, y) is False
    assert f(x, x + y, y) is False


@prop("Sides x, y, z with z one less than x + y (all positive) form a valid triangle.",
      x=st.integers(1, 10**6), y=st.integers(1, 10**6))
def nearly_degenerate_valid(f, x, y):
    assert f(x, y, x + y - 1) is True
    assert f(x + y - 1, x, y) is True
    assert f(x, x, x) is True


@prop("A zero or negative side is never valid.", a=st.integers(-100, 0), b=st.integers(-100, 100), c=st.integers(-100, 100))
def non_positive_invalid(f, a, b, c):
    assert f(a, b, c) is False
    assert f(b, a, c) is False
    assert f(b, c, a) is False

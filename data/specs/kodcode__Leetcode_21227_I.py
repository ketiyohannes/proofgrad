"""Spec for largest_rectangle_area: largest area of a rectangle spanning consecutive buildings (histogram).

Domain: lists of non-negative integer heights, including the empty list.
A rectangle over buildings i..j has height min(heights[i..j]) and width j - i + 1.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "largest_rectangle_area"

CLARIFICATIONS = ["Return 0 for an empty list."]

heights = st.one_of(
    st.lists(st.integers(0, 10), max_size=25),
    st.lists(st.integers(0, 2), max_size=25),
    st.lists(st.integers(0, 1000), max_size=25),
    st.lists(st.integers(0, 20), max_size=25).map(sorted),
    st.lists(st.integers(0, 20), max_size=25).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(0, 10), st.integers(0, 15)),
)


def areas(hs):
    return [min(hs[i:j + 1]) * (j - i + 1) for i in range(len(hs)) for j in range(i, len(hs))]


@prop("The result is an int equal to the best min-height times width over all runs of consecutive buildings.", hs=heights)
def matches_definition(f, hs):
    r = f(hs)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == max(areas(hs), default=0)


@prop("No run of consecutive buildings gives a larger rectangle than the result.", hs=heights)
def is_upper_bound(f, hs):
    r = f(hs)
    assert all(a <= r for a in areas(hs))


@prop("Reversing the buildings does not change the answer.", hs=heights)
def reverse_invariant(f, hs):
    assert f(hs) == f(hs[::-1])


@prop("The answer is at least the tallest building and at least len * min height.", hs=st.lists(st.integers(0, 100), min_size=1, max_size=30))
def simple_lower_bounds(f, hs):
    r = f(hs)
    assert r >= max(hs)
    assert r >= len(hs) * min(hs)


@prop("Empty gives 0, one building gives its height, equal buildings give height * count.",
      h=st.integers(0, 1000), n=st.integers(1, 20))
def degenerate_cases(f, h, n):
    assert f([]) == 0
    assert f([h]) == h
    assert f([h] * n) == h * n

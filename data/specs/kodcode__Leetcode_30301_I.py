"""Spec for max_rect_area: largest rectangle formed over a run of adjacent buildings (histogram).

Domain: lists of non-negative integer heights, including the empty list. A run of buildings i..j
forms a rectangle of area (j - i + 1) * min(heights[i..j]).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_rect_area"

CLARIFICATIONS = [
    "Return 0 for an empty list.",
]

heights = st.one_of(
    st.lists(st.integers(min_value=0, max_value=4), max_size=20),
    st.lists(st.integers(min_value=0, max_value=10**4), max_size=20),
    st.lists(st.integers(min_value=0, max_value=10), max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=10), max_size=20).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(min_value=0, max_value=10), st.integers(min_value=1, max_value=12)),
)


def best_area(hs):
    return max((min(hs[i:j + 1]) * (j - i + 1) for i in range(len(hs)) for j in range(i, len(hs))), default=0)


@prop("The result is an int equal to the best width * minimum height over all runs of adjacent buildings.", hs=heights)
def matches_brute_force(f, hs):
    r = f(hs)
    assert isinstance(r, int)
    assert r == best_area(hs)


@prop("The result is at least the tallest building and at least the full width times the shortest building.",
      hs=heights.filter(bool))
def lower_bounds(f, hs):
    r = f(hs)
    assert r >= max(hs)
    assert r >= min(hs) * len(hs)


@prop("Reversing the buildings does not change the result.", hs=heights)
def reverse_invariant(f, hs):
    assert f(hs) == f(hs[::-1])


@prop("Equal-height buildings give height * count.", h=st.integers(min_value=0, max_value=1000), n=st.integers(min_value=1, max_value=30))
def equal_heights(f, h, n):
    assert f([h] * n) == h * n


@prop("An empty list gives 0 and a single building gives its height.", h=st.integers(min_value=0, max_value=10**6))
def degenerate(f, h):
    assert f([]) == 0
    assert f([h]) == h

"""Spec for trap: total rain water trapped between columns of the given heights.

Domain: lists of non-negative integers, including the empty list.
Water above column i is min(max height to its left incl. i, max height to its right incl. i) - height[i].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "trap"

CLARIFICATIONS = ["Return 0 for an empty list."]

heights = st.one_of(
    st.lists(st.integers(0, 10), max_size=30),
    st.lists(st.integers(0, 2), max_size=30),
    st.lists(st.integers(0, 1000), max_size=30),
    st.lists(st.integers(0, 20), max_size=30).map(sorted),
    st.lists(st.integers(0, 20), max_size=30).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(0, 10), st.integers(0, 15)),
)


def water(hs):
    return sum(max(0, min(max(hs[:i + 1]), max(hs[i:])) - hs[i]) for i in range(len(hs)))


@prop("The result is an int equal to the trapped water computed column by column.", hs=heights)
def matches_definition(f, hs):
    r = f(hs)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == water(hs)


@prop("Reversing the columns does not change the trapped water.", hs=heights)
def reverse_invariant(f, hs):
    assert f(hs) == f(hs[::-1])


@prop("Monotone (sorted or reverse-sorted) terrain traps no water.", hs=st.lists(st.integers(0, 50), max_size=30))
def monotone_traps_nothing(f, hs):
    assert f(sorted(hs)) == 0
    assert f(sorted(hs, reverse=True)) == 0


@prop("A pit between two walls holds min(walls) - depth per column.",
      a=st.integers(0, 100), b=st.integers(0, 100), inner=st.lists(st.integers(0, 100), min_size=1, max_size=8))
def single_basin(f, a, b, inner):
    lo = min(a, b)
    inner = [min(x, lo) for x in inner]
    assert f([a] + inner + [b]) == sum(lo - x for x in inner)


@prop("Empty, single-column and two-column inputs trap no water.", a=st.integers(0, 100), b=st.integers(0, 100))
def degenerate_cases(f, a, b):
    assert f([]) == 0
    assert f([a]) == 0
    assert f([a, b]) == 0

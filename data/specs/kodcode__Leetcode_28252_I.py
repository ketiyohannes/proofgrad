"""Spec for trap: total rain water trapped by an elevation map.

Domain: lists of non-negative integer heights, including the empty list. Water above column i is
min(tallest column at or left of i, tallest column at or right of i) - height[i].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "trap"

CLARIFICATIONS = [
    "Heights are non-negative integers; return 0 for an empty list.",
]

heights = st.one_of(
    st.lists(st.integers(min_value=0, max_value=3), max_size=20),
    st.lists(st.integers(min_value=0, max_value=10**4), max_size=25),
    st.lists(st.integers(min_value=0, max_value=10), max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=10), max_size=20).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(min_value=0, max_value=5), st.integers(min_value=0, max_value=10)),
)


def water(hs):
    total = 0
    for i, h in enumerate(hs):
        level = min(max(hs[: i + 1]), max(hs[i:]))
        total += level - h
    return total


@prop("The result is an int equal to the sum over columns of the trapped water above each column.", hs=heights)
def matches_definition(f, hs):
    r = f(hs)
    assert isinstance(r, int)
    assert r == water(hs)


@prop("Reversing the elevation map does not change the trapped water.", hs=heights)
def reverse_invariant(f, hs):
    assert f(hs) == f(hs[::-1])


@prop("Monotone (sorted or reverse-sorted) elevation maps trap no water.",
      hs=st.lists(st.integers(min_value=0, max_value=50), max_size=20), rev=st.booleans())
def monotone_traps_nothing(f, hs, rev):
    assert f(sorted(hs, reverse=rev)) == 0


@prop("A basin between two walls of height w over a flat floor traps w - floor per inner column.",
      w=st.integers(min_value=0, max_value=20), floor=st.integers(min_value=0, max_value=20),
      width=st.integers(min_value=1, max_value=10), extra=st.integers(min_value=0, max_value=5))
def simple_basin(f, w, floor, width, extra):
    floor = min(floor, w)
    assert f([w] + [floor] * width + [w + extra]) == (w - floor) * width


@prop("Fewer than three columns trap no water.",
      hs=st.lists(st.integers(min_value=0, max_value=10**4), max_size=2))
def too_short(f, hs):
    assert f(hs) == 0

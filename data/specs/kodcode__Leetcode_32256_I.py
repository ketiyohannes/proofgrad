"""Spec for trap_rain_water: total rain water trapped between poles.

Domain: lists of non-negative integer heights, including the empty list. Water above pole i is
min(tallest pole at or left of i, tallest pole at or right of i) - height[i].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "trap_rain_water"

CLARIFICATIONS = [
    "The water above each pole is the smaller of the tallest pole on its left and the tallest pole on its right (each including itself), minus its own height; return the sum over all poles.",
    "Heights are non-negative integers; return 0 for an empty list or fewer than three poles.",
]

heights = st.one_of(
    st.lists(st.integers(min_value=0, max_value=3), max_size=20),
    st.lists(st.integers(min_value=0, max_value=10**4), max_size=25),
    st.lists(st.integers(min_value=0, max_value=10), max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=10), max_size=20).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(min_value=0, max_value=5), st.integers(min_value=0, max_value=10)),
)


def water(hs):
    return sum(min(max(hs[: i + 1]), max(hs[i:])) - h for i, h in enumerate(hs))


@prop("The result is an int equal to the sum over poles of the water held above each pole.", hs=heights)
def matches_definition(f, hs):
    r = f(hs)
    assert isinstance(r, int)
    assert r == water(hs)


@prop("Reversing the poles does not change the trapped water.", hs=heights)
def reverse_invariant(f, hs):
    assert f(hs) == f(hs[::-1])


@prop("Monotone (sorted or reverse-sorted) poles trap no water.",
      hs=st.lists(st.integers(min_value=0, max_value=50), max_size=20), rev=st.booleans())
def monotone_traps_nothing(f, hs, rev):
    assert f(sorted(hs, reverse=rev)) == 0


@prop("A basin between two walls over a flat floor holds (lower wall - floor) per inner pole.",
      w=st.integers(min_value=0, max_value=20), floor=st.integers(min_value=0, max_value=20),
      width=st.integers(min_value=1, max_value=10), extra=st.integers(min_value=0, max_value=5))
def simple_basin(f, w, floor, width, extra):
    floor = min(floor, w)
    assert f([w + extra] + [floor] * width + [w]) == (w - floor) * width


@prop("Fewer than three poles trap no water.", hs=st.lists(st.integers(min_value=0, max_value=10**4), max_size=2))
def too_short(f, hs):
    assert f(hs) == 0

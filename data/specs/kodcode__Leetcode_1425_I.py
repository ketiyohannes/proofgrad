"""Spec for maxWaterTrapped: total rain water held between buildings of width 1 (the classic trapping rain water problem).

Domain: lists (possibly empty) of non-negative integer heights.
Water above building i is min(tallest building at or left of i, tallest at or right of i) - height[i].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "maxWaterTrapped"

CLARIFICATIONS = [
    "Return the total units of water trapped: the water level above each building is limited by the tallest building on its left and the tallest on its right (whichever is lower), and water spills off both ends.",
    "Heights are non-negative ints; an empty list or fewer than three buildings trap 0. Return an int.",
]

heights = st.one_of(
    st.lists(st.integers(0, 5), max_size=20),
    st.lists(st.integers(0, 100), max_size=20),
    st.lists(st.integers(0, 1), max_size=20),
)


def water(h):
    return sum(max(0, min(max(h[: i + 1]), max(h[i:])) - h[i]) for i in range(len(h)))


@prop("The total equals the sum, over buildings, of how far the lower of the two surrounding maxima rises above it.", h=heights)
def matches_definition(f, h):
    assert f(h) == water(h)


@prop("Reversing the skyline does not change the amount of water.", h=heights)
def reverse_invariant(f, h):
    assert f(h[::-1]) == f(h)


@prop("Non-decreasing or non-increasing skylines hold no water.", h=st.lists(st.integers(0, 100), max_size=20).map(sorted), rev=st.booleans())
def monotone_no_water(f, h, rev):
    assert f(h[::-1] if rev else h) == 0


@prop("A valley between two walls fills up to the lower wall.", left=st.integers(1, 50), right=st.integers(1, 50),
      inner=st.lists(st.integers(0, 50), min_size=1, max_size=10))
def valley_fills_to_lower_wall(f, left, right, inner):
    level = min(left, right)
    inner = [min(x, level) for x in inner]
    assert f([left] + inner + [right]) == sum(level - x for x in inner)


@prop("Empty, single and two-building inputs trap 0; results are non-negative ints.", a=st.integers(0, 100), b=st.integers(0, 100), h=heights)
def degenerate(f, a, b, h):
    assert f([]) == 0
    assert f([a]) == 0
    assert f([a, b]) == 0
    r = f(h)
    assert isinstance(r, int) and r >= 0

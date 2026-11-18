"""Spec for max_trapped_water: total rain water trapped above an elevation profile.

Domain: heights is a list (possibly empty) of non-negative integers. Water above index i is
min(max(heights[:i+1]), max(heights[i:])) - heights[i].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_trapped_water"

CLARIFICATIONS = [
    "Return the total trapped water as an int; return 0 for fewer than three buildings.",
]

height_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=10), max_size=20),
    st.lists(st.integers(min_value=0, max_value=2), max_size=20),
    st.lists(st.integers(min_value=0, max_value=1000), max_size=20),
    st.builds(lambda v, n: [v] * n, st.integers(0, 10), st.integers(0, 10)),
)


def oracle(h):
    return sum(min(max(h[:i + 1]), max(h[i:])) - h[i] for i in range(len(h)))


@prop("The result equals the sum over positions of min(tallest to the left, tallest to the right) minus the height.",
      heights=height_lists)
def total_water(f, heights):
    assert f(heights) == oracle(heights)


@prop("Fewer than three buildings trap no water.", heights=st.lists(st.integers(min_value=0, max_value=100), max_size=2))
def too_few(f, heights):
    assert f(heights) == 0


@prop("A non-decreasing or non-increasing profile traps no water.",
      heights=st.lists(st.integers(min_value=0, max_value=100), max_size=20), desc=st.booleans())
def monotone_no_water(f, heights, desc):
    assert f(sorted(heights, reverse=desc)) == 0


@prop("Reversing the profile does not change the amount of water.", heights=height_lists)
def reversal_invariant(f, heights):
    assert f(heights[::-1]) == f(heights)


@prop("A single valley between two walls holds (lower wall - floor) * width.",
      left=st.integers(0, 50), right=st.integers(0, 50), floor_=st.integers(0, 50), width=st.integers(1, 8))
def single_valley(f, left, right, floor_, width):
    floor_ = min(floor_, left, right)
    assert f([left] + [floor_] * width + [right]) == (min(left, right) - floor_) * width

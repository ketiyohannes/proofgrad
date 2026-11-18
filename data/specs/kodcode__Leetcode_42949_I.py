"""Spec for minTime: split nums into at most n contiguous segments minimizing the largest segment sum.

Domain: nums is a non-empty list of non-negative integers; n is a positive integer that may exceed
len(nums) (extra processors stay idle). The completion time is the largest segment sum.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "minTime"

CLARIFICATIONS = [
    "Every element must be assigned to exactly one processor; each processor takes one contiguous (possibly empty) segment, so processors may be left idle.",
    "The total completion time is the largest segment sum, since processors work in parallel.",
]


@st.composite
def case(draw, max_len=9):
    nums = draw(st.one_of(
        st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=max_len),
        st.lists(st.integers(min_value=0, max_value=2), min_size=1, max_size=max_len),
        st.builds(lambda v, k: [v] * k, st.integers(0, 20), st.integers(1, max_len)),
    ))
    n = draw(st.integers(min_value=1, max_value=len(nums) + 2))
    return nums, n


def oracle(nums, n):
    m = len(nums)
    best = None
    for cuts in range(0, min(n - 1, m - 1) + 1):
        for pos in combinations(range(1, m), cuts):
            bounds = (0,) + pos + (m,)
            worst = max(sum(nums[a:b]) for a, b in zip(bounds, bounds[1:]))
            best = worst if best is None else min(best, worst)
    return best


@prop("The result equals the smallest achievable maximum segment sum.", c=case())
def is_optimal(f, c):
    nums, n = c
    assert f(nums, n) == oracle(nums, n)


@prop("The result is at least the largest element and at least ceil(sum / n).", c=case(max_len=30))
def lower_bounds(f, c):
    nums, n = c
    r = f(nums, n)
    assert r >= max(nums)
    assert r * n >= sum(nums)


@prop("With one processor the answer is the total sum.",
      nums=st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=30))
def single_processor(f, nums):
    assert f(nums, 1) == sum(nums)


@prop("With at least as many processors as elements the answer is the largest element.",
      nums=st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=30), extra=st.integers(0, 3))
def enough_processors(f, nums, extra):
    assert f(nums, len(nums) + extra) == max(nums)


@prop("Adding a processor never increases the answer.", c=case(max_len=20))
def monotone_in_processors(f, c):
    nums, n = c
    assert f(nums, n + 1) <= f(nums, n)

"""Spec for rob: maximum sum of a subset of houses with no two adjacent houses.

Domain: nums is a list (possibly empty) of non-negative integers.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "rob"

CLARIFICATIONS = [
    "Return 0 when there are no houses.",
]

small_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=100), max_size=12),
    st.lists(st.integers(min_value=0, max_value=2), max_size=12),
    st.builds(lambda v, n: [v] * n, st.integers(0, 50), st.integers(0, 12)),
)


def oracle(nums):
    n = len(nums)
    best = 0
    for size in range(1, (n + 1) // 2 + 1):
        for idx in combinations(range(n), size):
            if all(b - a >= 2 for a, b in zip(idx, idx[1:])):
                best = max(best, sum(nums[i] for i in idx))
    return best


@prop("The result equals the best total over all sets of pairwise non-adjacent houses.", nums=small_lists)
def is_optimal(f, nums):
    assert f(nums) == oracle(nums)


@prop("The result is at least the largest single house and at least the sum of every other house.",
      nums=st.lists(st.integers(min_value=0, max_value=10**6), min_size=1, max_size=40))
def lower_bounds(f, nums):
    r = f(nums)
    assert r >= max(nums)
    assert r >= sum(nums[0::2]) and r >= sum(nums[1::2])


@prop("The result never exceeds the total of all houses.",
      nums=st.lists(st.integers(min_value=0, max_value=10**6), max_size=40))
def upper_bound(f, nums):
    assert f(nums) <= sum(nums)


@prop("No houses give 0; one house gives its value; two houses give the larger value.",
      a=st.integers(min_value=0, max_value=10**6), b=st.integers(min_value=0, max_value=10**6))
def tiny_inputs(f, a, b):
    assert f([]) == 0
    assert f([a]) == a
    assert f([a, b]) == max(a, b)


@prop("Reversing the street does not change the answer.", nums=small_lists)
def reversal_invariant(f, nums):
    assert f(nums[::-1]) == f(nums)

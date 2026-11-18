"""Spec for max_subarray_sum: the maximum sum of a length-k contiguous subarray, or None if k > len(nums).

Domain: nums is a list (possibly empty) of integers, negatives allowed; k is a positive integer.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_subarray_sum"

CLARIFICATIONS = [
    "Return the maximum sum itself (an int), not the subarray.",
    "Return None (Python's null) if k is greater than len(nums); k is at least 1.",
]

num_lists = st.one_of(
    st.lists(st.integers(min_value=-20, max_value=20), max_size=15),
    st.lists(st.integers(min_value=-10**6, max_value=-1), max_size=15),
    st.lists(st.integers(min_value=-1, max_value=1), max_size=15),
)


@st.composite
def valid_case(draw):
    nums = draw(num_lists.filter(bool))
    k = draw(st.integers(min_value=1, max_value=len(nums)))
    return nums, k


def window_sums(nums, k):
    return [sum(nums[i:i + k]) for i in range(len(nums) - k + 1)]


@prop("The result is at least the sum of every length-k window.", c=valid_case())
def is_upper_bound(f, c):
    nums, k = c
    r = f(nums, k)
    assert all(r >= s for s in window_sums(nums, k))


@prop("The result is the sum of some length-k window.", c=valid_case())
def is_attained(f, c):
    nums, k = c
    assert f(nums, k) in window_sums(nums, k)


@prop("k greater than the list length gives None.", nums=num_lists, extra=st.integers(min_value=1, max_value=5))
def too_large_k(f, nums, extra):
    assert f(nums, len(nums) + extra) is None


@prop("k equal to the length gives the total sum; k = 1 gives the maximum element.", nums=num_lists.filter(bool))
def boundary_k(f, nums):
    assert f(nums, len(nums)) == sum(nums)
    assert f(nums, 1) == max(nums)


@prop("The result is an int when k <= len(nums).", c=valid_case())
def returns_int(f, c):
    nums, k = c
    assert isinstance(f(nums, k), int)

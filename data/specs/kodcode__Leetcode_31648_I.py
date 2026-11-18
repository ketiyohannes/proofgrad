"""Spec for min_largest_element: smallest achievable maximum after (sum, |difference|) replacement operations.

Domain: non-empty lists of positive integers. Statement semantics: replacing a, b by a + b and
|a - b| never lowers the maximum (a + b >= max(a, b) for non-negative values), so the answer is
max(nums), reached with zero operations.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_largest_element"

EXCLUDE_REASON = (
    "Each operation creates a + b >= max(a, b), so the largest element can never decrease and the true "
    "answer is max(nums); the reference returns gcd(nums) (e.g. [3, 7, 11] -> 1), which is unreachable."
)

nums_st = st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=8)


@prop("The result equals the original maximum, since no operation can lower the maximum.", nums=nums_st)
def equals_max(f, nums):
    assert f(nums) == max(nums)


@prop("The result is at least every element of the input.", nums=nums_st)
def upper_bound(f, nums):
    r = f(nums)
    assert all(r >= x for x in nums)


@prop("A single-element array returns that element.", x=st.integers(min_value=1, max_value=10**6))
def single(f, x):
    assert f([x]) == x

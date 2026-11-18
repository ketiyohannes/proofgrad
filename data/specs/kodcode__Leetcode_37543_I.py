"""Spec for check_array_length: whether the length after keeping each value at most twice equals k.

Domain: nums is a non-decreasing list of integers (possibly empty); k is a non-negative integer.
The new length is sum over distinct values v of min(count(v), 2).
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "check_array_length"

CLARIFICATIONS = [
    "Return a bool: True if and only if the array length after the removal equals k. An empty array has length 0.",
]

sorted_lists = st.one_of(
    st.lists(st.integers(min_value=-5, max_value=5), max_size=20),
    st.lists(st.integers(min_value=0, max_value=2), max_size=20),
    st.builds(lambda v, n: [v] * n, st.integers(-10, 10), st.integers(0, 10)),
    st.lists(st.integers(min_value=-1000, max_value=1000), unique=True, max_size=15),
).map(sorted)


def new_length(nums):
    return sum(min(c, 2) for c in Counter(nums).values())


@prop("Returns True when k is the length after keeping each value at most twice.", nums=sorted_lists)
def true_for_correct_length(f, nums):
    assert f(nums, new_length(nums)) is True


@prop("Returns False when k is off by one from the correct length.", nums=sorted_lists, up=st.booleans())
def false_for_off_by_one(f, nums, up):
    k = new_length(nums) + (1 if up else -1)
    if k >= 0:
        assert f(nums, k) is False


@prop("Returns False for the original length when some value appears three or more times.",
      nums=sorted_lists, v=st.integers(-5, 5), extra=st.integers(3, 6))
def original_length_wrong_with_triples(f, nums, v, extra):
    arr = sorted(nums + [v] * extra)
    assert f(arr, len(arr)) is False


@prop("The result is True for exactly one k among 0..len(nums)+2.", nums=sorted_lists)
def exactly_one_k(f, nums):
    results = [f(nums, k) for k in range(len(nums) + 3)]
    assert all(isinstance(r, bool) for r in results)
    assert [k for k, r in enumerate(results) if r] == [new_length(nums)]


@prop("An empty array has length 0.", k=st.integers(min_value=0, max_value=5))
def empty_array(f, k):
    assert f([], k) is (k == 0)

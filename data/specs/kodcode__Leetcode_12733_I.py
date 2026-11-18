"""Spec for longest_subarray_with_distinct_integers: length of the longest contiguous subarray with no repeated value.

Domain: nums is a list of integers (negatives allowed). An empty list gives 0, following the
reference solution and unit tests.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "longest_subarray_with_distinct_integers"

CLARIFICATIONS = [
    "The subarray must be contiguous.",
    "Return 0 for an empty array.",
    "Return the length as an int.",
]

small_ints = st.one_of(
    st.lists(st.integers(min_value=-4, max_value=4), min_size=1, max_size=20),
    st.lists(st.integers(min_value=0, max_value=1), min_size=1, max_size=20),
    st.builds(lambda x, n: [x] * n, st.integers(min_value=-5, max_value=5), st.integers(min_value=1, max_value=10)),
    st.builds(lambda xs, r: xs * r, st.lists(st.integers(min_value=-6, max_value=6), unique=True, min_size=1, max_size=6),
              st.integers(min_value=1, max_value=3)),
    st.lists(st.integers(min_value=-50, max_value=50), unique=True, min_size=1, max_size=15),
)


def has_distinct_window(nums, length):
    return any(len(set(nums[i:i + length])) == length for i in range(len(nums) - length + 1))


@prop("The result is an int and some contiguous subarray of that length has all distinct values.", nums=small_ints)
def is_achievable(f, nums):
    n = f(nums)
    assert isinstance(n, int)
    assert 1 <= n <= len(nums)
    assert has_distinct_window(nums, n)


@prop("No contiguous subarray longer than the returned length has all distinct values.", nums=small_ints)
def is_maximal(f, nums):
    n = f(nums)
    assert not any(has_distinct_window(nums, length) for length in range(n + 1, len(nums) + 1))


@prop("An empty array gives 0.", unused=st.just(None))
def empty_is_zero(f, unused):
    assert f([]) == 0


@prop("An array of one repeated value gives 1.",
      x=st.integers(min_value=-100, max_value=100), count=st.integers(min_value=1, max_value=10))
def all_same_is_one(f, x, count):
    assert f([x] * count) == 1


@prop("An array of all-distinct values gives its full length.",
      nums=st.lists(st.integers(min_value=-1000, max_value=1000), unique=True, min_size=1, max_size=30))
def all_distinct_is_full_length(f, nums):
    assert f(nums) == len(nums)


@prop("Reversing the array does not change the answer.", nums=small_ints)
def reversal_invariant(f, nums):
    assert f(nums) == f(nums[::-1])

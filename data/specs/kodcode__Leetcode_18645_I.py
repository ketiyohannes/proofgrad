"""Spec for third_max: the third largest distinct value, or the maximum if fewer than three distinct values exist.

Domain: nums is a non-empty list of integers (negatives allowed). Empty input is not
generated: the statement does not define it and the reference raises on it.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "third_max"

CLARIFICATIONS = [
    "nums contains at least one element.",
]

nums_lists = st.one_of(
    st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=20),
    st.lists(st.integers(min_value=-2, max_value=2), min_size=1, max_size=20),
    st.lists(st.integers(min_value=-1000, max_value=1000), unique=True, min_size=1, max_size=6),
    st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=20).map(sorted),
    st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=20).map(lambda xs: sorted(xs, reverse=True)),
)


@st.composite
def few_distinct(draw):
    values = draw(st.lists(st.integers(min_value=-100, max_value=100), unique=True, min_size=1, max_size=2))
    xs = draw(st.lists(st.sampled_from(values), min_size=1, max_size=10))
    return list(draw(st.permutations(xs + values)))


@st.composite
def many_distinct(draw):
    values = draw(st.lists(st.integers(min_value=-100, max_value=100), unique=True, min_size=3, max_size=8))
    xs = draw(st.lists(st.sampled_from(values), max_size=10))
    return list(draw(st.permutations(xs + values)))


@prop("The result is an element of nums.", nums=nums_lists)
def is_member(f, nums):
    assert f(nums) in nums


@prop("With at least three distinct values, exactly two distinct values are greater than the result.",
      nums=many_distinct())
def is_third_distinct_max(f, nums):
    r = f(nums)
    assert r in nums
    assert len({x for x in nums if x > r}) == 2


@prop("With fewer than three distinct values, the result is the maximum.", nums=few_distinct())
def fewer_than_three_returns_max(f, nums):
    assert f(nums) == max(nums)


@prop("Reordering the array does not change the answer.", nums=nums_lists, data=st.data())
def order_invariant(f, nums, data):
    shuffled = list(data.draw(st.permutations(nums)))
    assert f(shuffled) == f(nums)


@prop("Appending copies of existing elements does not change the answer.", nums=nums_lists, data=st.data())
def duplicate_invariant(f, nums, data):
    extra = data.draw(st.lists(st.sampled_from(nums), min_size=1, max_size=10))
    assert f(nums + extra) == f(nums)

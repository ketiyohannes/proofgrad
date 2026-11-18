"""Spec for find_pair_with_sum: whether two distinct elements of a list of unique integers sum to target.

Domain: lists of unique integers (possibly a single element or empty, negatives allowed) and an
integer target. Despite "exactly one solution", the unit tests require False when no pair exists.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_pair_with_sum"

CLARIFICATIONS = [
    "Return True if some two different elements sum to target, and False if no such pair exists (the input need not contain a solution).",
    "Return a bool (True or False).",
]

uniq = st.one_of(
    st.lists(st.integers(min_value=-8, max_value=8), unique=True, max_size=10),
    st.lists(st.integers(min_value=-10**6, max_value=10**6 + 5), unique=True, max_size=10),
)


@st.composite
def cases(draw):
    nums = draw(uniq)
    mode = draw(st.sampled_from(["any", "pair", "double"]))
    if mode == "pair" and len(nums) >= 2:
        i, j = draw(st.lists(st.integers(min_value=0, max_value=len(nums) - 1), min_size=2, max_size=2, unique=True))
        target = nums[i] + nums[j]
    elif mode == "double" and nums:
        target = 2 * draw(st.sampled_from(nums))
    else:
        target = draw(st.integers(min_value=-16, max_value=16))
    return nums, target


def has_pair(nums, target):
    return any(nums[i] + nums[j] == target for i in range(len(nums)) for j in range(i + 1, len(nums)))


@prop("The result is True exactly when two different elements sum to target.", case=cases())
def matches_definition(f, case):
    nums, target = case
    r = f(nums, target)
    assert isinstance(r, bool)
    assert r == has_pair(nums, target)


@prop("Whenever a pair summing to target is present, the result is True.", data=st.data(), nums=uniq.filter(lambda xs: len(xs) >= 2))
def finds_existing_pair(f, data, nums):
    i, j = data.draw(st.lists(st.integers(min_value=0, max_value=len(nums) - 1), min_size=2, max_size=2, unique=True))
    assert f(nums, nums[i] + nums[j]) is True


@prop("The same element is not used twice: target = 2 * x alone does not count.", data=st.data(), nums=uniq.filter(bool))
def no_reuse(f, data, nums):
    x = data.draw(st.sampled_from(nums))
    assert f(nums, 2 * x) is has_pair(nums, 2 * x)


@prop("Order of the elements does not matter.", case=cases(), data=st.data())
def order_invariant(f, case, data):
    nums, target = case
    assert f(list(data.draw(st.permutations(nums))), target) == f(nums, target)


@prop("A list with fewer than two elements gives False.", x=st.integers(min_value=-100, max_value=100), target=st.integers(min_value=-200, max_value=200))
def too_small(f, x, target):
    assert f([x], target) is False
    assert f([x], 2 * x) is False
    assert f([], target) is False

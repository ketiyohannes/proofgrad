"""Spec for two_sum: whether two elements at different positions sum to target.

Domain: lists of integers (possibly empty or with duplicates) and an integer target.
Despite "exactly one solution", the unit tests also expect False when no pair exists.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "two_sum"

CLARIFICATIONS = [
    "Return a bool. A pair exists only if two elements at different indices sum to target (equal values at different indices are allowed); return False if no such pair exists or the list has fewer than two elements.",
]

lists = st.one_of(
    st.lists(st.integers(-20, 20), max_size=15),
    st.lists(st.integers(-3, 3), max_size=10),
    st.lists(st.integers(-10**6, 10**6), max_size=10),
)


def has_pair(nums, target):
    return any(nums[i] + nums[j] == target for i in range(len(nums)) for j in range(i + 1, len(nums)))


@st.composite
def with_target(draw):
    nums = draw(lists)
    if len(nums) >= 2 and draw(st.booleans()):
        i, j = draw(st.lists(st.integers(0, len(nums) - 1), min_size=2, max_size=2, unique=True))
        target = nums[i] + nums[j]
    else:
        target = draw(st.integers(-40, 40))
    return nums, target


@prop("The result is a bool matching whether some pair of distinct positions sums to target.", case=with_target())
def matches_definition(f, case):
    nums, target = case
    r = f(nums, target)
    assert isinstance(r, bool)
    assert r == has_pair(nums, target)


@prop("When target is the sum of two chosen elements the result is True.", nums=st.lists(st.integers(-50, 50), min_size=2, max_size=15), data=st.data())
def planted_pair_found(f, nums, data):
    i, j = data.draw(st.lists(st.integers(0, len(nums) - 1), min_size=2, max_size=2, unique=True))
    assert f(nums, nums[i] + nums[j]) is True


@prop("An element cannot be used twice: target 2*x with a single copy of x is False; adding a second x makes it True.",
      xs=st.lists(st.integers(0, 15), unique=True, min_size=1, max_size=8), data=st.data())
def no_reuse(f, xs, data):
    # Distinct powers of 4: no two different ones sum to twice a third, so only x + x could hit the target.
    x = data.draw(st.sampled_from(xs))
    nums = [4 ** v for v in xs]
    t = 2 * 4 ** x
    assert f(nums, t) is False
    assert f(nums + [4 ** x], t) is True


@prop("Permuting the list does not change the answer.", case=with_target(), data=st.data())
def order_invariant(f, case, data):
    nums, target = case
    assert f(list(data.draw(st.permutations(nums))), target) == f(nums, target)


@prop("Empty and single-element lists give False.", x=st.integers(-100, 100), t=st.integers(-200, 200))
def tiny_lists(f, x, t):
    assert f([], t) is False
    assert f([x], t) is False
    assert f([x], 2 * x) is False

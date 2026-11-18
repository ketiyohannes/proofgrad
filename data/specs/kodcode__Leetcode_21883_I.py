"""Spec for highest_value_reached: maximum running total (starting at 0) over a sequence of +1/-1 steps.

Domain: lists whose elements are 1 or -1, including the empty list. The starting value 0 counts as
reached, so the answer is never negative.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "highest_value_reached"

CLARIFICATIONS = [
    "The starting value 0 counts as reached, so the result is at least 0 (e.g. all decrements or an empty list give 0).",
]

steps = st.one_of(
    st.lists(st.sampled_from([1, -1]), max_size=40),
    st.lists(st.sampled_from([1, 1, 1, -1]), max_size=40),
    st.lists(st.sampled_from([1, -1, -1, -1]), max_size=40),
)


def highest(nums):
    return max([sum(nums[:k]) for k in range(len(nums) + 1)])


@prop("The result is an int equal to the largest prefix sum, counting the empty prefix (0).", nums=steps)
def matches_definition(f, nums):
    r = f(nums)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == highest(nums)


@prop("The result is never negative.", nums=steps)
def non_negative(f, nums):
    assert f(nums) >= 0


@prop("Some prefix of the operations reaches the returned value.", nums=steps)
def is_reached(f, nums):
    r = f(nums)
    assert any(sum(nums[:k]) == r for k in range(len(nums) + 1))


@prop("Appending operations never lowers the highest value reached.", nums=steps, more=steps)
def monotone_in_prefix(f, nums, more):
    assert f(nums + more) >= f(nums)


@prop("All increments give the length; all decrements and the empty list give 0.", n=st.integers(0, 30))
def uniform_sequences(f, n):
    assert f([1] * n) == n
    assert f([-1] * n) == 0
    assert f([-1] * n + [1] * (n + 1)) == 1

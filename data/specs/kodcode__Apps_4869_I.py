"""Spec for single_number: the only element that appears once when every other element appears exactly twice.

Domain: lists built as pairs of distinct integers plus one unique integer, shuffled;
values may be negative or zero.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "single_number"


@st.composite
def instance(draw, lo=-10**6, hi=10**6, max_pairs=20):
    values = draw(st.lists(st.integers(lo, hi), min_size=1, max_size=max_pairs + 1, unique=True))
    single, paired = values[0], values[1:]
    nums = paired + paired + [single]
    nums = draw(st.permutations(nums))
    return list(nums), single


@prop("The result is the element that appears exactly once.", case=st.one_of(instance(), instance(-5, 5, 10)))
def finds_single(f, case):
    nums, single = case
    assert f(nums) == single


@prop("Negative and zero singles are found.", case=instance(-10**6, 0))
def nonpositive_single(f, case):
    nums, single = case
    assert f(nums) == single


@prop("The single element is found wherever it is placed (first, last or middle).",
      case=instance(max_pairs=10), where=st.sampled_from(["first", "last"]))
def position_independent(f, case, where):
    nums, single = case
    rest = [x for x in nums if x != single]
    arranged = [single] + rest if where == "first" else rest + [single]
    assert f(arranged) == single


@prop("A one-element list returns that element.", x=st.integers(-10**9, 10**9))
def single_element(f, x):
    assert f([x]) == x

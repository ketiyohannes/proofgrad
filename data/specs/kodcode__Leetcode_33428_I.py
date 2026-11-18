"""Spec for single_number: the value appearing once in a list where every other value appears exactly twice.

Domain: lists built from distinct integers (negatives allowed), one occurring once and the rest
exactly twice, in arbitrary order.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "single_number"


@st.composite
def instances(draw, lo=-10**6, hi=10**6):
    vals = draw(st.lists(st.integers(min_value=lo, max_value=hi), unique=True, min_size=1, max_size=15))
    single, pairs = vals[0], vals[1:]
    nums = list(draw(st.permutations(pairs + pairs + [single])))
    return nums, single


cases = st.one_of(instances(), instances(lo=-5, hi=5), instances(lo=0, hi=3))


@prop("The result is the value that occurs exactly once.", case=cases)
def finds_single(f, case):
    nums, single = case
    assert f(nums) == single


@prop("Negative singles are returned with their sign.", case=instances(lo=-10**6, hi=-1))
def negative_single(f, case):
    nums, single = case
    assert f(nums) == single


@prop("The single value is found wherever it is placed: first or last.", case=instances())
def position_independent(f, case):
    nums, single = case
    rest = [x for x in nums if x != single]
    assert f([single] + rest) == single
    assert f(rest + [single]) == single


@prop("Zero can be the single value.", pairs=st.lists(st.integers(min_value=1, max_value=50), unique=True, max_size=8), data=st.data())
def zero_single(f, pairs, data):
    nums = list(data.draw(st.permutations(pairs + pairs + [0])))
    assert f(nums) == 0


@prop("A one-element list returns that element.", x=st.integers(min_value=-10**9, max_value=10**9))
def single_element(f, x):
    assert f([x]) == x

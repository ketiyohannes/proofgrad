"""Spec for single_number: the only value occurring once when every other value occurs exactly twice.

Domain: lists built from distinct integers (negatives and zero allowed), each paired except one, in any order.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "single_number"


@st.composite
def cases(draw, lo=-10**6, hi=10**6):
    vals = draw(st.lists(st.integers(lo, hi), unique=True, min_size=1, max_size=12))
    single, pairs = vals[0], vals[1:]
    arr = list(draw(st.permutations([single] + pairs + pairs)))
    return arr, single


@prop("The result is the value that occurs exactly once.", case=cases())
def finds_single(f, case):
    arr, single = case
    assert f(arr) == single


@prop("Works with small values including zero and negatives.", case=cases(-3, 3))
def small_values(f, case):
    arr, single = case
    assert f(arr) == single


@prop("The result is an element of the input.", case=cases())
def is_member(f, case):
    arr, _ = case
    assert f(arr) in arr


@prop("Reordering the input does not change the result.", case=cases(), data=st.data())
def order_invariant(f, case, data):
    arr, single = case
    assert f(list(data.draw(st.permutations(arr)))) == single


@prop("A single-element list returns that element.", x=st.integers(-10**6, 10**6))
def single_element(f, x):
    assert f([x]) == x

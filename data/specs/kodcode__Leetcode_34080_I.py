"""Spec for min_elements: element-wise minimum of two equal-length integer lists, [] if lengths differ.

Domain: integer lists (negatives allowed), possibly empty, of equal or different lengths.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_elements"

ints = st.integers(min_value=-10**6, max_value=10**6)


@st.composite
def same_length(draw):
    n = draw(st.integers(min_value=0, max_value=15))
    small = draw(st.booleans())
    el = st.integers(min_value=-3, max_value=3) if small else ints
    return draw(st.lists(el, min_size=n, max_size=n)), draw(st.lists(el, min_size=n, max_size=n))


@st.composite
def different_length(draw):
    a = draw(st.lists(ints, max_size=10))
    b = draw(st.lists(ints, max_size=10).filter(lambda b: len(b) != len(a)))
    return a, b


@prop("For equal lengths the result is a list of the same length.", case=same_length())
def length_preserved(f, case):
    a, b = case
    r = f(a, b)
    assert isinstance(r, list)
    assert len(r) == len(a)


@prop("Each entry is the smaller of the two corresponding entries.", case=same_length())
def elementwise_min(f, case):
    a, b = case
    r = f(a, b)
    assert all(r[i] == min(a[i], b[i]) for i in range(len(a)))


@prop("Swapping the two lists does not change the result.", case=same_length())
def symmetric(f, case):
    a, b = case
    assert f(a, b) == f(b, a)


@prop("Lists of different lengths give an empty list.", case=different_length())
def different_lengths_empty(f, case):
    a, b = case
    assert f(a, b) == []


@prop("A list paired with itself is returned unchanged; two empty lists give [].", a=st.lists(ints, max_size=15))
def identity(f, a):
    assert f(a, list(a)) == a
    assert f([], []) == []

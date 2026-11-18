"""Spec for transform_list: even numbers go up by 1, odd numbers go down by 1, order preserved.

Domain: non-empty lists of integers, including negative numbers and zero.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "transform_list"

int_lists = st.one_of(
    st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=40),
    st.lists(st.integers(min_value=-4, max_value=4), min_size=1, max_size=20),
    st.lists(st.integers(min_value=-10**12, max_value=10**12), min_size=1, max_size=10),
)


@prop("The result is a list of the same length as the input.", lst=int_lists)
def same_length(f, lst):
    result = f(lst)
    assert isinstance(result, list)
    assert len(result) == len(lst)


@prop("Every even element (including zero and negatives) is incremented by 1 at its position.", lst=int_lists)
def evens_incremented(f, lst):
    result = f(lst)
    for x, y in zip(lst, result):
        if x % 2 == 0:
            assert y == x + 1


@prop("Every odd element (including negatives) is decremented by 1 at its position.", lst=int_lists)
def odds_decremented(f, lst):
    result = f(lst)
    for x, y in zip(lst, result):
        if x % 2 != 0:
            assert y == x - 1


@prop("A single-element list is transformed correctly.", x=st.integers(min_value=-50, max_value=50))
def single_element(f, x):
    assert f([x]) == [x + 1 if x % 2 == 0 else x - 1]

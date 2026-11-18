"""Spec for increment_array: a new list with every element increased by 1.

Domain: lists of integers (including negatives, zero and large values) and the empty list.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "increment_array"

int_lists = st.one_of(
    st.lists(st.integers(min_value=-1000, max_value=1000), max_size=40),
    st.lists(st.integers(min_value=-2, max_value=2), max_size=20),
    st.lists(st.integers(min_value=-10**12, max_value=10**12), max_size=10),
)


@prop("The result is a list with the same length as the input.", arr=int_lists)
def same_length(f, arr):
    result = f(arr)
    assert isinstance(result, list)
    assert len(result) == len(arr)


@prop("Each element of the result is the corresponding input element plus one.", arr=int_lists)
def each_incremented(f, arr):
    assert f(arr) == [x + 1 for x in arr]


@prop("The empty list gives the empty list.", dummy=st.just(None))
def empty_list(f, dummy):
    assert f([]) == []

"""Spec for frequency_counter: dict mapping each distinct integer in the list to its number of occurrences.

Domain: lists of integers (positive, negative, zero, duplicates), including the empty list.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "frequency_counter"

CLARIFICATIONS = ["Return a dict; the empty list gives {}."]

ints = st.one_of(
    st.lists(st.integers(-3, 3), max_size=40),
    st.lists(st.integers(-10**9, 10**9), max_size=30),
    st.builds(lambda x, n: [x] * n, st.integers(-100, 100), st.integers(1, 20)),
)


@prop("The result is a dict whose keys are exactly the distinct integers of the list.", lst=ints)
def keys_are_distinct_values(f, lst):
    r = f(lst)
    assert isinstance(r, dict)
    assert set(r) == set(lst)


@prop("Each value is the number of times its key occurs in the list.", lst=ints)
def values_are_counts(f, lst):
    r = f(lst)
    for k, v in r.items():
        assert v == lst.count(k)


@prop("The counts add up to the length of the list.", lst=ints)
def counts_sum_to_length(f, lst):
    assert sum(f(lst).values()) == len(lst)


@prop("Reordering the list does not change the result.", lst=ints, data=st.data())
def order_invariant(f, lst, data):
    assert f(data.draw(st.permutations(lst))) == f(lst)


@prop("The empty list gives {} and a single element x gives {x: 1}.", x=st.integers(-10**6, 10**6))
def small_cases(f, x):
    assert f([]) == {}
    assert f([x]) == {x: 1}

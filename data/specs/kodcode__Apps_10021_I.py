"""Spec for squared_evens: the squares of the even elements, in their original order.

Domain: lists of integers (negative values and zero allowed, as in the unit tests), possibly empty.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "squared_evens"

CLARIFICATIONS = [
    "Zero and negative even numbers count as even; return an empty list when there are no even numbers (including for an empty input).",
]

ints = st.one_of(
    st.lists(st.integers(min_value=-10**7, max_value=10**7), max_size=30),
    st.lists(st.integers(min_value=-4, max_value=4), max_size=30),
    st.lists(st.integers(min_value=-50, max_value=50).map(lambda x: 2 * x + 1), max_size=10),
    st.lists(st.integers(min_value=-50, max_value=50).map(lambda x: 2 * x), max_size=10),
)


@prop("The result is a list equal to the squares of the even elements, in input order.", nums=ints)
def matches_definition(f, nums):
    r = f(nums)
    assert isinstance(r, list)
    assert r == [x * x for x in nums if x % 2 == 0]


@prop("The result has exactly as many elements as the input has even numbers.", nums=ints)
def length_counts_evens(f, nums):
    assert len(f(nums)) == sum(1 for x in nums if x % 2 == 0)


@prop("Odd numbers never contribute: a list of only odd numbers gives an empty list.",
      nums=st.lists(st.integers(min_value=-10**6, max_value=10**6).map(lambda x: 2 * x + 1), max_size=20))
def odds_ignored(f, nums):
    assert f(nums) == []


@prop("Negative even numbers and zero are squared like positive ones.",
      nums=st.lists(st.integers(min_value=-10**6, max_value=0).map(lambda x: 2 * x), min_size=1, max_size=20))
def negative_evens(f, nums):
    assert f(nums) == [x * x for x in nums]


@prop("Concatenating two inputs concatenates their results.", a=ints, b=ints)
def concatenation(f, a, b):
    assert f(a + b) == f(a) + f(b)


@prop("The empty list gives the empty list.", dummy=st.just(None))
def empty_input(f, dummy):
    assert f([]) == []

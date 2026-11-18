"""Spec for factorial_list: factorials of the list elements that are <= n, in input order.

Domain: lists of non-negative integers (0..25, duplicates allowed, any order) and a
non-negative limit n (0..25), including the empty list.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "factorial_list"

CLARIFICATIONS = [
    "Keep the factorials in the same order as the corresponding numbers in the input list, including duplicates.",
]


def fact(k):
    p = 1
    for i in range(2, k + 1):
        p *= i
    return p


nums = st.one_of(
    st.lists(st.integers(0, 25), max_size=20),
    st.lists(st.integers(0, 4), max_size=12),
)
limit = st.one_of(st.integers(0, 25), st.integers(0, 4))


@prop("The result has one entry per input number that is <= n.", numbers=nums, n=limit)
def correct_count(f, numbers, n):
    result = f(numbers, n)
    assert isinstance(result, list)
    assert len(result) == sum(1 for x in numbers if x <= n)


@prop("The result is the factorials of the numbers <= n, in input order (duplicates kept).", numbers=nums, n=limit)
def exact_result(f, numbers, n):
    assert f(numbers, n) == [fact(x) for x in numbers if x <= n]


@prop("A number equal to n is included.", numbers=nums, n=limit)
def boundary_inclusive(f, numbers, n):
    assert f(numbers + [n], n)[-1] == fact(n)


@prop("The factorial of 0 is 1.", count=st.integers(1, 5), n=st.integers(0, 10))
def zero_factorial(f, count, n):
    assert f([0] * count, n) == [1] * count


@prop("If no number is <= n (or the list is empty), the result is empty.",
      n=st.integers(0, 15), offsets=st.lists(st.integers(1, 10), max_size=10))
def none_qualify(f, n, offsets):
    assert f([n + d for d in offsets], n) == []

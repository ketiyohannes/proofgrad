"""Spec for get_primes_desc: the primes of the input list (with multiplicity), sorted in descending order.

Domain: lists of integers, including 0, 1, negative numbers and duplicates (none of
0, 1 or negatives is prime by the stated definition), plus the empty list.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "get_primes_desc"

CLARIFICATIONS = [
    "Duplicate primes are kept: each occurrence in the input appears in the output.",
    "Zero, one and negative numbers are not prime.",
]


def is_prime(n):
    if n < 2:
        return False
    return all(n % d for d in range(2, n))


small_ints = st.integers(min_value=-20, max_value=120)
number_lists = st.one_of(
    st.lists(small_ints, max_size=30),
    st.lists(st.sampled_from([0, 1, 2, 3, 4, 9, 25, 49, 97, 91]), max_size=20),
    st.lists(st.integers(min_value=-5, max_value=5), max_size=20),
    st.lists(st.sampled_from([2, 3, 5, 7, 11, 13]), min_size=1, max_size=15),
)


@prop("The result is a list sorted in non-increasing order.", numbers=number_lists)
def sorted_descending(f, numbers):
    result = f(numbers)
    assert isinstance(result, list)
    assert all(result[i] >= result[i + 1] for i in range(len(result) - 1))


@prop("Every element of the result is a prime number.", numbers=number_lists)
def only_primes(f, numbers):
    assert all(is_prime(x) for x in f(numbers))


@prop("Every prime of the input appears in the result exactly as many times as in the input.", numbers=number_lists)
def all_primes_with_multiplicity(f, numbers):
    expected = Counter(x for x in numbers if is_prime(x))
    assert Counter(f(numbers)) == expected


@prop("The result equals the primes of the input sorted from largest to smallest.", numbers=number_lists)
def exact_result(f, numbers):
    assert f(numbers) == sorted((x for x in numbers if is_prime(x)), reverse=True)


@prop("Inputs without primes (including the empty list) give an empty list.",
      numbers=st.lists(st.sampled_from([-7, -2, -1, 0, 1, 4, 6, 8, 9, 15, 21, 25, 49, 91, 100]), max_size=15))
def no_primes_gives_empty(f, numbers):
    assert f(numbers) == []

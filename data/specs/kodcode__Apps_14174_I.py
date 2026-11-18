"""Spec for count_divisors: map each positive integer to the number of its positive divisors, preserving order.

Domain: lists of positive integers in 1..400 (the statement says nothing about 0 or negative numbers, so they
are not generated), including the empty list.
"""
from math import gcd, isqrt

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_divisors"

CLARIFICATIONS = [
    "The input contains only positive integers; count the positive divisors of each (1 and the number itself included).",
    "Return a list of ints in the same order as the input.",
]

positives = st.one_of(
    st.integers(min_value=1, max_value=400),
    st.sampled_from([1, 2, 3, 4, 9, 16, 36, 64, 97, 128, 360, 400]),
)
arrays = st.one_of(
    st.lists(positives, max_size=15),
    st.builds(lambda x, n: [x] * n, positives, st.integers(1, 5)),
)
PRIMES = [p for p in range(2, 400) if all(p % q for q in range(2, p))]


def brute_count(n):
    return sum(1 for d in range(1, n + 1) if n % d == 0)


@prop("Each output element equals the number of integers in 1..n that divide the corresponding input n.", arr=arrays)
def matches_brute_force(f, arr):
    assert f(arr) == [brute_count(n) for n in arr]


@prop("The output is a list of the same length as the input, and concatenating inputs concatenates outputs.",
      a=arrays, b=arrays)
def elementwise(f, a, b):
    out = f(a + b)
    assert isinstance(out, list)
    assert out == f(a) + f(b)


@prop("1 has exactly one divisor.", n=st.integers(1, 5))
def one_has_one_divisor(f, n):
    assert f([1] * n) == [1] * n


@prop("Every prime has exactly two divisors.", p=st.sampled_from(PRIMES))
def primes_have_two(f, p):
    assert f([p]) == [2]


@prop("The divisor count is multiplicative: d(a*b) == d(a)*d(b) for coprime a and b.",
      a=st.integers(1, 60), b=st.integers(1, 60))
def multiplicative(f, a, b):
    if gcd(a, b) != 1:
        b = 1
    da, db, dab = f([a, b, a * b])
    assert dab == da * db


@prop("A positive integer has an odd number of divisors exactly when it is a perfect square.", n=positives)
def odd_iff_square(f, n):
    (count,) = f([n])
    assert (count % 2 == 1) == (isqrt(n) ** 2 == n)

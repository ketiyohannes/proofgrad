"""Spec for first_n_primes: the first n prime numbers in increasing order.

Domain: n >= 1 (tested up to 400 to stay fast).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "first_n_primes"

CLARIFICATIONS = [
    "Return a list of ints in increasing order, starting with 2.",
]

small_n = st.one_of(st.integers(min_value=1, max_value=60), st.integers(min_value=1, max_value=400))


def is_prime(x):
    return x >= 2 and all(x % d for d in range(2, int(x ** 0.5) + 1))


@prop("The result is a list of exactly n elements.", n=small_n)
def has_length_n(f, n):
    r = f(n)
    assert isinstance(r, list)
    assert len(r) == n


@prop("Every element of the result is prime.", n=small_n)
def all_prime(f, n):
    assert all(isinstance(p, int) and is_prime(p) for p in f(n))


@prop("The result is strictly increasing.", n=small_n)
def strictly_increasing(f, n):
    r = f(n)
    assert all(a < b for a, b in zip(r, r[1:]))


@prop("No prime is skipped: every prime up to the last element appears in the result.", n=small_n)
def no_gaps(f, n):
    r = f(n)
    assert r, "result must be non-empty"
    assert r == [x for x in range(2, r[-1] + 1) if is_prime(x)]


@prop("The result for k is the prefix of length k of the result for n (k <= n).", n=small_n, data=st.data())
def prefix_consistent(f, n, data):
    k = data.draw(st.integers(min_value=1, max_value=n))
    assert f(k) == f(n)[:k]


@prop("The first prime is 2 and the first few primes are 2, 3, 5, 7, 11.", n=st.integers(min_value=1, max_value=5))
def small_cases(f, n):
    assert f(n) == [2, 3, 5, 7, 11][:n]

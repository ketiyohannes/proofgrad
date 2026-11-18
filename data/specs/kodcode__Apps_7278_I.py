"""Spec for findPrimes: the ascending list of all primes strictly less than n.

Domain: integers n in 0..3000 (the oracle uses trial division, as defined).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "findPrimes"

CLARIFICATIONS = ["Return the primes in ascending order as a list; n itself is never included."]


def is_prime(k):
    if k < 2:
        return False
    d = 2
    while d * d <= k:
        if k % d == 0:
            return False
        d += 1
    return True


limits = st.one_of(st.integers(0, 3000), st.integers(0, 30), st.sampled_from([0, 1, 2, 3, 4, 5, 9, 10, 11, 25, 49, 50, 121, 122]))


@prop("Every element of the result is a prime less than n.", n=limits)
def only_primes_below(f, n):
    result = f(n)
    assert isinstance(result, list)
    assert all(is_prime(p) and p < n for p in result)


@prop("Every prime less than n appears in the result.", n=limits)
def complete(f, n):
    result = set(f(n))
    assert all(p in result for p in range(n) if is_prime(p))


@prop("The result is strictly increasing.", n=limits)
def strictly_increasing(f, n):
    result = f(n)
    assert all(result[i] < result[i + 1] for i in range(len(result) - 1))


@prop("The result equals the list of primes below n.", n=limits)
def exact(f, n):
    assert f(n) == [p for p in range(n) if is_prime(p)]


@prop("For a prime p, findPrimes(p) excludes p and findPrimes(p + 1) ends with p.",
      p=st.sampled_from([2, 3, 5, 7, 11, 13, 29, 97, 101, 997, 1009]))
def boundary_exclusive(f, p):
    assert p not in f(p)
    assert f(p + 1)[-1] == p


@prop("n of 0, 1 or 2 gives an empty list.", n=st.integers(0, 2))
def tiny_n(f, n):
    assert f(n) == []

"""Spec for filter_primes: the prime elements of the input, in their original order (duplicates kept).

Domain: lists of integers, including 0, 1 and negatives (never prime), possibly empty.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "filter_primes"

CLARIFICATIONS = [
    "Numbers less than 2 (including 0, 1 and negatives) are not prime. Keep duplicates and the original order.",
]

nums = st.one_of(
    st.lists(st.integers(-20, 120), max_size=30),
    st.lists(st.integers(-10**4, 10**5), max_size=20),
    st.lists(st.sampled_from([0, 1, 2, 3, 4, 9, 15, 25, 49, 121, -2, -3]), max_size=15),
)


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, int(n ** 0.5) + 1))


@prop("The result is a list equal to the prime elements in input order.", xs=nums)
def matches_definition(f, xs):
    r = f(xs)
    assert isinstance(r, list)
    assert r == [x for x in xs if is_prime(x)]


@prop("Every element of the result is prime.", xs=nums)
def all_prime(f, xs):
    assert all(is_prime(x) for x in f(xs))


@prop("Squares of primes and other composites are excluded.",
      p=st.sampled_from([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]), q=st.integers(2, 40))
def composites_excluded(f, p, q):
    assert f([p * p, p * q, p]) == [p]


@prop("Numbers below 2 are never kept.", xs=st.lists(st.integers(-1000, 1), max_size=20))
def below_two_excluded(f, xs):
    assert f(xs) == []


@prop("Concatenating inputs concatenates the results.", a=nums, b=nums)
def concatenation(f, a, b):
    assert f(a + b) == f(a) + f(b)


@prop("The empty list gives an empty list.", dummy=st.just(None))
def empty_input(f, dummy):
    assert f([]) == []

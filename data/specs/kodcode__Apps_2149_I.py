"""Spec for prime_factors: sorted list of the distinct primes dividing n; ValueError for invalid n.

Domain: valid inputs are ints 2..~10**6 (bounded so a trial-division reference stays fast).
Invalid inputs are ints <= 1, fractional floats and strings (as in the unit tests);
integral floats such as 4.0 are not generated.
"""
import math

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "prime_factors"

CLARIFICATIONS = [
    "Inputs that are not of type int (for example 1.5 or a string) must also raise the ValueError with that message.",
    "Return a list of ints.",
]

ERROR_MESSAGE = "Input must be a positive integer greater than 1"

SMALL_PRIMES = [p for p in range(2, 200) if all(p % d for d in range(2, int(p**0.5) + 1))]


def is_prime(k):
    if k < 2:
        return False
    return all(k % d for d in range(2, math.isqrt(k) + 1))


# Products of small primes (with repetition) give many repeated factors; plain
# integers cover primes and arbitrary composites.
products_of_primes = st.lists(st.sampled_from(SMALL_PRIMES), min_size=1, max_size=6).map(math.prod)
prime_powers = st.builds(pow, st.sampled_from(SMALL_PRIMES[:10]), st.integers(min_value=1, max_value=12)).filter(
    lambda k: k <= 10**6
)
valid_n = st.one_of(
    st.integers(min_value=2, max_value=20000),
    st.sampled_from(SMALL_PRIMES),
    prime_powers,
    products_of_primes,
    st.sampled_from([2, 3, 4, 6, 9997, 19997]),
)
small_n = st.integers(min_value=2, max_value=3000)

invalid_ints = st.integers(min_value=-10**6, max_value=1)
non_integers = st.one_of(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6).filter(lambda x: x != int(x)),
    st.text(max_size=5),
)


@prop("Integers less than or equal to 1 raise ValueError with the required message.", n=invalid_ints)
def rejects_small_integers(f, n):
    try:
        f(n)
    except ValueError as exc:
        assert ERROR_MESSAGE in str(exc)
    else:
        raise AssertionError(f"no ValueError for n={n!r}")


@prop("Non-integer inputs (fractional floats, strings) raise ValueError with the required message.", n=non_integers)
def rejects_non_integers(f, n):
    try:
        f(n)
    except ValueError as exc:
        assert ERROR_MESSAGE in str(exc)
    else:
        raise AssertionError(f"no ValueError for n={n!r}")


@prop("The result is a list sorted in strictly ascending order (no duplicates).", n=valid_n)
def strictly_ascending(f, n):
    result = f(n)
    assert isinstance(result, list)
    assert all(a < b for a, b in zip(result, result[1:]))


@prop("Every returned value is a prime that divides n.", n=valid_n)
def all_prime_divisors(f, n):
    for p in f(n):
        assert isinstance(p, int) and is_prime(p) and n % p == 0, p


@prop("The returned primes account for all of n: dividing them out repeatedly leaves 1.", n=valid_n)
def complete_factorization(f, n):
    result = f(n)
    rest = n
    for p in result:
        assert p >= 2
        while rest % p == 0:
            rest //= p
    assert rest == 1


@prop("On small inputs the result equals the brute-force list of prime divisors.", n=small_n)
def matches_brute_force(f, n):
    expected = [p for p in range(2, n + 1) if n % p == 0 and is_prime(p)]
    assert f(n) == expected

"""Spec for count_valid_sequences: number of length-N sequences over 3 colours with no two equal adjacent colours.

Domain: N >= 1 (kept to N <= 3000 so exact big-integer answers stay cheap).
"""
from itertools import product

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_valid_sequences"

CLARIFICATIONS = ["Return the exact count as an int (no modulo), even when it is very large."]


def brute(n):
    return sum(all(seq[i] != seq[i + 1] for i in range(n - 1)) for seq in product("RGB", repeat=n))


@prop("For small N the count equals the number of valid sequences found by enumerating all colourings.", n=st.integers(1, 8))
def matches_enumeration(f, n):
    assert f(n) == brute(n)


@prop("Each valid sequence can be extended by exactly two colours, so f(N + 1) == 2 * f(N) (checked exactly for large N).",
      n=st.integers(1, 3000))
def extends_in_two_ways(f, n):
    assert f(n + 1) == 2 * f(n)


@prop("The result is a positive int.", n=st.integers(1, 3000))
def positive_int(f, n):
    r = f(n)
    assert isinstance(r, int) and r > 0


@prop("A single light can be any of the 3 colours, and N = 2 gives 6.", dummy=st.just(None))
def base_cases(f, dummy):
    assert f(1) == 3
    assert f(2) == 6

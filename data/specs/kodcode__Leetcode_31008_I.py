"""Spec for min_final_digits: fewest digits reachable by replacing substrings with their digit sum, when that sum is a single digit.

Domain: non-empty digit strings. Statement semantics: an operation replaces a non-empty substring
with the decimal digit equal to its digit sum, and is only allowed when that sum is at most 9.
"""
from functools import lru_cache

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_final_digits"

EXCLUDE_REASON = (
    "The statement only allows a replacement when the substring's sum is a single digit, so e.g. '99' "
    "cannot be reduced below 2 digits, but the reference (and its unit tests, e.g. nineteen 1s -> 1) "
    "always returns 1 by repeatedly taking digit sums."
)

digit_strs = st.text(alphabet="0123456789", min_size=1, max_size=6)


@lru_cache(maxsize=None)
def fewest(s):
    best = len(s)
    for i in range(len(s)):
        for j in range(i + 2, len(s) + 1):
            total = sum(map(int, s[i:j]))
            if total <= 9:
                best = min(best, fewest(s[:i] + str(total) + s[j:]))
    return best


@prop("The result equals the fewest digits reachable by valid single-digit-sum replacements.", s=digit_strs)
def matches_brute_force(f, s):
    assert f(s) == fewest(s)


@prop("If the total digit sum is at most 9, the whole string collapses to one digit.",
      s=st.text(alphabet="0123", min_size=1, max_size=4))
def small_sum_collapses(f, s):
    if sum(map(int, s)) <= 9:
        assert f(s) == 1


@prop("A string of 9s cannot be reduced at all.", n=st.integers(min_value=1, max_value=10))
def nines_irreducible(f, n):
    assert f("9" * n) == n


@prop("The result is between 1 and the length of the string.", s=digit_strs)
def bounds(f, s):
    assert 1 <= f(s) <= len(s)

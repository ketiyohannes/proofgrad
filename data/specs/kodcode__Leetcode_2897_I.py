"""Spec for longest_unique_substring_length: best achievable length of an all-distinct substring over all permutations of s.

Domain: lowercase strings, including the empty string.
"""
from itertools import permutations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "longest_unique_substring_length"

CLARIFICATIONS = [
    "Return 0 for the empty string.",
]

short_strs = st.one_of(st.text(alphabet="abc", max_size=5), st.text(alphabet="abcdef", max_size=5))
long_strs = st.one_of(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", max_size=60),
    st.text(alphabet="ab", max_size=30),
    st.builds(lambda c, n: c * n, st.sampled_from("az"), st.integers(min_value=1, max_value=20)),
)


def longest_distinct_run(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if len(set(s[i:j])) == j - i), default=0)


def brute(s):
    return max((longest_distinct_run("".join(p)) for p in set(permutations(s))), default=0)


@prop("On short strings, the result equals the best longest-distinct-substring over all permutations.", s=short_strs)
def matches_brute_force(f, s):
    r = f(s)
    assert isinstance(r, int)
    assert r == brute(s)


@prop("Some permutation achieves the result: it never exceeds the number of distinct letters.", s=long_strs)
def upper_bound(f, s):
    assert f(s) <= len(set(s))


@prop("The distinct letters can always be placed side by side, so the result is at least their number.", s=long_strs)
def lower_bound(f, s):
    assert f(s) >= len(set(s))


@prop("Reordering the input does not change the result.", s=long_strs, data=st.data())
def permutation_invariant(f, s, data):
    t = "".join(data.draw(st.permutations(s)))
    assert f(s) == f(t)


@prop("The empty string gives 0 and a string of one repeated letter gives 1.",
      c=st.sampled_from("abcxyz"), n=st.integers(min_value=1, max_value=30))
def degenerate(f, c, n):
    assert f("") == 0
    assert f(c * n) == 1

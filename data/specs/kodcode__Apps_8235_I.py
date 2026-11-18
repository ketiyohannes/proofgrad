"""Spec for find_longest_substring: length of the longest contiguous substring with no repeated character.

Domain: arbitrary strings (case-sensitive), including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_longest_substring"

CLARIFICATIONS = ["Characters are compared exactly (case-sensitive). Return an int; the empty string gives 0."]

small_text = st.one_of(
    st.text(alphabet="abcd", max_size=25),
    st.text(alphabet="ab", max_size=25),
    st.text(alphabet="abcdefghij aA!", max_size=30),
    st.builds(lambda c, n: c * n, st.sampled_from("aZ "), st.integers(0, 20)),
)


def best_length(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if len(set(s[i:j])) == j - i), default=0)


@prop("The result equals the length of the longest substring without repeated characters (checked against all substrings).", s=small_text)
def matches_brute_force(f, s):
    assert f(s) == best_length(s)


@prop("The result is an int between min(1, len(s)) and the number of distinct characters.", s=small_text)
def bounds(f, s):
    r = f(s)
    assert isinstance(r, int)
    assert min(1, len(s)) <= r <= len(set(s))


@prop("A string whose characters are all distinct has answer equal to its length.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyzABC0123456789"), unique=True, max_size=30).map("".join))
def all_distinct(f, s):
    assert f(s) == len(s)


@prop("Appending text can never decrease the answer.", s=small_text, t=small_text)
def concat_monotone(f, s, t):
    assert f(s + t) >= max(f(s), f(t))


@prop("The empty string gives 0 and a run of one repeated character gives 1.", c=st.sampled_from("ax "), n=st.integers(1, 30))
def degenerate(f, c, n):
    assert f("") == 0
    assert f(c * n) == 1

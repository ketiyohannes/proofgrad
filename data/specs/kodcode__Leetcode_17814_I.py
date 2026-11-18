"""Spec for length_of_longest_substring: length of the longest contiguous substring with no repeated character.

Domain: arbitrary strings (case-sensitive, spaces count as characters), including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "length_of_longest_substring"

CLARIFICATIONS = [
    "Return 0 for the empty string.",
    "Characters are compared exactly (case-sensitive); spaces and punctuation count as characters.",
]

small_text = st.one_of(
    st.text(alphabet="abcd", max_size=25),
    st.text(alphabet="ab", max_size=25),
    st.builds(lambda c, n: c * n, st.sampled_from("aZ "), st.integers(0, 20)),
    st.text(alphabet="abcdefghij aAbB!", max_size=30),
)


def distinct(sub):
    return len(set(sub)) == len(sub)


def best_length(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if distinct(s[i:j])), default=0)


@prop("The result is an int equal to the length of the longest substring without repeated characters.", s=small_text)
def matches_definition(f, s):
    r = f(s)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == best_length(s)


@prop("Some substring of the returned length has all distinct characters (the length is achievable).", s=small_text)
def length_is_achievable(f, s):
    n = f(s)
    assert 0 <= n <= len(s)
    assert any(distinct(s[i:i + n]) for i in range(len(s) - n + 1))


@prop("No longer substring has all distinct characters.", s=small_text)
def no_longer_substring(f, s):
    n = f(s)
    assert not any(distinct(s[i:i + n + 1]) for i in range(len(s) - n))


@prop("A string of all-distinct characters returns its full length.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyzABC0123456789"), unique=True, min_size=1, max_size=30).map("".join))
def all_distinct_full_length(f, s):
    assert f(s) == len(s)


@prop("Reversing the string does not change the answer.", s=small_text)
def reverse_invariant(f, s):
    assert f(s) == f(s[::-1])


@prop("The empty string gives 0 and a single repeated character gives 1.", c=st.sampled_from("ab Z"), n=st.integers(1, 15))
def degenerate_cases(f, c, n):
    assert f("") == 0
    assert f(c * n) == 1

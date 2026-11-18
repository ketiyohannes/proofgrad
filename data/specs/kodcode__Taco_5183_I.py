"""Spec for length_of_longest_substring: length of the longest contiguous substring with no repeated character.

Domain: strings of letters (mostly lowercase; the unit tests also use mixed case, compared
case-sensitively) and the empty string, for which the answer is 0.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "length_of_longest_substring"

CLARIFICATIONS = [
    "Return 0 for the empty string.",
    "Characters are compared case-sensitively ('a' and 'A' are different).",
]

texts = st.one_of(
    st.text(alphabet="abcd", max_size=25),
    st.text(alphabet="ab", max_size=25),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", max_size=30),
    st.builds(lambda c, n: c * n, st.sampled_from("ab"), st.integers(1, 20)),
    st.text(alphabet="aAbB", max_size=20),
)


def distinct(sub):
    return len(set(sub)) == len(sub)


def longest(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if distinct(s[i:j])), default=0)


@prop("The result is an int equal to the longest repeat-free substring length.", s=texts)
def matches_bruteforce(f, s):
    result = f(s)
    assert isinstance(result, int)
    assert result == longest(s)


@prop("The result is between 1 and the number of distinct characters for non-empty input.", s=texts.filter(len))
def bounds(f, s):
    assert 1 <= f(s) <= len(set(s))


@prop("A string of distinct characters gives its full length.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyz"), unique=True, min_size=1, max_size=26).map("".join))
def all_distinct(f, s):
    assert f(s) == len(s)


@prop("A single character repeated gives 1.", c=st.sampled_from("abz"), n=st.integers(1, 50))
def repeated_char(f, c, n):
    assert f(c * n) == 1


@prop("Reversing the string does not change the answer.", s=texts)
def reverse_invariant(f, s):
    assert f(s[::-1]) == f(s)


@prop("The empty string gives 0.", dummy=st.just(None))
def empty(f, dummy):
    assert f("") == 0

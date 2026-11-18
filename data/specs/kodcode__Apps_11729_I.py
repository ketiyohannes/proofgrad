"""Spec for longest_substring_without_repeating_characters: the leftmost longest contiguous substring with no repeated character.

Domain: arbitrary strings (characters compared exactly, case-sensitive), including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "longest_substring_without_repeating_characters"

CLARIFICATIONS = [
    "If several substrings have the same maximal length, return the one that starts earliest (leftmost).",
    "Characters are compared exactly (case-sensitive); spaces and punctuation count as characters.",
]

small_text = st.one_of(
    st.text(alphabet="abcd", max_size=25),
    st.text(alphabet="ab", max_size=25),
    st.builds(lambda c, n: c * n, st.sampled_from("aZ "), st.integers(0, 20)),
)
wide_text = st.one_of(st.text(alphabet="abcdefghij aAbB!", max_size=40), small_text)


def distinct(sub):
    return len(set(sub)) == len(sub)


def best_length(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if distinct(s[i:j])), default=0)


@prop("The result is a contiguous substring of the input.", s=wide_text)
def is_substring(f, s):
    assert f(s) in s


@prop("The result contains no repeated character.", s=wide_text)
def has_distinct_chars(f, s):
    assert distinct(f(s))


@prop("The result is as long as the longest substring without repeated characters.", s=small_text)
def is_longest(f, s):
    assert len(f(s)) == best_length(s)


@prop("Among substrings of maximal length, the one that starts earliest in the input is returned.", s=small_text)
def leftmost_on_ties(f, s):
    n = best_length(s)
    first = next((s[i:i + n] for i in range(len(s) - n + 1) if distinct(s[i:i + n])), "")
    assert f(s) == first


@prop("A string whose characters are all distinct is returned unchanged.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyzABC0123456789"), unique=True, min_size=1, max_size=30).map("".join))
def all_distinct_returned_whole(f, s):
    assert f(s) == s


@prop("The empty string gives the empty string.", dummy=st.just(None))
def empty_string(f, dummy):
    assert f("") == ""

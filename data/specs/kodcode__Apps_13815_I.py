"""Spec for longest_substring: the length of the longest contiguous substring with no repeated character.

Domain: arbitrary strings (case-sensitive, spaces count), including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "longest_substring"

CLARIFICATIONS = [
    "Return an int; the empty string gives 0. Characters are compared exactly (case-sensitive).",
]

small_text = st.one_of(
    st.text(alphabet="abcd", max_size=25),
    st.text(alphabet="ab", max_size=25),
    st.text(alphabet="abcdefghij aA", max_size=30),
    st.builds(lambda c, n: c * n, st.sampled_from("aZ "), st.integers(0, 20)),
)


def distinct(sub):
    return len(set(sub)) == len(sub)


def best(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if distinct(s[i:j])), default=0)


@prop("The result is an int equal to the length of the longest substring without repeated characters.", s=small_text)
def matches_definition(f, s):
    r = f(s)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == best(s)


@prop("The result never exceeds the number of distinct characters nor the string length.", s=small_text)
def upper_bounds(f, s):
    r = f(s)
    assert 0 <= r <= len(set(s)) <= len(s)


@prop("A string of all distinct characters gives its full length.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyzABC0123"), unique=True, min_size=1, max_size=30).map("".join))
def all_distinct(f, s):
    assert f(s) == len(s)


@prop("A repeated single character gives 1.", c=st.sampled_from("ab Z"), n=st.integers(1, 30))
def repeated_char(f, c, n):
    assert f(c * n) == 1


@prop("Reversing the string does not change the answer.", s=small_text)
def reverse_invariant(f, s):
    assert f(s) == f(s[::-1])


@prop("The empty string gives 0.", dummy=st.just(None))
def empty_string(f, dummy):
    assert f("") == 0

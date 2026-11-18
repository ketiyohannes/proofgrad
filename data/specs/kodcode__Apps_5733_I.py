"""Spec for length_of_longest_substring: length of the longest substring with no repeated character.

Domain: strings of English letters, digits, symbols and spaces (case-sensitive), including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "length_of_longest_substring"


def distinct(sub):
    return len(set(sub)) == len(sub)


def best(s):
    return max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if distinct(s[i:j])), default=0)


small_text = st.one_of(
    st.text(alphabet="abcd", max_size=25),
    st.text(alphabet="ab", max_size=25),
    st.text(alphabet="abcdefgh aA1!", max_size=30),
    st.builds(lambda c, n: c * n, st.sampled_from("a !"), st.integers(0, 15)),
)


@prop("The result equals the length of the longest substring without repeated characters.", s=small_text)
def is_longest(f, s):
    assert f(s) == best(s)


@prop("Some substring of the returned length has all distinct characters.", s=small_text)
def achievable(f, s):
    n = f(s)
    assert isinstance(n, int)
    assert 0 <= n <= len(s)
    assert any(distinct(s[i:i + n]) for i in range(len(s) - n + 1))


@prop("Every longer substring contains a repeated character.", s=small_text)
def no_longer(f, s):
    n = f(s)
    assert not any(distinct(s[i:i + n + 1]) for i in range(len(s) - n))


@prop("Reversing the string does not change the answer.", s=small_text)
def reverse_invariant(f, s):
    assert f(s) == f(s[::-1])


@prop("A string of all-distinct characters gives its full length.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyzABC0123456789!@# "), unique=True, max_size=30).map("".join))
def all_distinct(f, s):
    assert f(s) == len(s)


@prop("A string repeating one character gives 1, and the empty string gives 0.", c=st.sampled_from("ab !"), n=st.integers(0, 20))
def repeated_char(f, c, n):
    assert f(c * n) == min(n, 1)

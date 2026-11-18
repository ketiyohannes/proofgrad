"""Spec for count_palindromic_substrings: number of (start, end) positions whose substring is a palindrome.

Domain: non-empty strings of lowercase letters. Substrings at different positions are counted separately.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_palindromic_substrings"

CLARIFICATIONS = ["Equal substrings at different positions are counted separately. Return an int."]

text = st.one_of(
    st.text(alphabet="ab", min_size=1, max_size=25),
    st.text(alphabet="abc", min_size=1, max_size=25),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=25),
)


def brute(s):
    return sum(s[i:j] == s[i:j][::-1] for i in range(len(s)) for j in range(i + 1, len(s) + 1))


@prop("The result equals the number of palindromic substrings found by checking every substring.", s=text)
def matches_brute_force(f, s):
    assert f(s) == brute(s)


@prop("Reversing the string does not change the count.", s=text)
def reverse_invariant(f, s):
    assert f(s[::-1]) == f(s)


@prop("The result is an int between len(s) and len(s) * (len(s) + 1) / 2.", s=text)
def bounds(f, s):
    r = f(s)
    assert isinstance(r, int)
    assert len(s) <= r <= len(s) * (len(s) + 1) // 2


@prop("A run of n equal characters has n * (n + 1) / 2 palindromic substrings.", c=st.sampled_from("az"), n=st.integers(1, 40))
def all_equal(f, c, n):
    assert f(c * n) == n * (n + 1) // 2


@prop("A string of distinct characters has exactly len(s) palindromic substrings.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyz"), unique=True, min_size=1, max_size=26).map("".join))
def all_distinct(f, s):
    assert f(s) == len(s)

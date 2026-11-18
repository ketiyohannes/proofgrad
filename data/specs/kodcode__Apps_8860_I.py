"""Spec for contains_anagram: True iff some contiguous substring of s2 is a permutation of s1.

Domain: lowercase strings; s1 may be empty (unit tests), in which case the answer is True.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "contains_anagram"

CLARIFICATIONS = [
    "If s1 is the empty string, return True.",
    "Return a bool (True or False).",
]

s1_text = st.one_of(st.text(alphabet="ab", min_size=1, max_size=4), st.text(alphabet="abc", min_size=1, max_size=5))
s2_text = st.one_of(st.text(alphabet="ab", max_size=15), st.text(alphabet="abc", max_size=15), st.text(alphabet="abcd", max_size=12))


def brute(s1, s2):
    m = len(s1)
    return any(Counter(s2[i:i + m]) == Counter(s1) for i in range(len(s2) - m + 1))


@prop("The result agrees with comparing every window of s2 of length len(s1) to s1 as multisets.", s1=s1_text, s2=s2_text)
def matches_brute_force(f, s1, s2):
    assert f(s1, s2) == brute(s1, s2)


@prop("A permutation of s1 planted anywhere in s2 is found.", s1=s1_text, pre=s2_text, post=s2_text, data=st.data())
def planted_permutation_true(f, s1, pre, post, data):
    perm = "".join(data.draw(st.permutations(list(s1))))
    assert f(s1, pre + perm + post) is True


@prop("A window must match exactly: s1 is not found in a string made of s1's characters spread apart.",
      s1=st.text(alphabet="abc", min_size=2, max_size=4))
def spread_apart_false(f, s1):
    s2 = "x".join(s1)
    assert f(s1, s2) is False


@prop("If s1 is longer than s2 the result is False.", s1=st.text(alphabet="ab", min_size=2, max_size=8), cut=st.integers(1, 8))
def longer_s1_false(f, s1, cut):
    s2 = s1[: max(0, len(s1) - cut)]
    assert f(s1, s2) is False


@prop("The empty s1 gives True; a string always contains itself; the result is a bool.", s=s2_text, s1=s1_text)
def trivial_cases(f, s, s1):
    assert f("", s) is True
    assert f(s1, s1) is True
    assert isinstance(f(s1, s), bool)

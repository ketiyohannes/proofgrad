"""Spec for is_palindrome: True exactly when the string equals its reverse.

Domain: lowercase strings, including the empty string (the unit tests use it).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_palindrome"

CLARIFICATIONS = [
    "Return a Python bool (True/False). The empty string is a palindrome.",
]

lower = st.text(alphabet="abc", max_size=20)
any_lower = st.one_of(lower, st.text(alphabet="abcdefghijklmnopqrstuvwxyz", max_size=20))


@st.composite
def palindromes(draw):
    half = draw(st.text(alphabet="abcxyz", max_size=15))
    mid = draw(st.sampled_from(["", "a", "q"]))
    return half + mid + half[::-1]


@st.composite
def near_palindromes(draw):
    p = draw(palindromes().filter(lambda s: len(s) >= 2))
    i = draw(st.integers(0, len(p) // 2 - 1))
    j = len(p) - 1 - i
    c = draw(st.sampled_from([ch for ch in "abcxyz" if ch != p[j]]))
    return p[:i] + c + p[i + 1:]


@prop("The result is a bool equal to whether the string reads the same backwards.", s=any_lower)
def matches_definition(f, s):
    r = f(s)
    assert r is True or r is False
    assert r == (s == s[::-1])


@prop("Every constructed palindrome returns True.", s=palindromes())
def palindromes_true(f, s):
    assert f(s) is True


@prop("Changing one character of a palindrome on one side only returns False.", s=near_palindromes())
def near_palindromes_false(f, s):
    assert f(s) is False


@prop("Reversing the string does not change the answer.", s=any_lower)
def reverse_invariant(f, s):
    assert f(s) == f(s[::-1])


@prop("The empty string and single characters are palindromes.", c=st.sampled_from("az"))
def trivial_palindromes(f, c):
    assert f("") is True
    assert f(c) is True

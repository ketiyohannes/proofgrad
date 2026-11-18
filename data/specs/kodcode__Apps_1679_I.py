"""Spec for isPerfect: whether some substring with length in [minLength, maxLength] and no leading zero is a perfect square.

Domain: digit strings of length 0..10 (the unit tests include ""), 1 <= minLength <= maxLength,
maxLength may exceed len(s) (the unit tests do this).
"""
from math import isqrt

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "isPerfect"

CLARIFICATIONS = [
    "Substrings that start with the digit '0' (including \"0\" itself) are ignored, so \"04\" does not count as 4.",
    "Return a bool. If no substring has a length in the range (e.g. maxLength or minLength exceeds len(s), or s is empty), return False.",
]

digit_strings = st.one_of(
    st.text(alphabet="0123456789", max_size=10),
    st.text(alphabet="2378", max_size=10),
    st.text(alphabet="0123", max_size=10),
)


@st.composite
def cases(draw):
    s = draw(digit_strings)
    lo = draw(st.integers(1, max(1, len(s)) + 1))
    hi = draw(st.integers(lo, lo + 3))
    return s, lo, hi


def is_square(n):
    return isqrt(n) ** 2 == n


def oracle(s, lo, hi):
    return any(
        s[i] != "0" and is_square(int(s[i:j]))
        for i in range(len(s))
        for j in range(i + lo, min(len(s), i + hi) + 1)
    )


@prop("The result is a bool equal to whether a qualifying perfect-square substring exists.", case=cases())
def matches_definition(f, case):
    s, lo, hi = case
    r = f(s, lo, hi)
    assert r is True or r is False
    assert r == oracle(s, lo, hi)


@prop("Embedding a perfect square (without leading zero) of a length in range gives True.",
      root=st.integers(1, 300), pre=st.text(alphabet="0123456789", max_size=3),
      post=st.text(alphabet="0123456789", max_size=3), slack=st.integers(0, 2))
def embedded_square_found(f, root, pre, post, slack):
    sq = str(root * root)
    lo = max(1, len(sq) - slack)
    assert f(pre + sq + post, lo, len(sq) + slack) is True


@prop("Widening the length range never turns True into False.", case=cases(), extra=st.integers(0, 3))
def monotone_in_range(f, case, extra):
    s, lo, hi = case
    if f(s, lo, hi):
        assert f(s, max(1, lo - extra), hi + extra) is True


@prop("Substrings with a leading zero are ignored.", root=st.integers(1, 30), zeros=st.integers(1, 3))
def leading_zero_ignored(f, root, zeros):
    sq = str(root * root)
    s = "0" * zeros + sq
    n = len(s)
    assert f(s, n, n) is False
    assert f("0" * zeros, 1, zeros) is False


@prop("Strings using only non-square digits and lengths of exactly 1 give False.",
      s=st.text(alphabet="2378", min_size=1, max_size=10))
def no_single_digit_squares(f, s):
    assert f(s, 1, 1) is False


@prop("A range longer than the string gives False.", s=digit_strings, extra=st.integers(1, 4))
def range_beyond_length(f, s, extra):
    assert f(s, len(s) + extra, len(s) + extra + 2) is False

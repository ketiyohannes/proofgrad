"""Spec for smallest_lexicographic_substring: lexicographically smallest length-k substring of s.

Domain: s is any string of lowercase letters (possibly empty), k an integer. When k < 1 or
k > len(s) the result is "", following the reference solution and unit tests (which use k == 0).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "smallest_lexicographic_substring"

CLARIFICATIONS = [
    "Return an empty string if k < 1 or k > len(s).",
    "Return the substring as a str.",
]

strings = st.one_of(
    st.text(alphabet="abc", min_size=1, max_size=20),
    st.text(alphabet="ab", min_size=1, max_size=20),
    st.builds(lambda c, n: c * n, st.sampled_from("az"), st.integers(min_value=1, max_value=10)),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
    st.text(alphabet="abcdef", min_size=1, max_size=20).map(lambda t: "".join(sorted(t, reverse=True))),
)


@st.composite
def string_and_valid_k(draw):
    s = draw(strings)
    k = draw(st.one_of(st.just(1), st.just(len(s)), st.integers(min_value=1, max_value=len(s))))
    return s, k


@st.composite
def string_and_invalid_k(draw):
    s = draw(st.one_of(st.just(""), st.text(alphabet="abcxyz", min_size=1, max_size=10)))
    k = draw(st.one_of(st.integers(min_value=-3, max_value=0), st.integers(min_value=len(s) + 1, max_value=len(s) + 5)))
    return s, k


def substrings(s, k):
    return [s[i:i + k] for i in range(len(s) - k + 1)]


@prop("The result is a str that is a contiguous substring of s of length exactly k.", case=string_and_valid_k())
def is_substring_of_length_k(f, case):
    s, k = case
    result = f(s, k)
    assert isinstance(result, str)
    assert len(result) == k
    assert result in substrings(s, k)


@prop("The result is lexicographically <= every substring of s of length k.", case=string_and_valid_k())
def is_minimal(f, case):
    s, k = case
    result = f(s, k)
    assert all(result <= t for t in substrings(s, k))


@prop("If k < 1 or k > len(s), the result is the empty string.", case=string_and_invalid_k())
def no_substring_returns_empty(f, case):
    s, k = case
    assert f(s, k) == ""


@prop("k == len(s) returns s itself.", s=strings)
def full_length_returns_s(f, s):
    assert f(s, len(s)) == s


@prop("k == 1 returns the smallest character of s.", s=strings)
def single_char_is_min(f, s):
    assert f(s, 1) == min(s)

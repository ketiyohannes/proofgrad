"""Spec for restore_string: the decoded string has s[i] at position indices[i].

Domain: s is a non-empty string of lowercase letters and indices is a permutation of
range(len(s)). Empty strings are not generated (the statement and tests do not cover them).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "restore_string"

CLARIFICATIONS = [
    "indices is a permutation of 0..len(s)-1.",
    "Return the decoded string as a str.",
]

letters = st.one_of(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=26),
    st.text(alphabet="ab", min_size=1, max_size=26),
    st.builds(lambda c, n: c * n, st.sampled_from("xyz"), st.integers(min_value=1, max_value=10)),
)


@st.composite
def encoded(draw):
    s = draw(letters)
    n = len(s)
    indices = draw(st.one_of(
        st.permutations(list(range(n))),
        st.just(list(range(n))),
        st.just(list(range(n - 1, -1, -1))),
        st.integers(min_value=0, max_value=n - 1).map(lambda r: [(i + r) % n for i in range(n)]),
    ))
    return s, list(indices)


@prop("The result is a str of the same length as s.", case=encoded())
def same_length_string(f, case):
    s, indices = case
    result = f(s, indices)
    assert isinstance(result, str)
    assert len(result) == len(s)


@prop("Each character s[i] appears at position indices[i] of the result.", case=encoded())
def characters_placed(f, case):
    s, indices = case
    result = f(s, indices)
    assert all(result[indices[i]] == s[i] for i in range(len(s)))


@prop("The result uses exactly the same multiset of characters as s.", case=encoded())
def is_permutation_of_s(f, case):
    s, indices = case
    assert sorted(f(s, indices)) == sorted(s)


@prop("The identity permutation returns s unchanged.", s=letters)
def identity_is_noop(f, s):
    assert f(s, list(range(len(s)))) == s


@prop("The reversed permutation returns s reversed.", s=letters)
def reverse_permutation_reverses(f, s):
    assert f(s, list(range(len(s) - 1, -1, -1))) == s[::-1]

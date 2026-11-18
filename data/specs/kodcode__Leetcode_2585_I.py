"""Spec for remove_duplicates: keep only the first occurrence of each character, preserving order.

Domain: lowercase strings, including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "remove_duplicates"

CLARIFICATIONS = ["Return \"\" for an empty string."]

texts = st.one_of(
    st.text(alphabet="abc", max_size=30),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", max_size=40),
    st.builds(lambda c, n: c * n, st.sampled_from("az"), st.integers(0, 10)),
)


def first_occurrences(s):
    return "".join(c for i, c in enumerate(s) if c not in s[:i])


@prop("The result is a string equal to the input with every repeated occurrence removed.", s=texts)
def matches_definition(f, s):
    r = f(s)
    assert isinstance(r, str)
    assert r == first_occurrences(s)


@prop("Every character of the input appears in the result exactly once.", s=texts)
def each_char_once(f, s):
    r = f(s)
    assert sorted(r) == sorted(set(s))


@prop("Characters appear in the order of their first appearance in the input.", s=texts)
def first_appearance_order(f, s):
    r = f(s)
    assert [s.index(c) for c in r] == sorted(s.index(c) for c in r)


@prop("The result is a subsequence of the input that starts with the input's first character.", s=texts)
def is_subsequence(f, s):
    r = f(s)
    it = iter(s)
    assert all(c in it for c in r)
    assert r[:1] == s[:1]


@prop("A string with all distinct characters is unchanged; the empty string gives the empty string.",
      s=st.lists(st.sampled_from("abcdefghijklmnopqrstuvwxyz"), unique=True, max_size=26).map("".join))
def distinct_unchanged(f, s):
    assert f(s) == s
    assert f(s + s) == s
    assert f("") == ""

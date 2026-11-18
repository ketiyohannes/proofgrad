"""Spec for is_subsequence: whether s1 can be obtained from s2 by deleting characters without reordering.

Domain: lowercase strings, including empty strings (unit tests cover "" for both arguments).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_subsequence"

CLARIFICATIONS = [
    "Return a bool (True or False).",
    "The empty string is a subsequence of every string (including the empty string).",
]

small = st.text(alphabet="abc", max_size=10)
tiny = st.text(alphabet="ab", max_size=6)


def subseq(a, b):
    """Brute force: does some set of positions in b spell a in order?"""
    def go(i, j):
        if i == len(a):
            return True
        return any(b[k] == a[i] and go(i + 1, k + 1) for k in range(j, len(b)))
    return go(0, 0)


@st.composite
def derived_pair(draw):
    s2 = draw(st.text(alphabet="abcd", max_size=15))
    keep = draw(st.lists(st.booleans(), min_size=len(s2), max_size=len(s2)))
    return "".join(c for c, k in zip(s2, keep) if k), s2


@prop("The result is a bool matching whether s1 is a subsequence of s2.", s1=tiny, s2=small)
def matches_definition(f, s1, s2):
    r = f(s1, s2)
    assert isinstance(r, bool)
    assert r == subseq(s1, s2)


@prop("A string obtained by deleting characters from s2 is a subsequence of s2.", pair=derived_pair())
def deletions_are_subsequences(f, pair):
    s1, s2 = pair
    assert f(s1, s2) is True


@prop("A string longer than s2 is never a subsequence of it.", s2=small, extra=st.text(alphabet="abc", min_size=1, max_size=4))
def longer_is_not(f, s2, extra):
    assert f(s2 + extra, s2) is False
    assert f(extra + s2, s2) is False


@prop("Order matters: a reordering that is not a subsequence is rejected.", pair=derived_pair())
def order_matters(f, pair):
    s1, s2 = pair
    t = s1[::-1]
    assert f(t, s2) is subseq(t, s2)


@prop("Multiplicity matters: needing more copies of a character than s2 has is rejected.", s2=small, c=st.sampled_from("abc"))
def multiplicity_matters(f, s2, c):
    assert f(c * (s2.count(c) + 1), s2) is False
    assert f(c * s2.count(c), s2) is True


@prop("Empty s1 is always a subsequence; non-empty s1 is never a subsequence of the empty string.", s=small)
def empty_cases(f, s):
    assert f("", s) is True
    assert f(s, s) is True
    if s:
        assert f(s, "") is False

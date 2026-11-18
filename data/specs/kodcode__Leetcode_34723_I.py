"""Spec for can_transform: whether t is a subsequence of s.

Domain: arbitrary strings (characters compared exactly), including empty strings.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_transform"

small = st.one_of(st.text(alphabet="ab", max_size=8), st.text(alphabet="abc", max_size=8))


def is_subsequence(s, t):
    return any("".join(s[i] for i in idx) == t for idx in combinations(range(len(s)), len(t))) if len(t) <= len(s) else False


@prop("The result is a bool that is True exactly when t is obtained from s by deleting characters.",
      s=small, t=st.one_of(st.text(alphabet="ab", max_size=5), st.text(alphabet="abc", max_size=5)))
def matches_definition(f, s, t):
    r = f(s, t)
    assert isinstance(r, bool)
    assert r == is_subsequence(s, t)


@prop("Deleting any set of characters from s gives a string s can be transformed into.",
      s=st.text(alphabet="abcd", max_size=15), data=st.data())
def deletions_succeed(f, s, data):
    keep = data.draw(st.lists(st.booleans(), min_size=len(s), max_size=len(s)))
    t = "".join(c for c, k in zip(s, keep) if k)
    assert f(s, t) is True


@prop("Order matters: if t reorders characters so they cannot match in sequence, the answer is False.",
      a=st.sampled_from("ab"), n=st.integers(min_value=0, max_value=5))
def order_matters(f, a, n):
    b = "b" if a == "a" else "a"
    s = a * n + b
    assert f(s, b + a) is False
    assert f(s, a * n + b) is True


@prop("A target longer than the source, or with a character missing from it, is not reachable.",
      s=st.text(alphabet="ab", max_size=8), extra=st.text(alphabet="ab", min_size=1, max_size=3), pos=st.integers(min_value=0, max_value=8))
def impossible_targets(f, s, extra, pos):
    assert f(s, s + extra) is False
    p = min(pos, len(s))
    assert f(s, s[:p] + "z" + s[p:]) is False


@prop("Empty target is always reachable; empty source reaches only the empty target.",
      s=st.text(max_size=10), t=st.text(min_size=1, max_size=5))
def empty_cases(f, s, t):
    assert f(s, "") is True
    assert f("", t) is False
    assert f(s, s) is True

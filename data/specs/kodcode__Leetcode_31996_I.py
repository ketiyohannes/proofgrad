"""Spec for reorganizeString: a rearrangement of s with no two equal adjacent letters, or "" if none exists.

Domain: lowercase strings (non-empty in generated cases, plus the empty string which must give "").
Any valid rearrangement is accepted.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "reorganizeString"

CLARIFICATIONS = [
    "Return the result as a str; an empty input gives \"\".",
]


@st.composite
def strings(draw):
    shape = draw(st.sampled_from(["random", "few", "dominant", "single"]))
    if shape == "random":
        return draw(st.text(alphabet="abcdef", min_size=1, max_size=20))
    if shape == "few":
        return draw(st.text(alphabet="ab", min_size=1, max_size=15))
    if shape == "single":
        return draw(st.sampled_from("az")) * draw(st.integers(min_value=1, max_value=5))
    # One letter right at (or one above) the feasibility threshold.
    rest = draw(st.text(alphabet="bcd", min_size=0, max_size=12))
    k = (len(rest) + 1) + draw(st.sampled_from([0, 0, 1, -1]))
    k = max(k, 1)
    letters = list("a" * k + rest)
    return "".join(draw(st.permutations(letters)))


def feasible(s):
    return not s or max(Counter(s).values()) <= (len(s) + 1) // 2


@prop("The result is a str that is either empty or a rearrangement of exactly the input letters.", s=strings())
def is_rearrangement(f, s):
    r = f(s)
    assert isinstance(r, str)
    assert r == "" or Counter(r) == Counter(s)


@prop("No two adjacent characters of the result are equal.", s=strings())
def no_equal_neighbours(f, s):
    r = f(s)
    assert all(a != b for a, b in zip(r, r[1:]))


@prop("A non-empty rearrangement is returned whenever one exists.", s=strings())
def nonempty_when_feasible(f, s):
    if feasible(s):
        r = f(s)
        assert len(r) == len(s)


@prop("The empty string is returned when a letter occurs more than ceil(n/2) times.", s=strings())
def empty_when_infeasible(f, s):
    if not feasible(s):
        assert f(s) == ""


@prop("A single letter is returned unchanged; two or more copies of one letter alone give \"\".",
      c=st.sampled_from("abz"), n=st.integers(min_value=2, max_value=10))
def degenerate(f, c, n):
    assert f(c) == c
    assert f(c * n) == ""

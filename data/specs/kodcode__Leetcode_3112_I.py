"""Spec for max_depth: maximum nesting depth of a parentheses string.

Domain: balanced strings of '(' and ')' (including the empty string), generated as nested
structures with a known depth; plus the degenerate unbalanced inputs the unit tests use
(only '(' characters, or only ')' characters).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_depth"

CLARIFICATIONS = [
    "The empty string has depth 0.",
    "A string of k '(' characters only has depth k; a string of only ')' characters has depth 0.",
]


@st.composite
def balanced(draw, max_depth_left=4):
    """Return (string, depth) for a concatenation of nested groups."""
    count = draw(st.integers(min_value=0, max_value=3 if max_depth_left > 0 else 0))
    parts, depth = [], 0
    for _ in range(count):
        inner, d = draw(balanced(max_depth_left - 1))
        parts.append("(" + inner + ")")
        depth = max(depth, d + 1)
    return "".join(parts), depth


@st.composite
def nested(draw):
    """A deep nest optionally surrounded by other balanced groups, depth known."""
    k = draw(st.integers(min_value=1, max_value=15))
    left, dl = draw(balanced(3))
    right, dr = draw(balanced(3))
    core = "(" * k + ")" * k
    return left + core + right, max(k, dl, dr)


cases = st.one_of(balanced(), nested())


@prop("The result is an int equal to the nesting depth of a balanced string.", case=cases)
def matches_depth(f, case):
    s, d = case
    r = f(s)
    assert isinstance(r, int)
    assert r == d


@prop("Wrapping a balanced string in one more pair of parentheses increases the depth by exactly one.", case=cases)
def wrap_adds_one(f, case):
    s, d = case
    assert f("(" + s + ")") == f(s) + 1


@prop("The depth of a concatenation of balanced strings is the larger of their depths.", a=cases, b=cases)
def concat_is_max(f, a, b):
    assert f(a[0] + b[0]) == max(a[1], b[1])


@prop("k nested pairs '((...))' have depth k, while k side-by-side pairs '()()...' have depth 1.",
      k=st.integers(min_value=1, max_value=40))
def nest_vs_sequence(f, k):
    assert f("(" * k + ")" * k) == k
    assert f("()" * k) == 1


@prop("The empty string has depth 0; only '(' characters give their count; only ')' characters give 0.",
      k=st.integers(min_value=1, max_value=30))
def degenerate(f, k):
    assert f("") == 0
    assert f("(" * k) == k
    assert f(")" * k) == 0

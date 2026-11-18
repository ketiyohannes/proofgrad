"""Spec for is_valid_expression: whether a string of brackets ()[]{} is balanced and properly nested.

Domain: strings over the six bracket characters, including the empty string (valid).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_valid_expression"

CLARIFICATIONS = [
    "Return a bool; the empty string is valid.",
]

PAIRS = ["()", "[]", "{}"]


def valid(s):
    prev = None
    while prev != s:
        prev = s
        for p in PAIRS:
            s = s.replace(p, "")
    return s == ""


@st.composite
def balanced(draw, depth=3):
    parts = draw(st.lists(st.sampled_from(PAIRS), min_size=0, max_size=3))
    out = ""
    for p in parts:
        inner = draw(balanced(depth - 1)) if depth > 0 and draw(st.booleans()) else ""
        out += p[0] + inner + p[1]
    return out


@st.composite
def corrupted(draw):
    s = draw(balanced())
    kind = draw(st.sampled_from(["drop", "insert", "swap", "flip"]))
    if not s or kind == "insert":
        k = draw(st.integers(0, len(s)))
        return s[:k] + draw(st.sampled_from("()[]{}")) + s[k:]
    k = draw(st.integers(0, len(s) - 1))
    if kind == "drop":
        return s[:k] + s[k + 1:]
    if kind == "flip":
        other = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{"}[s[k]]
        return s[:k] + other + s[k + 1:]
    j = draw(st.integers(0, len(s) - 1))
    t = list(s)
    t[k], t[j] = t[j], t[k]
    return "".join(t)


random_text = st.text(alphabet="()[]{}", max_size=12)


@prop("Properly nested, balanced strings are valid.", s=balanced())
def balanced_is_valid(f, s):
    assert f(s) is True


@prop("Strings with an odd length or a different number of openers and closers are invalid.", s=corrupted())
def unbalanced_is_invalid(f, s):
    opens = sum(s.count(c) for c in "([{")
    if len(s) % 2 == 1 or opens * 2 != len(s):
        assert f(s) is False


@prop("The result is a bool matching full validity on corrupted and random strings.", s=st.one_of(corrupted(), random_text))
def matches_definition(f, s):
    r = f(s)
    assert isinstance(r, bool)
    assert r == valid(s)


@prop("Crossed nesting of different bracket types is invalid.", s=balanced(), pair=st.permutations(PAIRS))
def crossing_invalid(f, s, pair):
    a, b = pair[0], pair[1]
    assert f(a[0] + b[0] + s + a[1] + b[1]) is False


@prop("The empty string is valid and a lone bracket is invalid.", c=st.sampled_from("()[]{}"))
def edge_cases(f, c):
    assert f("") is True
    assert f(c) is False

"""Spec for min_operations: the edit (Levenshtein) distance with unit-cost insert, remove and replace.

Domain: lowercase strings of length 0..7 (the unit tests include empty strings).
"""
from functools import lru_cache

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_operations"

CLARIFICATIONS = [
    "Either string may be empty. Return an int.",
]

words = st.one_of(st.text(alphabet="ab", max_size=7), st.text(alphabet="abcde", max_size=7))
ALPHA = "abcde"


def edit_distance(a, b):
    @lru_cache(maxsize=None)
    def d(i, j):
        if i == len(a):
            return len(b) - j
        if j == len(b):
            return len(a) - i
        return min(
            d(i + 1, j) + 1,
            d(i, j + 1) + 1,
            d(i + 1, j + 1) + (a[i] != b[j]),
        )
    return d(0, 0)


@prop("The result is an int equal to the minimum number of single-character edits.", a=words, b=words)
def matches_definition(f, a, b):
    r = f(a, b)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == edit_distance(a, b)


@prop("The result is at least the length difference and at most the longer length.", a=words, b=words)
def bounds(f, a, b):
    r = f(a, b)
    assert abs(len(a) - len(b)) <= r <= max(len(a), len(b))


@prop("The distance is symmetric.", a=words, b=words)
def symmetric(f, a, b):
    assert f(a, b) == f(b, a)


@prop("The distance is 0 exactly when the strings are equal.", a=words, b=words)
def zero_iff_equal(f, a, b):
    assert f(a, a) == 0
    assert (f(a, b) == 0) == (a == b)


@prop("A single insertion, removal or replacement gives distance 1.", a=words, data=st.data())
def single_edit(f, a, data):
    kind = data.draw(st.sampled_from(["insert", "remove", "replace"]))
    if kind == "insert" or not a:
        i = data.draw(st.integers(0, len(a)))
        b = a[:i] + data.draw(st.sampled_from(ALPHA)) + a[i:]
    elif kind == "remove":
        i = data.draw(st.integers(0, len(a) - 1))
        b = a[:i] + a[i + 1:]
    else:
        i = data.draw(st.integers(0, len(a) - 1))
        b = a[:i] + data.draw(st.sampled_from([c for c in ALPHA if c != a[i]])) + a[i + 1:]
    assert f(a, b) == 1


@prop("Transforming to or from the empty string costs the other string's length.", a=words)
def empty_string(f, a):
    assert f(a, "") == len(a)
    assert f("", a) == len(a)

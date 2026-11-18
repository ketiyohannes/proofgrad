"""Spec for flatten_nested_list: all integers of an arbitrarily nested list, in left-to-right order.

Domain: lists whose elements are integers or (recursively) such lists; empty sublists allowed.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "flatten_nested_list"

CLARIFICATIONS = [
    "Empty sublists contribute nothing; return a new flat list of the integers.",
]

ints = st.integers(-1000, 1000)
nested = st.recursive(st.lists(ints, max_size=4), lambda inner: st.lists(st.one_of(ints, inner), max_size=5), max_leaves=30)


def flat(x):
    out = []
    for item in x:
        if isinstance(item, list):
            out.extend(flat(item))
        else:
            out.append(item)
    return out


@prop("The result is a list equal to the integers of the input in left-to-right order.", xs=nested)
def matches_definition(f, xs):
    r = f(xs)
    assert isinstance(r, list)
    assert r == flat(xs)


@prop("The result contains no lists.", xs=nested)
def is_flat(f, xs):
    assert all(not isinstance(x, list) for x in f(xs))


@prop("A flat list of integers is returned unchanged.", xs=st.lists(ints, max_size=20))
def flat_unchanged(f, xs):
    assert f(xs) == xs


@prop("Flattening distributes over concatenation.", a=nested, b=nested)
def concatenation(f, a, b):
    assert f(a + b) == f(a) + f(b)


@prop("Wrapping the input in extra levels of nesting does not change the result.", xs=nested, k=st.integers(1, 6))
def deep_wrapping(f, xs, k):
    w = xs
    for _ in range(k):
        w = [w]
    assert f(w) == flat(xs)


@prop("Lists of only empty sublists give an empty list.", k=st.integers(0, 5))
def only_empties(f, k):
    assert f([[] for _ in range(k)]) == []
    assert f([[[]], [], [[[]]]]) == []

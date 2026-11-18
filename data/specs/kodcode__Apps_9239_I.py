"""Spec for findUnique: return the one integer that occurs an odd number of times (once); all others occur an even number of times.

Domain: non-empty integer lists (negatives allowed) in which exactly one value occurs once and every other value
occurs an even number of times (2 or 4, as in the examples).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "findUnique"

CLARIFICATIONS = ["Every value other than the answer occurs an even number of times (for example 2 or 4 times)."]


@st.composite
def instance(draw, lo=-10**7, hi=10**7, max_pairs=10, max_mult=2):
    vals = draw(st.lists(st.integers(lo, hi), min_size=1, max_size=max_pairs + 1, unique=True))
    unique, others = vals[0], vals[1:]
    xs = [unique]
    for v in others:
        xs += [v] * (2 * draw(st.integers(1, max_mult)))
    return unique, draw(st.permutations(xs))


@prop("Returns the value that occurs once when every other value occurs exactly twice, in any order.", case=instance())
def finds_unique_pairs(f, case):
    u, xs = case
    assert f(xs) == u


@prop("Returns the value that occurs once when other values occur two or four times.", case=instance(max_mult=2, lo=-5, hi=5))
def finds_unique_even_multiplicities(f, case):
    u, xs = case
    xs4 = list(xs) + [x for x in xs if x != u]
    assert f(xs) == u
    assert f(xs4) == u


@prop("Works with negative numbers and zero.", case=instance(lo=-1000, hi=0))
def negatives_and_zero(f, case):
    u, xs = case
    assert f(xs) == u


@prop("A single-element list returns that element.", x=st.integers(-10**9, 10**9))
def single_element(f, x):
    assert f([x]) == x


@prop("The answer is the element at either end of the list as well as in the middle.", case=instance(max_pairs=4), at_end=st.booleans())
def unique_at_ends(f, case, at_end):
    u, xs = case
    rest = [x for x in xs if x != u]
    ys = rest + [u] if at_end else [u] + rest
    assert f(ys) == u

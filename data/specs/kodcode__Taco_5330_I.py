"""Spec for find_outlier: the single element whose parity differs from all the others.

Domain: lists where all elements but exactly one share a parity and the majority has at least two
elements (so the outlier is well defined), plus one-element lists, which the unit tests cover
(the element itself is returned). Negative integers are allowed.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_outlier"

CLARIFICATIONS = [
    "For a one-element list, return that element.",
]

values = st.one_of(st.integers(-10**6, 10**6), st.integers(-5, 5))


@st.composite
def outlier_lists(draw):
    majority_even = draw(st.booleans())
    want = 0 if majority_even else 1
    majority = draw(st.lists(values.filter(lambda x: x % 2 == want), min_size=2, max_size=20))
    outlier = draw(values.filter(lambda x: x % 2 != want))
    pos = draw(st.sampled_from([0, len(majority), draw(st.integers(0, len(majority)))]))
    return majority[:pos] + [outlier] + majority[pos:], outlier


@prop("The result is the unique element of the minority parity.", case=outlier_lists())
def finds_outlier(f, case):
    xs, outlier = case
    assert f(xs) == outlier


@prop("The result is an element of the list whose parity no other element shares.", case=outlier_lists())
def result_is_unique_parity(f, case):
    xs, _ = case
    r = f(xs)
    assert r in xs
    assert sum(1 for x in xs if x % 2 == r % 2) == 1


@prop("The answer does not depend on where the outlier is placed.", case=outlier_lists(), data=st.data())
def position_invariant(f, case, data):
    xs, outlier = case
    shuffled = list(data.draw(st.permutations(xs)))
    assert f(shuffled) == outlier


@prop("An odd outlier among evens is found, including negative values.",
      evens=st.lists(st.integers(-50, 50).map(lambda x: 2 * x), min_size=2, max_size=10), odd=st.integers(-50, 50).map(lambda x: 2 * x + 1))
def odd_among_evens(f, evens, odd):
    assert f(evens + [odd]) == odd


@prop("An even outlier among odds is found, including negative values.",
      odds=st.lists(st.integers(-50, 50).map(lambda x: 2 * x + 1), min_size=2, max_size=10), even=st.integers(-50, 50).map(lambda x: 2 * x))
def even_among_odds(f, odds, even):
    assert f([even] + odds) == even


@prop("A one-element list returns its element.", x=values)
def single_element(f, x):
    assert f([x]) == x

"""Spec for max_price_difference: for each 1-based inclusive range [L, R], max price minus min price in that range.

Domain: N == len(prices) >= 1, 1 <= price <= 10^6, Q == len(queries) >= 1, each query a tuple
(L, R) with 1 <= L <= R <= N.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_price_difference"

CLARIFICATIONS = [
    "L and R are 1-based and inclusive; queries is a list of (L, R) tuples.",
    "Return a list of ints, one per query, in query order.",
]


@st.composite
def instance(draw):
    n = draw(st.integers(1, 15))
    value = draw(st.sampled_from([st.integers(1, 10**6), st.integers(1, 4)]))
    prices = draw(st.lists(value, min_size=n, max_size=n))

    def query():
        left = draw(st.integers(1, n))
        kind = draw(st.sampled_from(["any", "single", "whole", "prefix", "suffix"]))
        if kind == "single":
            return (left, left)
        if kind == "whole":
            return (1, n)
        if kind == "prefix":
            return (1, draw(st.integers(1, n)))
        if kind == "suffix":
            return (left, n)
        return (left, draw(st.integers(left, n)))

    queries = [query() for _ in range(draw(st.integers(1, 8)))]
    return n, prices, queries


def spread(prices, l, r):
    seg = prices[l - 1:r]
    return max(seg) - min(seg)


@prop("The result is a list with one int per query.", inst=instance())
def one_answer_per_query(f, inst):
    n, prices, queries = inst
    result = f(n, prices, len(queries), queries)
    assert isinstance(result, list)
    assert len(result) == len(queries)
    assert all(isinstance(r, int) for r in result)


@prop("Each answer is the maximum minus the minimum of prices[L..R] (1-based, inclusive).", inst=instance())
def matches_definition(f, inst):
    n, prices, queries = inst
    assert f(n, prices, len(queries), queries) == [spread(prices, l, r) for l, r in queries]


@prop("A single-city range gives 0.", inst=instance(), data=st.data())
def single_city_zero(f, inst, data):
    n, prices, _ = inst
    i = data.draw(st.integers(1, n))
    assert f(n, prices, 1, [(i, i)]) == [0]


@prop("Widening a range never decreases the answer.", inst=instance(), data=st.data())
def monotone_in_range(f, inst, data):
    n, prices, _ = inst
    l = data.draw(st.integers(1, n))
    r = data.draw(st.integers(l, n))
    l2 = data.draw(st.integers(1, l))
    r2 = data.draw(st.integers(r, n))
    small, big = f(n, prices, 2, [(l, r), (l2, r2)])
    assert big >= small


@prop("The whole-array range gives max(prices) - min(prices).", inst=instance())
def whole_range(f, inst):
    n, prices, _ = inst
    assert f(n, prices, 1, [(1, n)]) == [max(prices) - min(prices)]

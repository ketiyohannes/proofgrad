"""Spec for maxProfit: max of prices[j] - prices[i] over i < j, or 0 if no positive profit exists.

Domain: prices is a list (possibly empty) of non-negative integers.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "maxProfit"

CLARIFICATIONS = [
    "Return 0 for an empty list or a single day.",
]

price_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=100), max_size=20),
    st.lists(st.integers(min_value=0, max_value=3), max_size=20),
    st.lists(st.integers(min_value=0, max_value=100), max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=100), max_size=20).map(lambda xs: sorted(xs, reverse=True)),
)


def oracle(p):
    return max([0] + [p[j] - p[i] for i in range(len(p)) for j in range(i + 1, len(p))])


@prop("The result equals the best later-minus-earlier price difference, or 0 if none is positive.", prices=price_lists)
def is_best_profit(f, prices):
    assert f(prices) == oracle(prices)


@prop("The result is a non-negative int.", prices=price_lists)
def non_negative(f, prices):
    r = f(prices)
    assert isinstance(r, int) and r >= 0


@prop("Non-increasing prices give 0 profit.", prices=st.lists(st.integers(min_value=0, max_value=10**6), max_size=30))
def falling_prices(f, prices):
    assert f(sorted(prices, reverse=True)) == 0


@prop("Non-decreasing prices give last minus first.",
      prices=st.lists(st.integers(min_value=0, max_value=10**6), min_size=1, max_size=30))
def rising_prices(f, prices):
    p = sorted(prices)
    assert f(p) == p[-1] - p[0]


@prop("Empty and single-day inputs give 0; two days give max(0, second - first).",
      a=st.integers(min_value=0, max_value=10**6), b=st.integers(min_value=0, max_value=10**6))
def tiny_inputs(f, a, b):
    assert f([]) == 0
    assert f([a]) == 0
    assert f([a, b]) == max(0, b - a)


@prop("Selling must come after buying: reversing the prices gives the best earlier-minus-later difference.",
      prices=price_lists)
def direction_matters(f, prices):
    rev_best = max([0] + [prices[i] - prices[j] for i in range(len(prices)) for j in range(i + 1, len(prices))])
    assert f(prices[::-1]) == rev_best

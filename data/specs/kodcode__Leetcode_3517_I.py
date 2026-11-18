"""Spec for maxProfit: best prices[sell] - prices[buy] with buy before sell, or 0 if no profit.

Domain (from the constraints): lists of at least 2 non-negative integers <= 10^4.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "maxProfit"

prices_st = st.one_of(
    st.lists(st.integers(min_value=0, max_value=3), min_size=2, max_size=20),
    st.lists(st.integers(min_value=0, max_value=10**4), min_size=2, max_size=30),
    st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=20).map(lambda xs: sorted(xs, reverse=True)),
)


def best(prices):
    return max([0] + [prices[j] - prices[i] for i in range(len(prices)) for j in range(i + 1, len(prices))])


@prop("The result is an int equal to the best profit over all buy-before-sell day pairs (0 if none is positive).", prices=prices_st)
def matches_brute_force(f, prices):
    r = f(prices)
    assert isinstance(r, int)
    assert r == best(prices)


@prop("The sale must come after the purchase: non-increasing prices give 0.",
      prices=st.lists(st.integers(min_value=0, max_value=10**4), min_size=2, max_size=30).map(lambda xs: sorted(xs, reverse=True)))
def no_profit_when_falling(f, prices):
    assert f(prices) == 0


@prop("For non-decreasing prices, the profit is last minus first.",
      prices=st.lists(st.integers(min_value=0, max_value=10**4), min_size=2, max_size=30).map(sorted))
def rising(f, prices):
    assert f(prices) == prices[-1] - prices[0]


@prop("The minimum must precede the maximum: a later lower price does not help an earlier higher one.",
      lo=st.integers(min_value=0, max_value=100), hi=st.integers(min_value=101, max_value=10**4),
      mid=st.lists(st.integers(min_value=101, max_value=10**4), max_size=5))
def order_matters(f, lo, hi, mid):
    prices = [hi] + mid + [lo]
    assert f(prices) == best(prices)
    assert f([lo] + mid + [hi]) == max([hi] + mid) - lo


@prop("Two days give the gain if positive, else 0.", a=st.integers(min_value=0, max_value=10**4), b=st.integers(min_value=0, max_value=10**4))
def two_days(f, a, b):
    assert f([a, b]) == max(0, b - a)

"""Spec for max_units_sold_over_k_days: the maximum sum of any k consecutive entries of sales.

Domain: n == len(sales) >= 1, entries in 0..1000, 1 <= k <= n.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_units_sold_over_k_days"


@st.composite
def instances(draw):
    values = draw(st.sampled_from([st.integers(0, 1000), st.integers(0, 3), st.just(5)]))
    sales = draw(st.lists(values, min_size=1, max_size=40))
    k = draw(st.one_of(st.integers(1, len(sales)), st.sampled_from([1, len(sales)])))
    return sales, k


def windows(sales, k):
    return [sum(sales[i:i + k]) for i in range(len(sales) - k + 1)]


@prop("The result equals the largest sum over all windows of k consecutive days.", inst=instances())
def is_max_window(f, inst):
    sales, k = inst
    assert f(len(sales), sales, k) == max(windows(sales, k))


@prop("The result is at least the sum of every window of k consecutive days.", inst=instances())
def upper_bound(f, inst):
    sales, k = inst
    result = f(len(sales), sales, k)
    assert all(result >= w for w in windows(sales, k))


@prop("A window whose sum equals the result exists.", inst=instances())
def attained(f, inst):
    sales, k = inst
    assert f(len(sales), sales, k) in windows(sales, k)


@prop("With k = n the result is the total of all sales; with k = 1 it is the maximum day.",
      sales=st.lists(st.integers(0, 1000), min_size=1, max_size=40), whole=st.booleans())
def extreme_k(f, sales, whole):
    if whole:
        assert f(len(sales), sales, len(sales)) == sum(sales)
    else:
        assert f(len(sales), sales, 1) == max(sales)


@prop("A best window at the very end of the list is found.",
      prefix=st.lists(st.integers(0, 5), max_size=20), tail=st.lists(st.integers(100, 1000), min_size=1, max_size=5))
def best_at_end(f, prefix, tail):
    sales = prefix + tail
    k = len(tail)
    assert f(len(sales), sales, k) == sum(tail)

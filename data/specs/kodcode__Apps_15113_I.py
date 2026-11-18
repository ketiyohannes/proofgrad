"""Spec for highest_total_expense: the maximum, over days, of the sum of that day's expenses.

Domain: 1..10 days, each a list of 1..8 positive expenses (1..1000); separately, the unit tests' [[]] case.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "highest_total_expense"

CLARIFICATIONS = [
    "Return the maximum total as an int instead of printing it.",
    "A day with no recorded expenses has total 0 (e.g. [[]] gives 0).",
]

day = st.one_of(
    st.lists(st.integers(1, 1000), min_size=1, max_size=8),
    st.lists(st.integers(1, 3), min_size=1, max_size=8),
)
days = st.one_of(
    st.lists(day, min_size=1, max_size=10),
    day.flatmap(lambda d: st.lists(st.permutations(d).map(list), min_size=1, max_size=5)),
)


@prop("The result is an int equal to the largest daily total.", ds=days)
def matches_definition(f, ds):
    r = f(ds)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == max(sum(d) for d in ds)


@prop("The result is at least the total of every day.", ds=days)
def upper_bound(f, ds):
    r = f(ds)
    assert all(sum(d) <= r for d in ds)


@prop("The result is the total of some day.", ds=days)
def attained(f, ds):
    assert f(ds) in [sum(d) for d in ds]


@prop("Reordering days does not change the result.", ds=days, data=st.data())
def order_invariant(f, ds, data):
    assert f(list(data.draw(st.permutations(ds)))) == f(ds)


@prop("A single day returns that day's total.", d=day)
def single_day(f, d):
    assert f([d]) == sum(d)


@prop("A single day with no expenses gives 0.", dummy=st.just(None))
def empty_day(f, dummy):
    assert f([[]]) == 0

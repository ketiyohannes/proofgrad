"""Spec for calculate_maximum_bonus: per test case, the largest month-over-month increase (0 if none).

Domain: T == len(test_cases), each test case is (N, production) with N == len(production) >= 1, values 0..10**6.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "calculate_maximum_bonus"

EXCLUDE_REASON = (
    "The statement's sample output says the bonus for [10, 20, 30, 25, 35] is 15, but the reference "
    "solution and unit tests return 10 (the largest single-month increase), so the statement contradicts the reference."
)

CLARIFICATIONS = [
    "Instead of reading input, the function receives T and a list of T (N, production_list) tuples and returns a list of T ints.",
    "The bonus is the largest increase between two consecutive months; it is 0 when production never increases or N == 1.",
]


@st.composite
def case(draw):
    n = draw(st.integers(1, 12))
    vals = draw(st.one_of(
        st.lists(st.integers(0, 10**6), min_size=n, max_size=n),
        st.lists(st.integers(0, 3), min_size=n, max_size=n),
        st.lists(st.integers(0, 100), min_size=n, max_size=n).map(sorted),
        st.lists(st.integers(0, 100), min_size=n, max_size=n).map(lambda v: sorted(v, reverse=True)),
    ))
    return (n, vals)


cases = st.lists(case(), min_size=1, max_size=6)


def bonus(vals):
    return max([0] + [b - a for a, b in zip(vals, vals[1:])])


@prop("The result is a list with one int per test case.", tcs=cases)
def one_per_case(f, tcs):
    r = f(len(tcs), tcs)
    assert isinstance(r, list) and len(r) == len(tcs)


@prop("Each result equals the largest consecutive-month increase, or 0 if there is none.", tcs=cases)
def matches_definition(f, tcs):
    assert f(len(tcs), tcs) == [bonus(v) for _, v in tcs]


@prop("Non-increasing production gives a bonus of 0.",
      vals=st.lists(st.integers(0, 10**6), min_size=1, max_size=15).map(lambda v: sorted(v, reverse=True)))
def non_increasing_zero(f, vals):
    assert f(1, [(len(vals), vals)]) == [0]


@prop("A single month gives a bonus of 0.", v=st.integers(0, 10**6))
def single_month(f, v):
    assert f(1, [(1, [v])]) == [0]


@prop("Test cases are answered independently of each other.", tcs=cases)
def independent_cases(f, tcs):
    assert f(len(tcs), tcs) == [f(1, [t])[0] for t in tcs]

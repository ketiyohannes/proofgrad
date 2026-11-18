"""Spec for evaluate_submissions: "Accepted" for times <= 5000 ms, else "Disqualified", one per participant.

Domain: n == len(execution_times) >= 1, 1 <= m <= 1000 (m does not affect the result),
1 <= execution time <= 10000.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "evaluate_submissions"

CLARIFICATIONS = [
    "Return a list of strings, one per value in execution_times, in the same order (do not print).",
    "m does not affect the result.",
]

times = st.one_of(
    st.integers(1, 10000),
    st.integers(4995, 5005),
    st.sampled_from([1, 4999, 5000, 5001, 10000]),
)
time_lists = st.lists(times, min_size=1, max_size=30)
ms = st.integers(1, 1000)


def verdict(t):
    return "Accepted" if t <= 5000 else "Disqualified"


@prop("The result is a list of strings with one entry per participant.", ts=time_lists, m=ms)
def one_per_participant(f, ts, m):
    result = f(len(ts), m, ts)
    assert isinstance(result, list)
    assert len(result) == len(ts)
    assert all(isinstance(r, str) for r in result)


@prop("Each entry is 'Accepted' iff the time is at most 5000 ms, otherwise 'Disqualified'.", ts=time_lists, m=ms)
def correct_verdicts(f, ts, m):
    assert f(len(ts), m, ts) == [verdict(t) for t in ts]


@prop("Exactly 5000 ms is accepted and 5001 ms is disqualified.", m=ms)
def boundary(f, m):
    assert f(2, m, [5000, 5001]) == ["Accepted", "Disqualified"]


@prop("The number of problems m does not change the result.", ts=time_lists, m1=ms, m2=ms)
def m_irrelevant(f, ts, m1, m2):
    assert f(len(ts), m1, ts) == f(len(ts), m2, ts)

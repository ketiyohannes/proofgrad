"""Spec for max_tasks_completed: largest number of tasks whose total time fits within T.

Domain: tasks is a (possibly empty) list of positive integer durations; T is a non-negative integer.
Tasks may be chosen in any order and any subset; a total exactly equal to T is allowed.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_tasks_completed"

CLARIFICATIONS = [
    "Any subset of the tasks may be chosen; their total time must be at most T (exactly T is allowed).",
]


@st.composite
def cases(draw, max_n=8):
    tasks = draw(st.one_of(
        st.lists(st.integers(min_value=1, max_value=3), max_size=max_n),
        st.lists(st.integers(min_value=1, max_value=50), max_size=max_n),
        st.builds(lambda v, n: [v] * n, st.integers(min_value=1, max_value=5), st.integers(min_value=0, max_value=max_n)),
    ))
    mode = draw(st.sampled_from(["any", "subset_sum"]))
    if mode == "subset_sum" and tasks:
        chosen = draw(st.lists(st.sampled_from(tasks), max_size=len(tasks)))
        T = sum(chosen) + draw(st.sampled_from([-1, 0, 0, 1]))
        T = max(T, 0)
    else:
        T = draw(st.integers(min_value=0, max_value=sum(tasks) + 5))
    return tasks, T


def best_count(tasks, T):
    for k in range(len(tasks), -1, -1):
        if any(sum(c) <= T for c in combinations(tasks, k)):
            return k
    return 0


@prop("The result is an int equal to the size of the largest subset of tasks with total time at most T.", case=cases())
def matches_brute_force(f, case):
    tasks, T = case
    r = f(tasks, T)
    assert isinstance(r, int)
    assert r == best_count(tasks, T)


@prop("If the total of all tasks fits in T, every task is completed.",
      tasks=st.lists(st.integers(min_value=1, max_value=100), max_size=20), slack=st.integers(min_value=0, max_value=5))
def all_fit(f, tasks, slack):
    assert f(tasks, sum(tasks) + slack) == len(tasks)


@prop("Order of the tasks does not matter.", case=cases(), data=st.data())
def order_invariant(f, case, data):
    tasks, T = case
    assert f(list(data.draw(st.permutations(tasks))), T) == f(tasks, T)


@prop("Increasing the time limit never reduces the number of completed tasks.", case=cases(), more=st.integers(min_value=1, max_value=20))
def monotone_in_T(f, case, more):
    tasks, T = case
    assert f(tasks, T) <= f(tasks, T + more)


@prop("No tasks or a zero time limit completes nothing.",
      tasks=st.lists(st.integers(min_value=1, max_value=100), max_size=10), T=st.integers(min_value=0, max_value=100))
def degenerate(f, tasks, T):
    assert f([], T) == 0
    assert f(tasks, 0) == 0

"""Spec for calculate_total_time_in_building: per-employee total of (exit - enter) over all visits.

Domain: logs are listed in chronological order (non-decreasing timestamps). Each employee's
events alternate enter, exit, enter, exit, ... starting with enter and ending with exit.
Employee ids are short strings. Timestamps are non-negative integers.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "calculate_total_time_in_building"

CLARIFICATIONS = [
    "Logs are given in chronological order, and every employee's last action is 'exit'.",
    "Return a dict mapping each employee_id that appears in the logs to their total time; return {} for no logs.",
]

IDS = ["A", "B", "C", "D", "E"]


@st.composite
def logs_strategy(draw, max_employees=4, max_visits=3):
    employees = draw(st.lists(st.sampled_from(IDS), unique=True, max_size=max_employees))
    stamps = []
    for emp in employees:
        visits = draw(st.integers(min_value=1, max_value=max_visits))
        times = draw(st.lists(st.integers(min_value=0, max_value=60), min_size=2 * visits, max_size=2 * visits))
        stamps.extend((t, emp) for t in times)
    # Chronological order with a random order among equal timestamps.
    rnd = draw(st.randoms(use_true_random=False))
    rnd.shuffle(stamps)
    stamps.sort(key=lambda e: e[0])
    # Each employee's events alternate enter/exit in order of appearance.
    seen = {}
    logs = []
    for t, emp in stamps:
        k = seen.get(emp, 0)
        seen[emp] = k + 1
        logs.append((t, emp, "enter" if k % 2 == 0 else "exit"))
    return logs


def oracle(logs):
    totals, open_since = {}, {}
    for t, emp, action in logs:
        if action == "enter":
            open_since[emp] = t
        else:
            totals[emp] = totals.get(emp, 0) + t - open_since.pop(emp)
    return totals


@prop("Each employee's value is the sum of exit minus enter over all of their visits.", logs=logs_strategy())
def totals_correct(f, logs):
    r = f(logs)
    expected = oracle(logs)
    for emp, total in expected.items():
        assert r[emp] == total


@prop("The result is a dict whose keys are exactly the employees appearing in the logs.", logs=logs_strategy())
def keys_are_employees(f, logs):
    r = f(logs)
    assert isinstance(r, dict)
    assert set(r) == {emp for _, emp, _ in logs}


@prop("An employee with a single visit gets exit minus enter, including 0 for a zero-length visit.",
      emp=st.sampled_from(IDS), t=st.integers(min_value=0, max_value=86400), d=st.integers(min_value=0, max_value=1000))
def single_visit(f, emp, t, d):
    assert f([(t, emp, "enter"), (t + d, emp, "exit")]) == {emp: d}


@prop("No logs give an empty dict.", dummy=st.just(None))
def no_logs(f, dummy):
    assert f([]) == {}


@prop("Shifting every timestamp by the same amount does not change the totals.",
      logs=logs_strategy(), shift=st.integers(min_value=1, max_value=1000))
def shift_invariant(f, logs, shift):
    shifted = [(t + shift, emp, a) for t, emp, a in logs]
    assert f(shifted) == f(logs)

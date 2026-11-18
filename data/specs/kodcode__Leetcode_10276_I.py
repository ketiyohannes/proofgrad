"""Spec for scheduleProcesses: process ids ordered by burst time, then arrival time, then id.

Domain: a non-empty list of (id, arrivalTime, burstTime) tuples with distinct non-negative integer ids and
non-negative times. Following the reference and unit tests, all processes are ordered at once (a process is
not delayed until it has arrived); arrival time only breaks ties.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "scheduleProcesses"

CLARIFICATIONS = [
    "Treat every process as available from the start: order all of them by burst time, using arrival time and then id only to break ties.",
    "Process ids are distinct; return a list of ids.",
]


@st.composite
def processes(draw, min_size=1):
    n = draw(st.integers(min_size, 10))
    ids = draw(st.lists(st.integers(0, 50), min_size=n, max_size=n, unique=True))
    small = draw(st.booleans())
    hi = 2 if small else 20
    procs = [(i, draw(st.integers(0, hi)), draw(st.integers(1, hi + 1))) for i in ids]
    return procs


def position(order, pid):
    return order.index(pid)


@prop("The result is a list containing every process id exactly once.", procs=processes())
def is_permutation_of_ids(f, procs):
    r = f(procs)
    assert isinstance(r, list)
    assert sorted(r) == sorted(p[0] for p in procs)


@prop("A process with a shorter burst time is scheduled before one with a longer burst time.", procs=processes(2))
def shorter_burst_first(f, procs):
    r = f(procs)
    for a in procs:
        for b in procs:
            if a[2] < b[2]:
                assert position(r, a[0]) < position(r, b[0])


@prop("Among equal burst times, the earlier arrival is scheduled first.", procs=processes(2))
def earlier_arrival_breaks_ties(f, procs):
    r = f(procs)
    for a in procs:
        for b in procs:
            if a[2] == b[2] and a[1] < b[1]:
                assert position(r, a[0]) < position(r, b[0])


@prop("Among equal burst and arrival times, the smaller id is scheduled first.", procs=processes(2))
def smaller_id_breaks_ties(f, procs):
    r = f(procs)
    for a in procs:
        for b in procs:
            if a[2] == b[2] and a[1] == b[1] and a[0] < b[0]:
                assert position(r, a[0]) < position(r, b[0])


@prop("A single process is returned alone, and a process that arrives later but is shorter still runs first.",
      pid=st.integers(0, 50), arr=st.integers(0, 20), burst=st.integers(1, 20))
def single_and_late_short(f, pid, arr, burst):
    assert f([(pid, arr, burst)]) == [pid]
    assert f([(pid, 0, burst + 1), (pid + 1, arr + 1, burst)]) == [pid + 1, pid]

"""Spec for optimize_cycling_log: per test case, merge runs of equal consecutive distances into their sum, formatted "Case #i: ...".

Domain: a list of (N, distances) tuples with N == len(distances), distances in 1..100; N may be 0 (unit tests).
"""
from itertools import groupby

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "optimize_cycling_log"

CLARIFICATIONS = [
    "test_cases is a list of (N, distances) tuples; return a list of strings, one per test case, in order.",
    "Format each line as \"Case #i: \" (i starting at 1) followed by the merged distances separated by single spaces, with no trailing space.",
    "A test case with no segments (N = 0) gives \"Case #i:\" with nothing after the colon.",
]


@st.composite
def log(draw, min_size=1):
    shape = draw(st.sampled_from(["random", "few", "equal", "runs"]))
    if shape == "random":
        return draw(st.lists(st.integers(1, 100), min_size=min_size, max_size=20))
    if shape == "few":
        return draw(st.lists(st.integers(1, 3), min_size=min_size, max_size=20))
    if shape == "equal":
        return [draw(st.integers(1, 100))] * draw(st.integers(max(1, min_size), 15))
    runs = draw(st.lists(st.tuples(st.integers(1, 5), st.integers(1, 4)), min_size=1, max_size=6))
    return [v for v, k in runs for _ in range(k)]


def expected_line(i, d):
    merged = [sum(g) for _, g in groupby(d)]
    return f"Case #{i}:" + "".join(f" {x}" for x in merged)


def cases(logs):
    return [(len(d), d) for d in logs]


@prop("Each line equals the case header followed by the sums of the maximal runs of equal consecutive distances.",
      logs=st.lists(log(), min_size=1, max_size=4))
def matches_run_merging(f, logs):
    assert f(cases(logs)) == [expected_line(i + 1, d) for i, d in enumerate(logs)]


@prop("The result is a list with one string per test case, numbered 'Case #1:', 'Case #2:', ... in order.",
      logs=st.lists(log(), min_size=1, max_size=6))
def numbered_lines(f, logs):
    r = f(cases(logs))
    assert isinstance(r, list) and len(r) == len(logs)
    for i, line in enumerate(r):
        assert isinstance(line, str) and line.startswith(f"Case #{i + 1}:")


@prop("Merging preserves the total distance of each case.", logs=st.lists(log(), min_size=1, max_size=4))
def total_preserved(f, logs):
    for line, d in zip(f(cases(logs)), logs):
        assert sum(int(x) for x in line.split(":", 1)[1].split()) == sum(d)


@prop("A log with no two equal neighbours is printed unchanged.", d=st.lists(st.integers(1, 100), min_size=1, max_size=20))
def no_runs_unchanged(f, d):
    d = [x for i, x in enumerate(d) if i == 0 or x != d[i - 1]]
    assert f([(len(d), d)]) == ["Case #1: " + " ".join(map(str, d))]


@prop("A run of equal distances collapses to one number; an empty log gives 'Case #i:' with nothing after the colon.",
      x=st.integers(1, 100), n=st.integers(1, 20), before=st.lists(log(), max_size=2))
def equal_and_empty(f, x, n, before):
    k = len(before) + 1
    r = f(cases(before) + [(n, [x] * n), (0, [])])
    assert r[-2] == f"Case #{k}: {x * n}"
    assert r[-1] == f"Case #{k + 1}:"

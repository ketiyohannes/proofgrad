"""Spec for process_registrations: per test case (N, K), the number of complete groups of size K and the leftover participants.

Domain: T == len(registrations) >= 1, 1 <= N <= 100000, 1 <= K <= 1000.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "process_registrations"

CLARIFICATIONS = [
    "registrations is a list of T (N, K) tuples.",
    "Return a list with one (groups, leftover) tuple of ints per test case, in input order.",
]

pair = st.one_of(
    st.tuples(st.integers(1, 100000), st.integers(1, 1000)),
    st.tuples(st.integers(1, 30), st.integers(1, 10)),
    st.integers(1, 1000).flatmap(lambda k: st.tuples(st.integers(1, 100).map(lambda m: m * k), st.just(k))),
)
batch = st.lists(pair, min_size=1, max_size=8)


@prop("The result is a list of T tuples, each holding two ints.", regs=batch)
def output_shape(f, regs):
    r = f(len(regs), regs)
    assert isinstance(r, list) and len(r) == len(regs)
    for item in r:
        assert isinstance(item, tuple) and len(item) == 2
        assert all(isinstance(x, int) for x in item)


@prop("groups * K + leftover == N for every test case.", regs=batch)
def accounts_for_everyone(f, regs):
    for (g, rest), (n, k) in zip(f(len(regs), regs), regs):
        assert g * k + rest == n


@prop("The leftover is smaller than the group size and never negative (all complete groups are formed).", regs=batch)
def leftover_too_small_for_group(f, regs):
    for (g, rest), (n, k) in zip(f(len(regs), regs), regs):
        assert 0 <= rest < k
        assert g >= 0


@prop("When K exceeds N no group forms and everyone is left over; with K = 1 everyone is grouped.", n=st.integers(1, 999), extra=st.integers(1, 100))
def edge_group_sizes(f, n, extra):
    assert f(1, [(n, n + extra)]) == [(0, n)]
    assert f(1, [(n, 1)]) == [(n, 0)]
    assert f(1, [(n, n)]) == [(1, 0)]


@prop("Answers are given per test case, in input order.", regs=batch)
def per_case_order(f, regs):
    r = f(len(regs), regs)
    assert r == [f(1, [p])[0] for p in regs]
    assert f(len(regs), regs[::-1]) == r[::-1]

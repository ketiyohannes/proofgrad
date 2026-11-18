"""Spec for find_groupings: every non-empty subset of friends 1..n, each listed once.

Domain: 0 <= n <= 8. Output order (from the reference and unit tests): groups by increasing size,
groups of equal size in lexicographic order, IDs within a group increasing.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_groupings"

CLARIFICATIONS = [
    "Return a list of lists; list the IDs inside each group in increasing order.",
    "Order the groups by increasing size, and groups of the same size lexicographically (e.g. for n = 3: [[1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]); the example ordering in the statement is only illustrative.",
    "Return [] for n = 0.",
]

sizes = st.integers(0, 8)


@prop("The groups are exactly the non-empty subsets of 1..n, ignoring order.", n=sizes)
def correct_subsets(f, n):
    r = f(n)
    got = {frozenset(g) for g in r}
    want = {frozenset(c) for k in range(1, n + 1) for c in combinations(range(1, n + 1), k)}
    assert got == want


@prop("No group is repeated, the result has 2**n - 1 groups and every group is a list.", n=sizes)
def no_duplicates(f, n):
    r = f(n)
    assert isinstance(r, list) and all(isinstance(g, list) for g in r)
    assert len(r) == 2 ** n - 1
    assert len({frozenset(g) for g in r}) == len(r)
    assert all(len(set(g)) == len(g) for g in r)


@prop("IDs inside every group are in increasing order.", n=sizes)
def groups_sorted(f, n):
    assert all(list(g) == sorted(g) for g in f(n))


@prop("Groups are ordered by size, then lexicographically.", n=sizes)
def groups_ordered(f, n):
    keys = [(len(g), list(g)) for g in f(n)]
    assert keys == sorted(keys)


@prop("n = 0 gives [] and n = 1 gives [[1]].", dummy=st.just(None))
def small_cases(f, dummy):
    assert f(0) == []
    assert f(1) == [[1]]

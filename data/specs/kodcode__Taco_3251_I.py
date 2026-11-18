"""Spec for reorder_sequence: for each query, alternately take the next smallest and next largest remaining element.

Domain: queries is a list of tuples (N, sequence) with N == len(sequence) >= 0. Every sequence is
given in non-decreasing order (as in all samples and unit tests), so taking from the left end is
the same as taking the smallest remaining number and from the right end the largest. Values are
positive integers. The unit tests include an empty sequence (0, []).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "reorder_sequence"

CLARIFICATIONS = [
    "Each query's sequence is given in non-decreasing order.",
    "queries is a list of tuples (N, sequence); return a list containing one reordered list per query, in input order.",
    "An empty sequence (N = 0) yields an empty list.",
]

sequences = st.one_of(
    st.lists(st.integers(1, 10**9), max_size=25),
    st.lists(st.integers(1, 4), max_size=25),
    st.lists(st.integers(1, 10**9), min_size=1, max_size=2),
).map(sorted)
queries = st.lists(sequences.map(lambda s: (len(s), s)), min_size=1, max_size=5)


def alternate(seq):
    """Take from the remaining pool: smallest, largest, smallest, ... until empty."""
    pool = list(seq)
    out = []
    take_small = True
    while pool:
        out.append(pool.pop(pool.index(min(pool)) if take_small else len(pool) - 1 - pool[::-1].index(max(pool))))
        take_small = not take_small
    return out


@prop("The result is a list with one list per query.", queries=queries)
def one_list_per_query(f, queries):
    result = f(len(queries), queries)
    assert isinstance(result, list)
    assert len(result) == len(queries)
    assert all(isinstance(r, list) for r in result)


@prop("Each reordered sequence is a permutation of its input.", queries=queries)
def is_permutation(f, queries):
    for (_, seq), r in zip(queries, f(len(queries), queries)):
        assert sorted(r) == sorted(seq)


@prop("Each reordered sequence alternates smallest remaining, largest remaining, starting with the smallest.", queries=queries)
def alternates_min_max(f, queries):
    assert f(len(queries), queries) == [alternate(seq) for _, seq in queries]


@prop("The first element is the minimum and the second (if any) is the maximum.", seq=sequences.filter(len))
def starts_min_then_max(f, seq):
    (r,) = f(1, [(len(seq), seq)])
    assert r[0] == min(seq)
    if len(seq) > 1:
        assert r[1] == max(seq)


@prop("Queries are answered independently: each query alone gives the same result as within the batch.", queries=queries)
def queries_independent(f, queries):
    batch = f(len(queries), queries)
    assert batch == [f(1, [q])[0] for q in queries]


@prop("An empty sequence gives an empty list.", extra=st.lists(sequences.map(lambda s: (len(s), s)), max_size=2))
def empty_sequence(f, extra):
    result = f(1 + len(extra), [(0, [])] + extra)
    assert result[0] == []

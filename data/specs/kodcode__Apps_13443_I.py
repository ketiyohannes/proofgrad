"""Spec for distinctCharacters: for each (left, right) query, the number of distinct characters in s[left..right].

Domain: non-empty lowercase strings, 1..15 queries with 0 <= left <= right < len(s).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "distinctCharacters"

CLARIFICATIONS = [
    "Return a list of ints, one per query, in the same order as the queries.",
]


@st.composite
def cases(draw):
    s = draw(st.one_of(
        st.text(alphabet="abc", min_size=1, max_size=30),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=30),
        st.text(alphabet="a", min_size=1, max_size=10),
    ))
    n = len(s)
    q = st.integers(0, n - 1).flatmap(lambda l: st.tuples(st.just(l), st.integers(l, n - 1)))
    edge = st.sampled_from([(0, n - 1), (0, 0), (n - 1, n - 1)])
    queries = draw(st.lists(st.one_of(q, edge), min_size=1, max_size=15))
    return s, queries


@prop("The result is a list with one entry per query.", case=cases())
def one_per_query(f, case):
    s, queries = case
    r = f(s, queries)
    assert isinstance(r, list) and len(r) == len(queries)


@prop("Each entry equals the number of distinct characters in s[left..right], right inclusive.", case=cases())
def matches_definition(f, case):
    s, queries = case
    assert f(s, queries) == [len(set(s[l:r + 1])) for l, r in queries]


@prop("A query with left == right gives 1.", case=cases())
def single_char_query(f, case):
    s, _ = case
    queries = [(i, i) for i in range(len(s))]
    assert f(s, queries) == [1] * len(s)


@prop("Answering queries one at a time gives the same results as answering them together.", case=cases())
def queries_independent(f, case):
    s, queries = case
    assert f(s, queries) == [f(s, [q])[0] for q in queries]


@prop("A string of all distinct letters gives right - left + 1 for each query.",
      letters=st.permutations("abcdefghijklmnopqrstuvwxyz"), data=st.data())
def all_distinct(f, letters, data):
    s = "".join(letters[: data.draw(st.integers(1, 26))])
    n = len(s)
    queries = data.draw(st.lists(st.integers(0, n - 1).flatmap(lambda l: st.tuples(st.just(l), st.integers(l, n - 1))),
                                 min_size=1, max_size=10))
    assert f(s, queries) == [r - l + 1 for l, r in queries]

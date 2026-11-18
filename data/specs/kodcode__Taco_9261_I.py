"""Spec for unique_stones: per test case, the number of brilliance values that occur exactly once.

Domain: T == len(test_cases) >= 1; each test case is a tuple (N, B) with N == len(B) >= 1 and
0 <= B[i] <= 100000.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "unique_stones"

CLARIFICATIONS = [
    "test_cases is a list of tuples (N, B); return a list of ints, one answer per test case, in input order.",
]

values = st.one_of(
    st.lists(st.integers(0, 100000), min_size=1, max_size=30),
    st.lists(st.integers(0, 4), min_size=1, max_size=30),
    st.builds(lambda v, k: [v] * k, st.integers(0, 100000), st.integers(1, 10)),
    st.lists(st.integers(0, 100000), min_size=1, max_size=30, unique=True),
)
cases = st.lists(values.map(lambda b: (len(b), b)), min_size=1, max_size=5)


def singletons(b):
    return sum(1 for v in set(b) if b.count(v) == 1)


@prop("The result is a list with one int per test case.", cases=cases)
def one_answer_per_case(f, cases):
    result = f(len(cases), cases)
    assert isinstance(result, list)
    assert len(result) == len(cases)
    assert all(isinstance(r, int) for r in result)


@prop("Each answer is the number of values occurring exactly once.", cases=cases)
def matches_definition(f, cases):
    assert f(len(cases), cases) == [singletons(b) for _, b in cases]


@prop("All-distinct values keep every stone.", b=st.lists(st.integers(0, 100000), min_size=1, max_size=40, unique=True))
def all_distinct(f, b):
    assert f(1, [(len(b), b)]) == [len(b)]


@prop("Doubling every stone leaves none unique.", b=values)
def doubled_none(f, b):
    d = b + b
    assert f(1, [(len(d), d)]) == [0]


@prop("A value occurring two or more times is not unique; a value occurring once is.", v=st.integers(0, 100000), k=st.integers(2, 10))
def repeated_not_unique(f, v, k):
    assert f(1, [(k, [v] * k)]) == [0]
    assert f(1, [(k + 1, [v] * k + [v + 1])]) == [1]

"""Spec for max_candles_blown_out: for each test case, the number of candles of maximum height.

Domain: T == len(test_cases) >= 1; each test case is a tuple (N, heights) with N == len(heights) >= 1
and 1 <= heights[i] <= 10000.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_candles_blown_out"

CLARIFICATIONS = [
    "test_cases is a list of tuples (N, heights); return a list of ints, one answer per test case, in input order.",
]

heights = st.one_of(
    st.lists(st.integers(1, 10000), min_size=1, max_size=30),
    st.lists(st.integers(1, 3), min_size=1, max_size=30),
    st.builds(lambda h, k: [h] * k, st.integers(1, 10000), st.integers(1, 20)),
    st.lists(st.integers(1, 10000), min_size=1, max_size=30).map(sorted),
    st.lists(st.integers(1, 10000), min_size=1, max_size=30).map(lambda xs: sorted(xs, reverse=True)),
)
cases = st.lists(heights.map(lambda hs: (len(hs), hs)), min_size=1, max_size=6)


def tallest_count(hs):
    tallest = max(hs)
    return sum(1 for h in hs if h == tallest)


@prop("The result is a list with one int per test case.", cases=cases)
def one_answer_per_case(f, cases):
    result = f(len(cases), cases)
    assert isinstance(result, list)
    assert len(result) == len(cases)
    assert all(isinstance(r, int) for r in result)


@prop("Each answer equals the number of candles having the maximum height.", cases=cases)
def counts_tallest(f, cases):
    assert f(len(cases), cases) == [tallest_count(hs) for _, hs in cases]


@prop("Each answer is between 1 and N.", cases=cases)
def answer_in_range(f, cases):
    for (n, _), r in zip(cases, f(len(cases), cases)):
        assert 1 <= r <= n


@prop("Adding a candle taller than all others makes the answer 1.", hs=heights)
def new_tallest_gives_one(f, hs):
    taller = hs + [max(hs) + 1]
    assert f(1, [(len(taller), taller)]) == [1]


@prop("A test case with all candles of equal height answers N.", h=st.integers(1, 10000), n=st.integers(1, 30))
def all_equal(f, h, n):
    assert f(1, [(n, [h] * n)]) == [n]

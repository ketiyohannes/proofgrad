"""Spec for sumOfDistinctElements: per query, the sum of the distinct values >= d in nums[l..r] (1-based, inclusive).

Domain: 1 <= nums[i] <= 1000, 1 <= d <= 1000, queries is a list (possibly empty, as in the unit
tests) of tuples (l, r) with 1 <= l <= r <= len(nums). The statement's example outputs contain
arithmetic slips (19 and 18); its own explanations and the unit tests give 20 and 15.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "sumOfDistinctElements"

CLARIFICATIONS = [
    "Queries use 1-based inclusive indices: query (l, r) covers nums[l-1], ..., nums[r-1].",
    "Each distinct value is added once, however often it occurs in the range; return 0 if no value qualifies.",
    "The correct outputs for the examples are {12, 20} and {9, 15, 15}.",
    "Return a list of ints, one per query, in query order (an empty list for no queries).",
]


@st.composite
def instance(draw):
    n = draw(st.integers(1, 15))
    value = draw(st.sampled_from([st.integers(1, 1000), st.integers(1, 6)]))
    nums = draw(st.lists(value, min_size=n, max_size=n))
    d = draw(st.one_of(st.sampled_from(nums), st.integers(1, 1000), st.integers(1, 7)))

    def query():
        left = draw(st.integers(1, n))
        kind = draw(st.sampled_from(["any", "single", "whole"]))
        if kind == "single":
            return (left, left)
        if kind == "whole":
            return (1, n)
        return (left, draw(st.integers(left, n)))

    queries = [query() for _ in range(draw(st.integers(0, 6)))]
    return nums, d, queries


def answer(nums, d, l, r):
    seen = []
    for x in nums[l - 1:r]:
        if x >= d and x not in seen:
            seen.append(x)
    return sum(seen)


@prop("The result is a list with one int per query.", inst=instance())
def one_answer_per_query(f, inst):
    nums, d, queries = inst
    result = f(nums, d, queries)
    assert isinstance(result, list)
    assert len(result) == len(queries)
    assert all(isinstance(r, int) for r in result)


@prop("Each answer is the sum of the distinct values >= d in the 1-based inclusive range.", inst=instance())
def matches_definition(f, inst):
    nums, d, queries = inst
    assert f(nums, d, queries) == [answer(nums, d, l, r) for l, r in queries]


@prop("Values equal to d are included and values just below d are excluded.", v=st.integers(2, 1000), k=st.integers(1, 5))
def threshold_inclusive(f, v, k):
    nums = [v] * k + [v - 1]
    assert f(nums, v, [(1, k + 1)]) == [v]


@prop("Repeated values are counted once.", v=st.integers(1, 1000), k=st.integers(1, 10))
def duplicates_once(f, v, k):
    assert f([v] * k, 1, [(1, k)]) == [v]


@prop("If d exceeds every value, every answer is 0.", inst=instance())
def all_below_threshold(f, inst):
    nums, _, queries = inst
    assert f(nums, max(nums) + 1, queries) == [0] * len(queries)


@prop("No queries give an empty list.", inst=instance())
def no_queries(f, inst):
    nums, d, _ = inst
    assert f(nums, d, []) == []

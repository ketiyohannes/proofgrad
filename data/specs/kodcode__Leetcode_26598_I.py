"""Spec for find_disappeared_numbers: integers in [1, n] that do not occur in nums (n = len(nums)), ascending.

Domain: lists of length n (0..30) whose elements lie in [1, n].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_disappeared_numbers"

CLARIFICATIONS = [
    "Return the missing numbers as a list in increasing order; return [] for an empty array.",
    "Elements may appear more than twice.",
]


@st.composite
def arrays(draw):
    n = draw(st.integers(0, 30))
    if n == 0:
        return []
    shape = draw(st.sampled_from(["random", "perm", "few", "const"]))
    if shape == "perm":
        return list(draw(st.permutations(list(range(1, n + 1)))))
    if shape == "few":
        vals = draw(st.lists(st.integers(1, n), min_size=1, max_size=3))
        return draw(st.lists(st.sampled_from(vals), min_size=n, max_size=n))
    if shape == "const":
        return [draw(st.integers(1, n))] * n
    return draw(st.lists(st.integers(1, n), min_size=n, max_size=n))


@prop("The result is a list equal to the numbers in [1, n] absent from nums, in increasing order.", nums=arrays())
def matches_definition(f, nums):
    r = f(nums)
    assert isinstance(r, list)
    assert r == [v for v in range(1, len(nums) + 1) if v not in nums]


@prop("No returned number occurs in nums and every number lies in [1, n].", nums=arrays())
def returned_are_missing(f, nums):
    r = f(nums)
    assert all(1 <= v <= len(nums) and v not in nums for v in r)


@prop("Every number in [1, n] absent from nums is returned.", nums=arrays())
def all_missing_returned(f, nums):
    r = set(f(nums))
    assert all(v in r for v in range(1, len(nums) + 1) if v not in nums)


@prop("The result is strictly increasing (sorted, no duplicates).", nums=arrays())
def sorted_unique(f, nums):
    r = f(nums)
    assert all(a < b for a, b in zip(r, r[1:]))


@prop("A permutation of 1..n gives []; an empty array gives [].", n=st.integers(0, 20), data=st.data())
def permutation_empty(f, n, data):
    nums = list(data.draw(st.permutations(list(range(1, n + 1)))))
    assert f(nums) == []
    assert f([]) == []

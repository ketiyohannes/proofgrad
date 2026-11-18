"""Spec for rearrange_list: an ordering of nums with every adjacent difference <= k, else [].

Domain: nums is a list (possibly empty) of non-negative integers, duplicates allowed; k is a non-negative integer.
"""
from itertools import permutations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "rearrange_list"

CLARIFICATIONS = [
    "When a valid arrangement exists, return the elements sorted in non-decreasing order.",
    "Return an empty list for an empty input or when no valid arrangement exists.",
]


@st.composite
def case(draw, max_len=6):
    nums = draw(st.one_of(
        st.lists(st.integers(min_value=0, max_value=20), max_size=max_len),
        st.lists(st.integers(min_value=0, max_value=5), max_size=max_len),
        st.lists(st.integers(min_value=0, max_value=100), max_size=max_len),
    ))
    gaps = [b - a for a, b in zip(sorted(nums), sorted(nums)[1:])]
    k = draw(st.one_of(st.integers(min_value=0, max_value=30),
                       st.sampled_from(gaps or [0]).flatmap(lambda g: st.sampled_from([g, max(g - 1, 0)]))))
    return nums, k


def feasible(nums, k):
    return len(nums) <= 1 or any(all(abs(a - b) <= k for a, b in zip(p, p[1:])) for p in permutations(nums))


@prop("A non-empty result is a rearrangement (same multiset) of the input.", c=case(max_len=12))
def is_permutation(f, c):
    nums, k = c
    r = f(nums, k)
    if r:
        assert sorted(r) == sorted(nums)


@prop("Every pair of consecutive elements in the result differs by at most k.", c=case(max_len=12))
def adjacent_within_k(f, c):
    nums, k = c
    r = f(nums, k)
    assert all(abs(a - b) <= k for a, b in zip(r, r[1:]))


@prop("The result is non-empty exactly when some ordering of the input satisfies the condition.", c=case())
def empty_iff_impossible(f, c):
    nums, k = c
    r = f(nums, k)
    assert isinstance(r, list)
    assert (len(r) > 0) == (len(nums) > 0 and feasible(nums, k))


@prop("When an arrangement exists, the returned list is sorted in non-decreasing order.", c=case(max_len=12))
def sorted_when_possible(f, c):
    nums, k = c
    r = f(nums, k)
    if r:
        assert r == sorted(nums)


@prop("An empty list gives [] and a single element is returned as a one-element list.",
      x=st.integers(min_value=0, max_value=100), k=st.integers(min_value=0, max_value=10))
def tiny_inputs(f, x, k):
    assert f([], k) == []
    assert f([x], k) == [x]

"""Spec for four_sum: all distinct value-quadruplets (each sorted ascending) drawn from distinct positions of nums that sum to target, listed in ascending lexicographic order.

Domain: lists of 0..10 small integers (including the empty list and lists with heavy duplication) and small targets.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "four_sum"

CLARIFICATIONS = [
    "Each quadruplet uses four different positions of nums, so a value can appear in a quadruplet at most as often as it occurs in nums.",
    "Return a list of lists; each quadruplet is sorted ascending and the quadruplets are sorted in ascending lexicographic order.",
    "Return [] when nums has fewer than four elements or no quadruplet sums to target.",
]

# Mix general lists with lists drawn from very few distinct values (including all-equal lists),
# where duplicate handling is most error-prone.
nums_strategy = st.one_of(
    st.lists(st.integers(min_value=-6, max_value=6), max_size=10),
    st.lists(st.integers(min_value=-3, max_value=3), min_size=1, max_size=3, unique=True).flatmap(
        lambda pool: st.lists(st.sampled_from(pool), max_size=10)
    ),
    st.lists(st.integers(min_value=-6, max_value=6), max_size=10).map(sorted),
)


@st.composite
def nums_and_target(draw):
    nums = draw(nums_strategy)
    if len(nums) >= 4 and draw(st.booleans()):
        idx = draw(st.lists(st.integers(0, len(nums) - 1), min_size=4, max_size=4, unique=True))
        target = sum(nums[i] for i in idx)
    else:
        target = draw(st.integers(min_value=-15, max_value=15))
    return nums, target


def brute(nums, target):
    return {tuple(sorted(c)) for c in combinations(nums, 4) if sum(c) == target}


def uses_available_values(quad, nums):
    pool = list(nums)
    for x in quad:
        if x not in pool:
            return False
        pool.remove(x)
    return True


@prop("The result is a list whose items are lists.", case=nums_and_target())
def returns_list_of_lists(f, case):
    out = f(*case)
    assert isinstance(out, list)
    assert all(isinstance(q, list) for q in out)


@prop("Every returned quadruplet has four elements that sum to the target.", case=nums_and_target())
def quadruplets_sum_to_target(f, case):
    nums, target = case
    for q in f(nums, target):
        assert len(q) == 4 and sum(q) == target


@prop("Every returned quadruplet is sorted in ascending order.", case=nums_and_target())
def quadruplets_sorted(f, case):
    for q in f(*case):
        assert list(q) == sorted(q)


@prop("Every returned quadruplet uses values available in the input (respecting multiplicity).", case=nums_and_target())
def uses_input_values(f, case):
    nums, target = case
    for q in f(nums, target):
        assert uses_available_values(q, nums)


@prop("No quadruplet is listed twice.", case=nums_and_target())
def no_duplicates(f, case):
    out = [tuple(q) for q in f(*case)]
    assert len(out) == len(set(out))


@prop("Every valid quadruplet is found: the set of returned quadruplets equals a brute-force enumeration.",
      case=nums_and_target())
def complete(f, case):
    nums, target = case
    assert {tuple(sorted(q)) for q in f(nums, target)} == brute(nums, target)


@prop("The quadruplets are listed in ascending lexicographic order.", case=nums_and_target())
def ordered(f, case):
    out = [list(q) for q in f(*case)]
    assert out == sorted(out)


@prop("Lists with fewer than four elements give [].", nums=st.lists(st.integers(-6, 6), max_size=3),
      target=st.integers(-15, 15))
def short_input_empty(f, nums, target):
    assert f(nums, target) == []

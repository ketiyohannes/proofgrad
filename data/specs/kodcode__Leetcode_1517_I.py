"""Spec for rob: maximum total of a set of houses with no two adjacent houses chosen.

Domain: nums is a (possibly empty) list of non-negative integer amounts; negative amounts
are not generated. An empty street gives 0, following the unit tests.
"""
from itertools import product

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "rob"

CLARIFICATIONS = [
    "All amounts are non-negative integers.",
    "Return 0 if there are no houses.",
    "Return the total as an int.",
]

money = st.integers(min_value=0, max_value=1000)

houses = st.one_of(
    st.lists(money, min_size=0, max_size=12),
    st.lists(st.sampled_from([0, 1, 100]), min_size=0, max_size=12),
    st.builds(lambda x, n: [x] * n, money, st.integers(min_value=0, max_value=12)),
    st.lists(money, min_size=0, max_size=12).map(sorted),
    st.lists(money, min_size=0, max_size=12).map(lambda xs: sorted(xs, reverse=True)),
)


def best_by_enumeration(nums):
    best = 0
    for picks in product((False, True), repeat=len(nums)):
        if any(picks[i] and picks[i + 1] for i in range(len(nums) - 1)):
            continue
        best = max(best, sum(x for x, p in zip(nums, picks) if p))
    return best


@prop("The result is an int equal to the best total over all non-adjacent selections of houses.", nums=houses)
def matches_enumeration(f, nums):
    result = f(nums)
    assert isinstance(result, int)
    assert result == best_by_enumeration(nums)


@prop("A street with no houses gives 0.", unused=st.just(None))
def empty_street(f, unused):
    assert f([]) == 0


@prop("One house gives its value, and two houses give the larger value.", a=money, b=money)
def one_or_two_houses(f, a, b):
    assert f([a]) == a
    assert f([a, b]) == max(a, b)


@prop("The result is at least the largest house and at least the sum of the even-indexed or odd-indexed houses.",
      nums=st.lists(money, min_size=1, max_size=40))
def lower_bounds(f, nums):
    r = f(nums)
    assert r >= max(nums)
    assert r >= sum(nums[0::2]) and r >= sum(nums[1::2])


@prop("Reversing the street does not change the answer.", nums=houses)
def reversal_invariant(f, nums):
    assert f(nums) == f(nums[::-1])


@prop("Adding a house at the end never decreases the answer.", nums=houses, extra=money)
def monotone_in_houses(f, nums, extra):
    assert f(nums + [extra]) >= f(nums)

"""Spec for can_complete_circuit: smallest start index from which one full circular trip is possible, else -1.

Domain: nums and cost are non-empty lists of the same length holding non-negative integers.
Trip model: at each position i you first add nums[i] to the tank, then spend cost[i] to reach
(i + 1) % n; the tank may reach exactly 0 but must never go negative.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_complete_circuit"

CLARIFICATIONS = [
    "nums and cost have the same length n >= 1 and contain non-negative integers.",
    "At each position i you first take on nums[i] gas, then spend cost[i] to reach the next position; the tank may become exactly 0 but never negative.",
    "Return the index as an int, or -1 if no start works.",
]

amount = st.integers(min_value=0, max_value=10)


@st.composite
def stations(draw):
    n = draw(st.integers(min_value=1, max_value=10))
    nums = draw(st.lists(amount, min_size=n, max_size=n))
    shape = draw(st.sampled_from(["random", "small", "equal", "balanced", "constant"]))
    if shape == "small":
        # Gas and cost in 0..1 so the tank often hits exactly 0 or -1, exposing off-by-one bugs.
        nums = draw(st.lists(st.integers(min_value=0, max_value=1), min_size=n, max_size=n))
        cost = draw(st.lists(st.integers(min_value=0, max_value=1), min_size=n, max_size=n))
    elif shape == "random":
        cost = draw(st.lists(amount, min_size=n, max_size=n))
    elif shape == "equal":
        cost = list(nums)
    elif shape == "balanced":
        cost = list(draw(st.permutations(nums)))
    else:
        c = draw(amount)
        nums = [draw(st.sampled_from([c, c + 1]))] * n
        cost = [c] * n
    return nums, cost


def completes_from(nums, cost, start):
    """Drive once around the circle from `start`, refuelling then paying each leg; fail if the tank goes negative."""
    n = len(nums)
    tank = 0
    for step in range(n):
        i = (start + step) % n
        tank += nums[i] - cost[i]
        if tank < 0:
            return False
    return True


@prop("The result is an int that is -1 or a valid index from which the car completes the full circle.", case=stations())
def returned_start_is_valid(f, case):
    nums, cost = case
    r = f(nums, cost)
    assert isinstance(r, int)
    assert r == -1 or (0 <= r < len(nums) and completes_from(nums, cost, r))


@prop("No index smaller than the returned one is a valid start (and -1 means no index is valid).", case=stations())
def returned_start_is_smallest(f, case):
    nums, cost = case
    r = f(nums, cost)
    limit = len(nums) if r == -1 else r
    assert not any(completes_from(nums, cost, i) for i in range(limit))


@prop("The answer is -1 exactly when total gas is less than total cost.", case=stations())
def feasible_iff_enough_gas(f, case):
    nums, cost = case
    assert (f(nums, cost) == -1) == (sum(nums) < sum(cost))


@prop("A single station returns 0 when its gas covers its cost and -1 otherwise.",
      gas=st.integers(min_value=0, max_value=10**6), c=st.integers(min_value=0, max_value=10**6))
def single_station(f, gas, c):
    assert f([gas], [c]) == (0 if gas >= c else -1)

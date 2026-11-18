"""Spec for can_jump: whether the last index is reachable from index 0 with jumps of 1..nums[i] steps forward.

Domain: nums is a non-empty list of non-negative integers.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_jump"

CLARIFICATIONS = [
    "From index i you may jump forward any number of steps from 1 to nums[i]. Return a bool.",
]

jump_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=3), min_size=1, max_size=15),
    st.lists(st.integers(min_value=0, max_value=1), min_size=1, max_size=15),
    st.lists(st.sampled_from([0, 0, 1, 2, 5]), min_size=1, max_size=15),
    st.lists(st.integers(min_value=0, max_value=20), min_size=1, max_size=15),
)


def reachable(nums):
    seen = {0}
    frontier = [0]
    while frontier:
        i = frontier.pop()
        for s in range(1, nums[i] + 1):
            j = i + s
            if j < len(nums) and j not in seen:
                seen.add(j)
                frontier.append(j)
    return len(nums) - 1 in seen


@prop("The result is True exactly when the last index can be reached by a sequence of allowed jumps.", nums=jump_lists)
def matches_reachability(f, nums):
    assert f(nums) == reachable(nums)


@prop("The result is a bool.", nums=jump_lists)
def returns_bool(f, nums):
    assert isinstance(f(nums), bool)


@prop("A single element is always reachable, even [0].", v=st.integers(min_value=0, max_value=10))
def single_element(f, v):
    assert f([v]) is True


@prop("An array of all positive values is always reachable.",
      nums=st.lists(st.integers(min_value=1, max_value=5), min_size=1, max_size=30))
def all_positive(f, nums):
    assert f(nums) is True


@prop("A zero that cannot be jumped over blocks the end.",
      prefix=st.lists(st.integers(min_value=1, max_value=4), max_size=8), tail=st.integers(min_value=1, max_value=5),
      tail_vals=st.lists(st.integers(min_value=0, max_value=5), min_size=5, max_size=5))
def blocking_zero(f, prefix, tail, tail_vals):
    # Cap every jump so it lands at or before the zero at index len(prefix).
    z = len(prefix)
    capped = [min(v, z - i) for i, v in enumerate(prefix)]
    nums = capped + [0] + tail_vals[:tail]
    assert f(nums) is False


@prop("A first jump long enough to reach the end makes it reachable regardless of the rest.",
      rest=st.lists(st.integers(min_value=0, max_value=3), max_size=15), extra=st.integers(min_value=0, max_value=5))
def big_first_jump(f, rest, extra):
    assert f([len(rest) + extra] + rest) is True

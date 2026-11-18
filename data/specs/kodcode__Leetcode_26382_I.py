"""Spec for product_except_self: out[i] is the product of every element of nums except nums[i].

Domain: lists of unique integers (negatives and zero allowed), including the empty list.
Complexity and "no division" requirements are not observable and are not checked.
"""
from math import prod

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "product_except_self"

CLARIFICATIONS = [
    "Return [] for an empty list and [1] for a single-element list (the empty product is 1).",
]

nums_lists = st.one_of(
    st.lists(st.integers(-10, 10), unique=True, max_size=10),
    st.lists(st.integers(-1000, 1000), unique=True, max_size=8),
    st.lists(st.integers(-5, 5), unique=True, min_size=1, max_size=8).map(lambda xs: xs if 0 in xs else xs + [0]),
)


def expected(nums):
    return [prod(nums[:i] + nums[i + 1:]) for i in range(len(nums))]


@prop("The result is a list of the same length as the input.", nums=nums_lists)
def same_length(f, nums):
    r = f(nums)
    assert isinstance(r, list)
    assert len(r) == len(nums)


@prop("Every entry equals the product of all other elements.", nums=nums_lists)
def matches_definition(f, nums):
    assert f(nums) == expected(nums)


@prop("With a zero in the list, only the zero's position can be non-zero.",
      nums=st.lists(st.integers(-9, 9).filter(bool), unique=True, max_size=7), data=st.data())
def zero_handling(f, nums, data):
    k = data.draw(st.integers(0, len(nums)))
    xs = nums[:k] + [0] + nums[k:]
    r = f(xs)
    assert all(r[i] == 0 for i in range(len(xs)) if i != k)
    assert r[k] == prod(nums)


@prop("Each entry times its own element equals the product of the whole list.", nums=nums_lists)
def times_self_is_total(f, nums):
    total = prod(nums)
    assert all(r * x == total for r, x in zip(f(nums), nums))


@prop("Empty gives [], one element gives [1], two elements swap.", a=st.integers(-1000, 1000), b=st.integers(-1000, 1000))
def small_cases(f, a, b):
    assert f([]) == []
    assert f([a]) == [1]
    if a != b:
        assert f([a, b]) == [b, a]

"""Spec for product_except_self: answer[i] is the product of every element except nums[i].

Domain: 2 to 100 integers in [-30, 30] whose non-zero elements have a product within 32-bit range
(which keeps every prefix and suffix product in range). The O(n) time / O(1) space requirement
is not observable and not checked.
"""
import math

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "product_except_self"

CLARIFICATIONS = ["Return the answer as a list of ints."]

INT32_MAX = 2**31 - 1


def fits_int32(nums):
    # Every prefix/suffix product is 0 or a sub-product of the non-zero elements,
    # so bounding the product of all non-zero elements bounds them all.
    return abs(math.prod(x for x in nums if x != 0)) <= INT32_MAX


element = st.one_of(st.integers(-3, 3), st.integers(-30, 30))
nums_any = st.one_of(
    st.lists(element, min_size=2, max_size=15).filter(fits_int32),
    st.lists(st.sampled_from([-1, 1]), min_size=2, max_size=100),
    st.lists(st.sampled_from([-1, 0, 1, 2]), min_size=2, max_size=30).filter(fits_int32),
    st.builds(lambda x, n: [x] * n, st.integers(-3, 3), st.integers(2, 15)),
    st.lists(element, min_size=2, max_size=2),
)
nums_no_zero = st.lists(element.filter(lambda x: x != 0), min_size=2, max_size=15).filter(fits_int32)


@st.composite
def nums_with_zeros(draw, count):
    """A valid array with exactly `count` zeros (or at least 2 when count is None)."""
    base = draw(st.lists(element.filter(lambda x: x != 0), min_size=0, max_size=12).filter(fits_int32))
    zeros = count if count is not None else draw(st.integers(2, 4))
    nums = base + [0] * zeros
    if len(nums) < 2:
        nums.append(draw(element.filter(lambda x: x != 0)))
    return list(draw(st.permutations(nums)))


@prop("The output is a list with one entry per input element.", nums=nums_any)
def same_length(f, nums):
    result = f(nums)
    assert isinstance(result, list) and len(result) == len(nums)


@prop("Each entry equals the direct product of all other elements.", nums=nums_any)
def matches_definition(f, nums):
    result = f(nums)
    expected = [math.prod(nums[:i] + nums[i + 1:]) for i in range(len(nums))]
    assert result == expected


@prop("Without zeros, answer[i] * nums[i] equals the product of the whole array.", nums=nums_no_zero)
def times_self_is_total(f, nums):
    total = math.prod(nums)
    result = f(nums)
    assert all(r * x == total for r, x in zip(result, nums))
    assert len(result) == len(nums)


@prop("With exactly one zero, only the zero's position is non-zero: the product of the rest.", nums=nums_with_zeros(1))
def single_zero(f, nums):
    k = nums.index(0)
    result = f(nums)
    assert len(result) == len(nums)
    for i, r in enumerate(result):
        assert r == (math.prod(nums[:k] + nums[k + 1:]) if i == k else 0)


@prop("With two or more zeros, every entry is 0.", nums=nums_with_zeros(None))
def multiple_zeros(f, nums):
    result = f(nums)
    assert len(result) == len(nums) and all(r == 0 for r in result)


@prop("Permuting the input permutes the output the same way.", nums=nums_any, data=st.data())
def permutation_equivariant(f, nums, data):
    order = data.draw(st.permutations(range(len(nums))))
    result = f(nums)
    permuted = f([nums[i] for i in order])
    assert permuted == [result[i] for i in order]

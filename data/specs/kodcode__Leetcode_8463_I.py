"""Spec for max_length_equal_ones_negones: length of the longest contiguous subarray with as many 1s as -1s.

Domain: arr is a list (possibly empty) whose elements are each 1 or -1.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_length_equal_ones_negones"

CLARIFICATIONS = [
    "Return 0 if the array is empty or no non-empty subarray has equal counts.",
]

pm_lists = st.one_of(
    st.lists(st.sampled_from([1, -1]), max_size=20),
    st.lists(st.sampled_from([1, 1, 1, -1]), max_size=20),
    st.lists(st.sampled_from([-1, -1, -1, 1]), max_size=20),
    st.builds(lambda v, n: [v] * n, st.sampled_from([1, -1]), st.integers(0, 10)),
)


def oracle(arr):
    return max((j - i for i in range(len(arr)) for j in range(i + 1, len(arr) + 1) if sum(arr[i:j]) == 0), default=0)


@prop("The result equals the length of the longest subarray with equal numbers of 1s and -1s.", arr=pm_lists)
def is_longest(f, arr):
    assert f(arr) == oracle(arr)


@prop("The result is an even int between 0 and len(arr), and some subarray of that length is balanced.", arr=pm_lists)
def attained_even(f, arr):
    r = f(arr)
    assert isinstance(r, int) and r % 2 == 0 and 0 <= r <= len(arr)
    if r:
        assert any(sum(arr[i:i + r]) == 0 for i in range(len(arr) - r + 1))


@prop("A whole array with equal counts gives its full length.",
      half=st.integers(min_value=0, max_value=20), data=st.data())
def balanced_whole(f, half, data):
    arr = data.draw(st.permutations([1] * half + [-1] * half))
    assert f(list(arr)) == 2 * half


@prop("Arrays containing only one value (or empty) give 0.", v=st.sampled_from([1, -1]), n=st.integers(min_value=0, max_value=30))
def single_value(f, v, n):
    assert f([v] * n) == 0


@prop("Reversing or negating the array does not change the answer.", arr=pm_lists)
def symmetries(f, arr):
    r = f(arr)
    assert f(arr[::-1]) == r
    assert f([-x for x in arr]) == r

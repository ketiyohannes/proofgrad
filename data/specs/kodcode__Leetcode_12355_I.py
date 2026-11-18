"""Spec for max_sum_k_consecutive: maximum sum over all windows of k consecutive elements.

Domain: arr is a list of integers (negatives allowed); k is an integer. When no window of
k elements exists (arr empty, k < 1 or k > len(arr)) the result is 0, following the
reference solution and unit tests.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_sum_k_consecutive"

CLARIFICATIONS = [
    "Return 0 if arr is empty, if k < 1, or if k is greater than len(arr).",
    "Return the sum as an int.",
]

ints = st.integers(min_value=-1000, max_value=1000)

arrays = st.one_of(
    st.lists(ints, min_size=1, max_size=30),
    st.lists(st.integers(min_value=-1000, max_value=-1), min_size=1, max_size=30),
    st.lists(st.integers(min_value=-3, max_value=3), min_size=1, max_size=30),
    st.builds(lambda x, n: [x] * n, ints, st.integers(min_value=1, max_value=10)),
    st.lists(ints, min_size=1, max_size=30).map(sorted),
    st.lists(ints, min_size=1, max_size=30).map(lambda xs: sorted(xs, reverse=True)),
)


@st.composite
def array_and_valid_k(draw):
    arr = draw(arrays)
    k = draw(st.one_of(st.just(1), st.just(len(arr)), st.integers(min_value=1, max_value=len(arr))))
    return arr, k


@st.composite
def array_and_invalid_k(draw):
    arr = draw(st.one_of(st.just([]), st.lists(ints, min_size=1, max_size=10)))
    k = draw(st.one_of(st.integers(min_value=-3, max_value=0), st.integers(min_value=len(arr) + 1, max_value=len(arr) + 5)))
    return arr, k


def window_sums(arr, k):
    return [sum(arr[i:i + k]) for i in range(len(arr) - k + 1)]


@prop("The result is an int equal to the sum of some k consecutive elements of arr.", case=array_and_valid_k())
def is_achievable(f, case):
    arr, k = case
    result = f(arr, k)
    assert isinstance(result, int)
    assert result in window_sums(arr, k)


@prop("The result is at least the sum of every window of k consecutive elements.", case=array_and_valid_k())
def is_upper_bound(f, case):
    arr, k = case
    result = f(arr, k)
    assert all(result >= s for s in window_sums(arr, k))


@prop("When no window of k elements exists (empty list, k < 1, or k > len(arr)), the result is 0.", case=array_and_invalid_k())
def no_window_returns_zero(f, case):
    arr, k = case
    assert f(arr, k) == 0


@prop("Reversing the list does not change the answer.", case=array_and_valid_k())
def reversal_invariant(f, case):
    arr, k = case
    assert f(arr, k) == f(arr[::-1], k)


@prop("With k == len(arr) the answer is the sum of the whole list.", arr=arrays)
def full_window_is_total(f, arr):
    assert f(arr, len(arr)) == sum(arr)


@prop("With k == 1 the answer is the largest element.", arr=arrays)
def unit_window_is_max(f, arr):
    assert f(arr, 1) == max(arr)

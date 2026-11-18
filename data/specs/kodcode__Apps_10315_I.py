"""Spec for max_consecutive_sum: maximum sum over all windows of exactly k consecutive elements, 0 if len(arr) < k.

Domain: elements in [-10^4, 10^4], k >= 1, arr possibly empty (as the statement allows).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_consecutive_sum"

CLARIFICATIONS = [
    "Return the answer as an int.",
]

values = st.integers(min_value=-10**4, max_value=10**4)


def biased_arrays(min_size):
    """General arrays mixed with all-equal, all-negative, few-distinct, sorted and reverse-sorted arrays."""
    general = st.lists(values, min_size=min_size, max_size=30)
    return st.one_of(
        general,
        st.lists(st.integers(min_value=-10**4, max_value=-1), min_size=min_size, max_size=30),
        st.tuples(values, st.integers(min_value=min_size, max_value=30)).map(lambda t: [t[0]] * t[1]),
        st.lists(st.sampled_from([-1, 0, 1]), min_size=min_size, max_size=30),
        general.map(sorted),
        general.map(lambda xs: sorted(xs, reverse=True)),
    )


@st.composite
def array_and_valid_k(draw):
    arr = draw(biased_arrays(1))
    k = draw(st.one_of(st.just(1), st.just(len(arr)), st.integers(min_value=1, max_value=len(arr))))
    return arr, k


def window_sums(arr, k):
    return [sum(arr[i:i + k]) for i in range(len(arr) - k + 1)]


@prop("When k <= len(arr), the result equals the largest sum of any k consecutive elements.",
      case=array_and_valid_k())
def matches_brute_force(f, case):
    arr, k = case
    assert f(arr, k) == max(window_sums(arr, k))


@prop("The result is an int.", case=array_and_valid_k())
def returns_int(f, case):
    arr, k = case
    result = f(arr, k)
    assert isinstance(result, int) and not isinstance(result, bool)


@prop("When the array has fewer than k elements (including the empty array), the result is 0.",
      arr=st.one_of(st.just([]), biased_arrays(0)), extra=st.integers(min_value=1, max_value=20))
def short_array_returns_zero(f, arr, extra):
    assert f(arr, len(arr) + extra) == 0


@prop("With k == len(arr) the result is the sum of the whole array.", arr=biased_arrays(1))
def whole_array_window(f, arr):
    assert f(arr, len(arr)) == sum(arr)


@prop("With k == 1 the result is the largest element.", arr=biased_arrays(1))
def single_element_window(f, arr):
    assert f(arr, 1) == max(arr)


@prop("Reversing the array does not change the answer.", case=array_and_valid_k())
def reversal_invariant(f, case):
    arr, k = case
    assert f(arr, k) == f(arr[::-1], k)

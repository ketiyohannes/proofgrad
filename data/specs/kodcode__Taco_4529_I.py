"""Spec for specialSort: stable partition of arr with multiples of K first.

Domain: 1 <= arr[i] <= 10^9, 1 <= K <= 10^9, N == len(arr) (the unit tests also use an empty array).
The task requires modifying arr in place and the reference returns None. The grading harness
deep-copies arguments on every call, so in-place changes cannot be observed; the properties below
check a returned list instead, which the reference does not provide.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "specialSort"

EXCLUDE_REASON = (
    "The contract is an in-place modification with no return value (the reference returns None), "
    "which cannot be observed because the grader deep-copies arguments on every call."
)

CLARIFICATIONS = [
    "Return the rearranged list.",
]

ks = st.one_of(st.integers(1, 6), st.integers(1, 10**9))
arrays = st.one_of(
    st.lists(st.integers(1, 30), max_size=25),
    st.lists(st.integers(1, 10**9), max_size=25),
)


def stable_partition(arr, k):
    return [x for x in arr if x % k == 0] + [x for x in arr if x % k != 0]


@prop("The returned list is the stable partition with multiples of K first.", arr=arrays, k=ks)
def stable_partition_result(f, arr, k):
    assert f(arr, len(arr), k) == stable_partition(arr, k)


@prop("The returned list is a permutation of arr.", arr=arrays, k=ks)
def is_permutation(f, arr, k):
    assert sorted(f(arr, len(arr), k)) == sorted(arr)


@prop("No non-multiple of K appears before a multiple of K.", arr=arrays, k=ks)
def multiples_first(f, arr, k):
    flags = [x % k == 0 for x in f(arr, len(arr), k)]
    assert flags == sorted(flags, reverse=True)

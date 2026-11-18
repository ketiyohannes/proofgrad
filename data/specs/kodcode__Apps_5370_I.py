"""Spec for subarray_sum_exists: report whether some non-empty contiguous subarray sums to target.

Domain: non-empty lists of up to 25 integers in [-30, 30] (the statement and its third example
allow negatives), targets in [-200, 200].

EXCLUDED: the reference solution is a sliding window that is only correct for non-negative
elements and positive targets. It answers 'No' for ([5, -1], 4) although 5 + -1 == 4, and
'Yes' for ([3], 0) although no non-empty subarray sums to 0. The properties below follow the
problem statement, so the reference fails several of them.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "subarray_sum_exists"

EXCLUDE_REASON = (
    "The reference solution (a sliding window) contradicts the statement on arrays containing negative "
    "numbers, which the statement explicitly allows: it returns 'No' for ([5, -1], 4)."
)

CLARIFICATIONS = ["The subarray must contain at least one element."]

YES = "Yes, the subarray exists."
NO = "No, such subarray does not exist."

value = st.integers(min_value=-30, max_value=30)
arrays = st.one_of(
    st.lists(value, min_size=1, max_size=25),
    st.lists(st.integers(min_value=0, max_value=30), min_size=1, max_size=25),
    st.lists(st.sampled_from([-2, -1, 0, 1, 3]), min_size=1, max_size=25),
    st.builds(lambda x, n: [x] * n, value, st.integers(1, 25)),
)
targets = st.integers(min_value=-200, max_value=200)


def subarray_sums(array):
    n = len(array)
    return {sum(array[i:j]) for i in range(n) for j in range(i + 1, n + 1)}


@st.composite
def array_with_subarray_target(draw):
    """An array plus a target equal to the sum of one of its non-empty contiguous subarrays."""
    array = draw(arrays)
    i = draw(st.integers(0, len(array) - 1))
    j = draw(st.integers(i + 1, len(array)))
    return array, sum(array[i:j])


@prop("The result is always one of the two exact response strings.", array=arrays, target=targets)
def exact_strings(f, array, target):
    assert f(array, target) in (YES, NO)


@prop("If a non-empty contiguous subarray sums to target, the answer is Yes.", inst=array_with_subarray_target())
def detects_existing_subarray(f, inst):
    array, target = inst
    assert f(array, target) == YES


@prop("The answer matches a brute-force check over all non-empty contiguous subarrays.", array=arrays, target=targets)
def matches_brute_force(f, array, target):
    assert f(array, target) == (YES if target in subarray_sums(array) else NO)


@prop(
    "A target larger than the sum of all positive elements cannot be reached.",
    array=arrays,
    excess=st.integers(min_value=1, max_value=100),
)
def target_above_positive_total(f, array, excess):
    assert f(array, sum(x for x in array if x > 0) + excess) == NO


@prop(
    "Elements must be contiguous: skipping over an element does not count.",
    inst=st.tuples(
        st.integers(min_value=1, max_value=30), st.integers(min_value=1, max_value=30), st.integers(min_value=1, max_value=30)
    ).filter(lambda t: t[0] + t[2] not in (t[0], t[1], t[2], t[0] + t[1], t[1] + t[2])),
)
def requires_contiguity(f, inst):
    a, b, c = inst
    assert f([a, b, c], a + c) == NO


@prop("Reversing the array does not change the answer.", array=arrays, target=targets)
def reversal_invariant(f, array, target):
    assert f(array, target) == f(array[::-1], target)

"""Spec for max_subarray_sum: maximum sum over all non-empty contiguous subarrays (0 for an empty list).

Domain: lists of up to 30 integers in [-1000, 1000]; the empty list is covered by the unit tests.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_subarray_sum"

CLARIFICATIONS = [
    "The function receives the list of integers directly (not a string) and returns an int.",
    "A subarray must contain at least one element, so for a list of only negative numbers the answer is its largest element.",
    "Return 0 for an empty list.",
]

value = st.integers(min_value=-100, max_value=100)


@st.composite
def all_equal(draw):
    return [draw(value)] * draw(st.integers(1, 30))


# Mix in degenerate shapes: single elements, all-equal lists, few distinct values, sorted runs.
nonempty_ints = st.one_of(
    st.lists(value, min_size=1, max_size=30),
    st.lists(value, min_size=1, max_size=1),
    all_equal(),
    st.lists(st.sampled_from([-3, -1, 0, 2]), min_size=1, max_size=30),
    st.lists(value, min_size=1, max_size=30).map(sorted),
    st.lists(value, min_size=1, max_size=30).map(lambda xs: sorted(xs, reverse=True)),
)
negative_ints = st.one_of(
    st.lists(st.integers(min_value=-1000, max_value=-1), min_size=1, max_size=30),
    st.lists(st.integers(min_value=-1000, max_value=-1), min_size=1, max_size=1),
)
nonnegative_ints = st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=30)


def subarray_sums(xs):
    return [sum(xs[i:j]) for i in range(len(xs)) for j in range(i + 1, len(xs) + 1)]


@prop("An empty list yields 0.", xs=st.just([]))
def empty_is_zero(f, xs):
    assert f(xs) == 0


@prop("The result is the sum of some non-empty contiguous subarray.", xs=nonempty_ints)
def is_achieved(f, xs):
    assert f(xs) in set(subarray_sums(xs))


@prop("No non-empty contiguous subarray has a larger sum than the result.", xs=nonempty_ints)
def is_upper_bound(f, xs):
    result = f(xs)
    assert all(s <= result for s in subarray_sums(xs))


@prop("For all-negative lists the result is the largest single element.", xs=negative_ints)
def all_negative_is_max_element(f, xs):
    assert f(xs) == max(xs)


@prop("For lists without negative numbers the result is the sum of the whole list.", xs=nonnegative_ints)
def nonnegative_is_total(f, xs):
    assert f(xs) == sum(xs)


@prop("Reversing the list does not change the result.", xs=nonempty_ints)
def reversal_invariant(f, xs):
    assert f(xs) == f(xs[::-1])

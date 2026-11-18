"""Spec for longest_subarray_with_limit: longest contiguous subarray whose max - min is at most k.

Domain: arr is a list of positive integers (the unit tests also use the empty list, which gives 0);
k is a non-negative integer.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "longest_subarray_with_limit"

CLARIFICATIONS = [
    "Return 0 for an empty array.",
]

arrays = st.one_of(
    st.lists(st.integers(min_value=1, max_value=20), max_size=15),
    st.lists(st.integers(min_value=1, max_value=3), max_size=15),
    st.lists(st.integers(min_value=1, max_value=10**9), max_size=15),
    st.lists(st.integers(min_value=1, max_value=20), max_size=15).map(sorted),
)


@st.composite
def case(draw):
    arr = draw(arrays)
    diffs = sorted({abs(a - b) for a in arr for b in arr}) or [0]
    k = draw(st.one_of(st.integers(min_value=0, max_value=10), st.sampled_from(diffs),
                       st.integers(min_value=0, max_value=10**9)))
    return arr, k


def oracle(arr, k):
    return max((j - i for i in range(len(arr)) for j in range(i + 1, len(arr) + 1)
                if max(arr[i:j]) - min(arr[i:j]) <= k), default=0)


@prop("The result equals the length of the longest subarray whose max minus min is at most k.", c=case())
def is_longest(f, c):
    arr, k = c
    assert f(arr, k) == oracle(arr, k)


@prop("Some subarray of the returned length satisfies the limit.", c=case())
def length_attained(f, c):
    arr, k = c
    r = f(arr, k)
    assert isinstance(r, int) and 0 <= r <= len(arr)
    if r:
        assert any(max(arr[i:i + r]) - min(arr[i:i + r]) <= k for i in range(len(arr) - r + 1))


@prop("A k at least the overall spread gives the whole length.",
      arr=st.lists(st.integers(min_value=1, max_value=10**9), min_size=1, max_size=40), extra=st.integers(0, 5))
def large_k_whole_array(f, arr, extra):
    assert f(arr, max(arr) - min(arr) + extra) == len(arr)


@prop("With k = 0 the answer is the longest run of equal adjacent values.", arr=arrays)
def zero_k_runs(f, arr):
    best, run = 0, 0
    for i, v in enumerate(arr):
        run = run + 1 if i and arr[i - 1] == v else 1
        best = max(best, run)
    assert f(arr, 0) == best


@prop("Increasing k never decreases the answer.", c=case(), d=st.integers(min_value=1, max_value=5))
def monotone_in_k(f, c, d):
    arr, k = c
    assert f(arr, k + d) >= f(arr, k)


@prop("The empty array gives 0 and a single element gives 1.", x=st.integers(min_value=1, max_value=10**9), k=st.integers(0, 10))
def tiny_inputs(f, x, k):
    assert f([], k) == 0
    assert f([x], k) == 1

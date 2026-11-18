"""Spec for max_rectangle_area: largest (range length) * (minimum height in range) over non-empty contiguous ranges.

Domain: heights is a list (possibly empty) of non-negative integers.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_rectangle_area"

CLARIFICATIONS = [
    "Return 0 for an empty list.",
]

height_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=20), max_size=14),
    st.lists(st.integers(min_value=0, max_value=3), max_size=14),
    st.lists(st.integers(min_value=0, max_value=20), max_size=14).map(sorted),
    st.lists(st.integers(min_value=0, max_value=20), max_size=14).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda v, n: [v] * n, st.integers(0, 10), st.integers(0, 14)),
)


def oracle(h):
    return max((min(h[i:j]) * (j - i) for i in range(len(h)) for j in range(i + 1, len(h) + 1)), default=0)


@prop("The result equals the largest width * minimum height over all contiguous ranges.", heights=height_lists)
def is_maximum(f, heights):
    assert f(heights) == oracle(heights)


@prop("The result is at least the tallest building and at least min(heights) * len(heights).",
      heights=st.lists(st.integers(min_value=0, max_value=10**4), min_size=1, max_size=60))
def lower_bounds(f, heights):
    r = f(heights)
    assert r >= max(heights)
    assert r >= min(heights) * len(heights)


@prop("Reversing the buildings does not change the answer.", heights=height_lists)
def reversal_invariant(f, heights):
    assert f(heights[::-1]) == f(heights)


@prop("Equal heights give height * count.", v=st.integers(min_value=0, max_value=1000), n=st.integers(min_value=1, max_value=50))
def uniform_heights(f, v, n):
    assert f([v] * n) == v * n


@prop("An empty list gives 0 and a single building gives its height.", h=st.integers(min_value=0, max_value=10**6))
def tiny_inputs(f, h):
    assert f([]) == 0
    assert f([h]) == h

"""Spec for average_in_range: the mean of the elements in [10, 20], or None if there are none.

Domain: lists of integers (including negatives and the empty list). Means are compared
with a small relative tolerance.
"""
import math

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "average_in_range"

int_lists = st.one_of(
    st.lists(st.integers(-5, 30), max_size=20),
    st.lists(st.sampled_from([9, 10, 11, 19, 20, 21]), max_size=12),
    st.lists(st.integers(-1000, 1000), max_size=20),
)


def close(a, b):
    return a is not None and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


@prop("If some elements lie in 10..20, the result is their arithmetic mean.", numbers=int_lists)
def mean_of_in_range(f, numbers):
    inside = [x for x in numbers if 10 <= x <= 20]
    if inside:
        assert close(f(numbers), sum(inside) / len(inside))


@prop("The bounds 10 and 20 are included.", left=st.integers(0, 5), right=st.integers(0, 5))
def bounds_inclusive(f, left, right):
    numbers = [10] * left + [20] * right + [15]
    assert close(f(numbers), (10 * left + 20 * right + 15) / (left + right + 1))


@prop("Elements outside 10..20 do not affect the result.", numbers=int_lists,
      outside=st.lists(st.one_of(st.integers(-100, 9), st.integers(21, 100)), max_size=10))
def outside_ignored(f, numbers, outside):
    a, b = f(numbers), f(numbers + outside)
    assert (a is None and b is None) or close(b, a)


@prop("If no element lies in 10..20 (including the empty list), the result is None.",
      numbers=st.lists(st.one_of(st.integers(-100, 9), st.integers(21, 100)), max_size=15))
def none_when_empty(f, numbers):
    assert f(numbers) is None


@prop("A single in-range element is its own average.", x=st.integers(10, 20))
def single_element(f, x):
    assert close(f([x]), x)

"""Spec for running_median: list whose i-th entry is the median of nums[0..i].

Domain: integer lists (negatives and duplicates allowed), including the empty list.
Medians of even-sized prefixes are the mean of the two middle values (compared numerically).
"""
import math

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "running_median"

CLARIFICATIONS = [
    "Return a list of numbers; an empty input gives an empty list.",
    "For an even-sized prefix, the median is the true (possibly fractional) average of the two middle values, e.g. 1.5.",
]

nums_st = st.one_of(
    st.lists(st.integers(min_value=-5, max_value=5), max_size=20),
    st.lists(st.integers(min_value=-10**6, max_value=10**6), max_size=20),
    st.lists(st.integers(min_value=0, max_value=50), max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=50), max_size=20).map(lambda xs: sorted(xs, reverse=True)),
)


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def close(a, b):
    return math.isclose(a, b, rel_tol=0, abs_tol=1e-9)


@prop("The result is a list with one entry per input element.", nums=nums_st)
def same_length(f, nums):
    r = f(nums)
    assert isinstance(r, list)
    assert len(r) == len(nums)


@prop("Every entry equals the median of the corresponding prefix.", nums=nums_st)
def prefix_medians(f, nums):
    r = f(nums)
    assert all(close(r[i], median(nums[: i + 1])) for i in range(len(nums)))


@prop("Even-sized prefixes use the exact average of the two middle values (fractions kept).",
      a=st.integers(min_value=-1000, max_value=1000), b=st.integers(min_value=-1000, max_value=1000))
def even_average(f, a, b):
    r = f([a, b])
    assert close(r[0], a) and close(r[1], (a + b) / 2)


@prop("The first entry is the first element, and the last entry is the median of the whole list.",
      nums=nums_st.filter(bool))
def first_and_last(f, nums):
    r = f(nums)
    assert close(r[0], nums[0])
    assert close(r[-1], median(nums))


@prop("An empty list gives an empty list.", dummy=st.just(None))
def empty(f, dummy):
    assert f([]) == []

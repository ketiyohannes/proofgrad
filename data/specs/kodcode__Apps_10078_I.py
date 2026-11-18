"""Spec for reverseWithinBounds: reverse arr[start..end] (inclusive), leaving other elements unchanged.

Domain: non-empty integer lists, 0 <= start <= end < len(arr).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "reverseWithinBounds"

CLARIFICATIONS = [
    "Return the resulting list; bounds always satisfy 0 <= start <= end < len(arr).",
]


@st.composite
def cases(draw, distinct=False):
    n = draw(st.integers(min_value=1, max_value=15))
    if distinct:
        arr = draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n, unique=True))
    else:
        arr = draw(st.one_of(
            st.lists(st.integers(-10**6, 10**6), min_size=n, max_size=n),
            st.lists(st.integers(0, 2), min_size=n, max_size=n),
        ))
    kind = draw(st.sampled_from(["any", "whole", "single", "prefix", "suffix"]))
    if kind == "whole":
        s, e = 0, n - 1
    elif kind == "single":
        s = e = draw(st.integers(0, n - 1))
    elif kind == "prefix":
        s, e = 0, draw(st.integers(0, n - 1))
    elif kind == "suffix":
        s, e = draw(st.integers(0, n - 1)), n - 1
    else:
        s = draw(st.integers(0, n - 1))
        e = draw(st.integers(s, n - 1))
    return arr, (s, e)


@prop("The result is a list equal to arr with arr[start..end] reversed in place.", case=cases())
def matches_definition(f, case):
    arr, (s, e) = case
    r = f(arr, (s, e))
    assert isinstance(r, list)
    assert r == arr[:s] + arr[s:e + 1][::-1] + arr[e + 1:]


@prop("Elements outside the bounds are unchanged.", case=cases(distinct=True))
def outside_unchanged(f, case):
    arr, (s, e) = case
    r = f(arr, (s, e))
    assert len(r) == len(arr)
    assert r[:s] == arr[:s] and r[e + 1:] == arr[e + 1:]


@prop("Each position i inside the bounds holds arr[start + end - i].", case=cases(distinct=True))
def inside_mirrored(f, case):
    arr, (s, e) = case
    r = f(arr, (s, e))
    assert all(r[i] == arr[s + e - i] for i in range(s, e + 1))


@prop("Bounds covering one element leave the array unchanged.",
      data=st.data(), arr=st.lists(st.integers(-100, 100), min_size=1, max_size=15))
def single_element_bounds(f, data, arr):
    i = data.draw(st.integers(0, len(arr) - 1))
    assert f(arr, (i, i)) == arr


@prop("Bounds covering the whole array reverse it entirely.",
      arr=st.lists(st.integers(-100, 100), min_size=1, max_size=15))
def whole_array(f, arr):
    assert f(arr, (0, len(arr) - 1)) == arr[::-1]

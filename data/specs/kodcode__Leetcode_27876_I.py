"""Spec for count_visible_buildings: number of buildings strictly taller than every building to their left.

Domain: lists of non-negative integer heights, including the empty list.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_visible_buildings"

CLARIFICATIONS = [
    "Return 0 for an empty list; the first building is always visible.",
    "A building that is only as tall as (not taller than) some building to its left is not visible.",
]

heights_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=5), max_size=20),
    st.lists(st.integers(min_value=0, max_value=10**6), max_size=30),
    st.lists(st.integers(min_value=0, max_value=20), max_size=20).map(sorted),
    st.lists(st.integers(min_value=0, max_value=20), max_size=20).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(min_value=0, max_value=10), st.integers(min_value=1, max_value=10)),
)


def visible_count(hs):
    return sum(1 for i, h in enumerate(hs) if all(hs[j] < h for j in range(i)))


@prop("The result is an int equal to the number of buildings taller than all buildings to their left.", hs=heights_lists)
def matches_definition(f, hs):
    r = f(hs)
    assert isinstance(r, int)
    assert r == visible_count(hs)


@prop("A strictly increasing sequence of buildings is entirely visible.",
      hs=st.lists(st.integers(min_value=0, max_value=1000), unique=True, min_size=1, max_size=20).map(sorted))
def increasing_all_visible(f, hs):
    assert f(hs) == len(hs)


@prop("A non-increasing sequence (including equal heights) has exactly one visible building.",
      hs=st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=20).map(lambda xs: sorted(xs, reverse=True)))
def non_increasing_one_visible(f, hs):
    assert f(hs) == 1


@prop("Appending a building taller than all others adds exactly one visible building.",
      hs=st.lists(st.integers(min_value=0, max_value=10), max_size=15), extra=st.integers(min_value=1, max_value=5))
def append_tallest(f, hs, extra):
    tallest = max(hs, default=0) + extra
    assert f(hs + [tallest]) == f(hs) + 1


@prop("An empty list gives 0 and a single building gives 1.", h=st.integers(min_value=0, max_value=10**6))
def degenerate(f, h):
    assert f([]) == 0
    assert f([h]) == 1

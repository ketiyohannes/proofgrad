"""Spec for maxContainerArea: largest min(h[i], h[j]) * (j - i) over pairs of buildings i < j.

Domain: lists of non-negative integer heights; fewer than two buildings give 0.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "maxContainerArea"

CLARIFICATIONS = [
    "The distance between buildings i and j is j - i; return 0 when there are fewer than two buildings.",
]

heights = st.one_of(
    st.lists(st.integers(0, 10), min_size=2, max_size=30),
    st.lists(st.integers(0, 1000), min_size=2, max_size=30),
    st.lists(st.integers(0, 2), min_size=2, max_size=30),
    st.lists(st.integers(0, 50), min_size=2, max_size=30).map(sorted),
    st.lists(st.integers(0, 50), min_size=2, max_size=30).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda h, n: [h] * n, st.integers(0, 20), st.integers(2, 20)),
)


def best(hs):
    return max((min(hs[i], hs[j]) * (j - i) for i in range(len(hs)) for j in range(i + 1, len(hs))), default=0)


@prop("The result is an int equal to the maximum container area over all pairs of buildings.", hs=heights)
def matches_definition(f, hs):
    r = f(hs)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == best(hs)


@prop("The result is achieved by some pair of buildings.", hs=heights)
def achieved_by_pair(f, hs):
    r = f(hs)
    assert any(min(hs[i], hs[j]) * (j - i) == r for i in range(len(hs)) for j in range(i + 1, len(hs)))


@prop("No pair of buildings gives a larger area than the result.", hs=heights)
def is_upper_bound(f, hs):
    r = f(hs)
    assert all(min(hs[i], hs[j]) * (j - i) <= r for i in range(len(hs)) for j in range(i + 1, len(hs)))


@prop("Reversing the buildings does not change the answer.", hs=heights)
def reverse_invariant(f, hs):
    assert f(hs) == f(hs[::-1])


@prop("Two buildings give min(a, b) and a single building gives 0.", a=st.integers(0, 10**6), b=st.integers(0, 10**6))
def tiny_inputs(f, a, b):
    assert f([a, b]) == min(a, b)
    assert f([a]) == 0

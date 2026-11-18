"""Spec for rotate_list: return L rotated right by N positions (element i moves to index (i + N) % len(L)).

Domain: lists of 1..30 integers and 0 <= N <= 1001 (the unit tests use N = 1001, just past the stated bound),
plus the empty list that the unit tests check. The statement asks to print the result, but the signature and
reference return the rotated list; a clarification states that.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "rotate_list"

CLARIFICATIONS = [
    "Return the rotated list instead of printing it.",
    "N may be larger than the length of L.",
    "Return [] when L is empty.",
]

lists = st.one_of(
    st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=30),
    st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=2),
    st.lists(st.sampled_from([0, 1]), min_size=1, max_size=30),
)
shifts = st.one_of(st.integers(min_value=0, max_value=1001), st.sampled_from([0, 1, 1000, 1001]))


def rotate_once(xs):
    return xs[-1:] + xs[:-1]


@prop("The result equals moving the last element to the front N times.", L=lists, N=shifts)
def matches_repeated_single_steps(f, L, N):
    expected = list(L)
    for _ in range(N):
        expected = rotate_once(expected)
    assert f(L, N) == expected


@prop("Element L[i] ends up at index (i + N) % len(L) of a list with the same length.",
      L=st.lists(st.integers(-1000, 1000), min_size=1, max_size=30, unique=True), N=shifts)
def index_mapping(f, L, N):
    out = f(L, N)
    assert isinstance(out, list) and len(out) == len(L)
    for i, x in enumerate(L):
        assert out[(i + N) % len(L)] == x


@prop("Rotating by 0 returns the list unchanged.", L=lists)
def zero_is_identity(f, L):
    assert f(L, 0) == L


@prop("Rotating by a positive multiple of len(L) returns the list unchanged.",
      L=lists, k=st.integers(min_value=1, max_value=30))
def full_turns_are_identity(f, L, k):
    k = min(k, 1001 // len(L))
    assert f(L, k * len(L)) == L


@prop("Rotating by N and then by M is the same as rotating by N + M.", L=lists,
      N=st.integers(0, 500), M=st.integers(0, 500))
def composition(f, L, N, M):
    assert f(f(L, N), M) == f(L, N + M)


@prop("Rotating an empty list returns an empty list.", N=shifts)
def empty_list(f, N):
    assert f([], N) == []

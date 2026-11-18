"""Spec for rotate_array: arr rotated right by k steps (last element moves to the front, k times).

Domain: non-empty lists of integers (-10^9..10^9), 0 <= k <= 10^5.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "rotate_array"

CLARIFICATIONS = [
    "Return the rotated array as a new list.",
]

arrays = st.one_of(
    st.lists(st.integers(-10**9, 10**9), min_size=1, max_size=20),
    st.lists(st.integers(0, 3), min_size=1, max_size=20),
    st.lists(st.integers(-10**9, 10**9), min_size=1, max_size=2),
)
small_k = st.integers(0, 45)
any_k = st.one_of(small_k, st.integers(0, 10**5))


def rotate_steps(arr, k):
    """Apply k single right rotations literally."""
    out = list(arr)
    for _ in range(k):
        out = [out[-1]] + out[:-1]
    return out


@prop("The result equals applying k single right rotations.", arr=arrays, k=small_k)
def matches_steps(f, arr, k):
    assert f(arr, k) == rotate_steps(arr, k)


@prop("The result is a list of the same length containing the same elements.", arr=arrays, k=any_k)
def is_permutation(f, arr, k):
    r = f(arr, k)
    assert isinstance(r, list)
    assert sorted(r) == sorted(arr)


@prop("Rotating by k + len(arr) gives the same result as rotating by k (large k).", arr=arrays, k=any_k)
def periodic(f, arr, k):
    assert f(arr, k + len(arr)) == f(arr, k)


@prop("Rotating by 0 or by a multiple of the length returns the array unchanged.", arr=arrays, mult=st.integers(0, 1000))
def full_turns_identity(f, arr, mult):
    assert f(arr, 0) == arr
    assert f(arr, len(arr) * mult) == arr


@prop("Element i of the input ends up at position (i + k) mod n.", arr=st.lists(st.integers(), min_size=1, max_size=20, unique=True), k=any_k)
def positions(f, arr, k):
    r = f(arr, k)
    n = len(arr)
    assert all(r[(i + k) % n] == arr[i] for i in range(n))

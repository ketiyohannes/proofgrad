"""Spec for has_pair_with_sum: whether two elements at different positions sum to x.

Domain: integer lists (possibly empty, with duplicates and negatives) and an integer x.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "has_pair_with_sum"

CLARIFICATIONS = [
    "The two elements must be at different positions; equal values at two positions may be paired.",
    "Return a bool (True or False).",
]

arrays = st.one_of(
    st.lists(st.integers(min_value=-6, max_value=6), max_size=12),
    st.lists(st.integers(min_value=-10**9, max_value=10**9), max_size=12),
)


@st.composite
def array_and_x(draw):
    arr = draw(arrays)
    mode = draw(st.sampled_from(["any", "pair", "double"]))
    if mode == "pair" and len(arr) >= 2:
        i, j = draw(st.lists(st.integers(min_value=0, max_value=len(arr) - 1), min_size=2, max_size=2, unique=True))
        x = arr[i] + arr[j]
    elif mode == "double" and arr:
        x = 2 * draw(st.sampled_from(arr))
    else:
        x = draw(st.integers(min_value=-12, max_value=12))
    return arr, x


def has_pair(arr, x):
    return any(arr[i] + arr[j] == x for i in range(len(arr)) for j in range(i + 1, len(arr)))


@prop("The result is True exactly when two elements at different positions sum to x.", case=array_and_x())
def matches_definition(f, case):
    arr, x = case
    r = f(arr, x)
    assert isinstance(r, bool)
    assert r == has_pair(arr, x)


@prop("An element is never paired with itself.",
      vals=st.lists(st.integers(min_value=-1000, max_value=1000), unique=True, max_size=10), data=st.data())
def no_self_pairing(f, vals, data):
    if not vals:
        assert f([], data.draw(st.integers(min_value=-10, max_value=10))) is False
        return
    a = data.draw(st.sampled_from(vals))
    expected = has_pair(vals, 2 * a)
    assert f(vals, 2 * a) is expected


@prop("Two equal values at different positions can form a pair.", a=st.integers(min_value=-10**9, max_value=10**9),
      others=st.lists(st.integers(min_value=-10**9, max_value=10**9), max_size=5), data=st.data())
def duplicates_pair(f, a, others, data):
    arr = data.draw(st.permutations(others + [a, a]))
    assert f(list(arr), 2 * a) is True


@prop("The order of the elements does not matter.", case=array_and_x(), data=st.data())
def order_invariant(f, case, data):
    arr, x = case
    shuffled = list(data.draw(st.permutations(arr)))
    assert f(arr, x) == f(shuffled, x)


@prop("Empty and single-element arrays never contain a pair.", a=st.integers(min_value=-100, max_value=100), x=st.integers(min_value=-200, max_value=200))
def too_small(f, a, x):
    assert f([], x) is False
    assert f([a], x) is False
    assert f([a], 2 * a) is False

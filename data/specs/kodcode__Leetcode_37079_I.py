"""Spec for has_pair_with_sum: whether two different elements of arr sum to k.

Domain: arr is a list of distinct integers (possibly empty or a single element); k is any integer.
An element may not be paired with itself.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "has_pair_with_sum"

CLARIFICATIONS = [
    "Return a bool; return False for an empty or single-element array.",
]

distinct_lists = st.one_of(
    st.lists(st.integers(min_value=-20, max_value=20), unique=True, max_size=12),
    st.lists(st.integers(min_value=-10**7, max_value=10**7), unique=True, max_size=12),
)


def oracle(arr, k):
    return any(arr[i] + arr[j] == k for i in range(len(arr)) for j in range(i + 1, len(arr)))


@st.composite
def case(draw):
    arr = draw(distinct_lists)
    mode = draw(st.sampled_from(["pair", "double", "random"]))
    if mode == "pair" and len(arr) >= 2:
        i, j = draw(st.lists(st.integers(0, len(arr) - 1), min_size=2, max_size=2, unique=True))
        k = arr[i] + arr[j]
    elif mode == "double" and arr:
        k = 2 * draw(st.sampled_from(arr))
    else:
        k = draw(st.integers(min_value=-40, max_value=40))
    return arr, k


@prop("The result is True exactly when two different elements sum to k.", c=case())
def matches_definition(f, c):
    arr, k = c
    assert f(arr, k) == oracle(arr, k)


@prop("The sum of any two distinct chosen elements is detected (result is True).", c=case())
def finds_existing_pair(f, c):
    arr, k = c
    if oracle(arr, k):
        assert f(arr, k) is True


@prop("An element is never paired with itself: k equal to twice a lone element gives False.",
      x=st.integers(min_value=-10**6, max_value=10**6), others=st.lists(st.integers(min_value=10**7, max_value=2 * 10**7), unique=True, max_size=5))
def no_self_pairing(f, x, others):
    arr = [x] + others
    assert f(arr, 2 * x) is False


@prop("Empty and single-element arrays give False.",
      x=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)), k=st.integers(min_value=-200, max_value=200))
def too_short(f, x, k):
    arr = [] if x is None else [x]
    assert f(arr, k) is False


@prop("The result is a bool and does not depend on element order.", c=case(), data=st.data())
def bool_and_order_invariant(f, c, data):
    arr, k = c
    r = f(arr, k)
    assert isinstance(r, bool)
    assert f(list(data.draw(st.permutations(arr))), k) == r

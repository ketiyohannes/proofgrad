"""Spec for pairSum: True iff two elements at different positions sum to target.

Domain: lists of up to 20 integers in [-50, 50] (plus a few large values), targets in [-200, 200].
"Two distinct numbers" is read as two different positions, as the [4, 4] example shows.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "pairSum"

CLARIFICATIONS = [
    "Return the Python booleans True or False.",
    "The two numbers must be at different positions in the array but may have equal values; a single element cannot be used twice.",
]

values = st.one_of(st.integers(min_value=-50, max_value=50), st.sampled_from([-10**8, 10**8, 10**7]))
targets = st.one_of(st.integers(min_value=-200, max_value=200), st.just(0))


@st.composite
def all_equal(draw):
    return [draw(values)] * draw(st.integers(0, 20))


arrays = st.one_of(
    st.lists(values, max_size=20),
    all_equal(),
    st.lists(st.sampled_from([-2, 0, 1, 3]), max_size=20),
    st.lists(values, min_size=2, max_size=2),
)


def brute_force(arr, target):
    return any(arr[i] + arr[j] == target for i in range(len(arr)) for j in range(i + 1, len(arr)))


@st.composite
def array_with_pair(draw):
    """An array plus a target equal to the sum of two elements at different positions."""
    arr = draw(st.one_of(st.lists(values, min_size=2, max_size=20), all_equal().filter(lambda xs: len(xs) >= 2)))
    i, j = draw(st.lists(st.integers(0, len(arr) - 1), min_size=2, max_size=2, unique=True))
    return arr, arr[i] + arr[j]


@st.composite
def single_use_trap(draw):
    """Distinct elements and a target equal to twice one of them: that element may not pair with itself."""
    arr = draw(st.lists(values, min_size=1, max_size=20, unique=True))
    x = draw(st.sampled_from(arr))
    return arr, 2 * x


@prop("Arrays with fewer than two elements give False.", arr=st.lists(values, max_size=1), target=targets)
def short_array_false(f, arr, target):
    assert f(arr, target) is False


@prop("If two elements at different positions sum to target, the result is True.", inst=array_with_pair())
def detects_pair(f, inst):
    arr, target = inst
    assert f(arr, target) is True


@prop("The result equals a brute-force check over all pairs of positions.", arr=arrays, target=targets)
def matches_brute_force(f, arr, target):
    assert f(arr, target) is brute_force(arr, target)


@prop("A single element is never paired with itself.", inst=single_use_trap())
def no_self_pairing(f, inst):
    arr, target = inst
    assert f(arr, target) is brute_force(arr, target)


@prop("Reordering the array does not change the result.", arr=arrays, target=targets, data=st.data())
def order_invariant(f, arr, target, data):
    shuffled = data.draw(st.permutations(arr))
    assert f(arr, target) == f(list(shuffled), target)

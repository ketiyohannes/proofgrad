"""Spec for min_operations_to_equalize: minimum +-1 steps on arr[1:] to make every element equal to arr[0].

Domain: non-empty integer lists (negatives allowed).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_operations_to_equalize"

CLARIFICATIONS = ["The array is non-empty; return an int (0 for a single element)."]

arrays = st.one_of(
    st.lists(st.integers(-10**6, 10**6), min_size=1, max_size=30),
    st.lists(st.integers(-2, 2), min_size=1, max_size=30),
    st.builds(lambda x, n: [x] * n, st.integers(-100, 100), st.integers(1, 10)),
)


@prop("The result is the total distance of the other elements from arr[0].", arr=arrays)
def matches_definition(f, arr):
    assert f(arr) == sum(abs(x - arr[0]) for x in arr[1:])


@prop("Reordering the elements after the first does not change the answer.", arr=arrays, data=st.data())
def order_invariant(f, arr, data):
    rest = data.draw(st.permutations(arr[1:]))
    assert f([arr[0]] + list(rest)) == f(arr)


@prop("Adding the same constant to every element does not change the answer.", arr=arrays, c=st.integers(-1000, 1000))
def shift_invariant(f, arr, c):
    assert f([x + c for x in arr]) == f(arr)


@prop("The target is arr[0], not some other value: moving arr[0] away from the rest changes the answer accordingly.",
      x=st.integers(-100, 100), rest=st.lists(st.integers(0, 10), min_size=1, max_size=10), gap=st.integers(1, 50))
def target_is_first(f, x, rest, gap):
    # Every other element is at least x + gap away above arr[0].
    others = [x + gap + r for r in rest]
    assert f([x] + others) == sum(gap + r for r in rest)


@prop("A single element or all-equal array needs 0 operations; the result is an int.", x=st.integers(-100, 100), n=st.integers(1, 10), arr=arrays)
def zero_cases(f, x, n, arr):
    assert f([x]) == 0
    assert f([x] * n) == 0
    assert isinstance(f(arr), int)

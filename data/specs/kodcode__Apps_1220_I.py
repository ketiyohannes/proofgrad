"""Spec for reverse_segments: reverse every maximal zero-free segment of the array, keeping zeros in place.

Domain: lists of 1..50 integers in 0..100.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "reverse_segments"

CLARIFICATIONS = [
    "Every maximal run of non-zero elements (before the first zero, between consecutive zeros, and after the last zero) is reversed; zeros stay at their positions.",
    "Return the result as a new list.",
]

arrays = st.one_of(
    st.lists(st.integers(0, 100), min_size=1, max_size=50),
    st.lists(st.sampled_from([0, 0, 1, 2, 3, 4, 5]), min_size=1, max_size=20),
    st.lists(st.integers(1, 100), min_size=1, max_size=20),
    st.lists(st.just(0), min_size=1, max_size=5),
)
distinct_nonzero = st.lists(st.integers(1, 100), unique=True, min_size=1, max_size=30)


@st.composite
def with_zeros(draw):
    vals = draw(distinct_nonzero)
    k = draw(st.integers(0, 6))
    positions = draw(st.lists(st.integers(0, len(vals)), min_size=k, max_size=k))
    arr = list(vals)
    for p in sorted(positions, reverse=True):
        arr.insert(p, 0)
    return arr


def oracle(a):
    out, seg = [], []
    for x in a + [0]:
        if x == 0:
            out.extend(reversed(seg))
            out.append(0)
            seg = []
        else:
            seg.append(x)
    return out[:-1]


@prop("The result is a list equal to the input with each zero-free segment reversed.", a=arrays)
def matches_definition(f, a):
    r = f(a)
    assert isinstance(r, list)
    assert r == oracle(a)


@prop("Zeros stay at exactly the same positions and the length is preserved.", a=with_zeros())
def zeros_fixed(f, a):
    r = f(a)
    assert len(r) == len(a)
    assert [i for i, x in enumerate(r) if x == 0] == [i for i, x in enumerate(a) if x == 0]


@prop("The result is a permutation of the input.", a=arrays)
def is_permutation(f, a):
    assert sorted(f(a)) == sorted(a)


@prop("An array without zeros is reversed entirely.", a=st.lists(st.integers(1, 100), min_size=1, max_size=50))
def no_zero_full_reverse(f, a):
    assert f(a) == a[::-1]


@prop("Applying the operation twice gives back the input.", a=with_zeros())
def involution(f, a):
    assert f(f(a)) == a


@prop("Segments after the last zero and before the first zero are also reversed.", a=with_zeros())
def edge_segments(f, a):
    r = f(a)
    if 0 in a:
        first = a.index(0)
        last = len(a) - 1 - a[::-1].index(0)
        assert r[:first] == a[:first][::-1]
        assert r[last + 1:] == a[last + 1:][::-1]
    else:
        assert r == a[::-1]

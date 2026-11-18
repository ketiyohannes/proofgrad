"""Spec for can_form_arithmetic_progression: True iff some permutation of nums has a constant consecutive difference.

Domain: integers in [-10000, 10000]; lists of length 2..30, plus the single-element list the unit tests check
(answer False). The empty list is not generated.
"""
import random
from itertools import permutations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_form_arithmetic_progression"

CLARIFICATIONS = [
    "A list with fewer than two elements is not an arithmetic progression: return False for it.",
    "A constant list (common difference 0) is an arithmetic progression.",
    "Return the bool True or False.",
]


def is_ap(seq):
    return all(seq[i + 1] - seq[i] == seq[1] - seq[0] for i in range(len(seq) - 1))


@st.composite
def progressions(draw):
    """A shuffled arithmetic progression; the step is biased toward 0 (constant) and +-1."""
    n = draw(st.one_of(st.just(2), st.just(3), st.integers(min_value=2, max_value=30)))
    d = draw(st.one_of(st.just(0), st.sampled_from([-1, 1]), st.integers(min_value=-600, max_value=600)))
    lo = -10000 - min(0, d * (n - 1))
    hi = 10000 - max(0, d * (n - 1))
    start = draw(st.integers(min_value=lo, max_value=hi))
    seq = [start + i * d for i in range(n)]
    return draw(st.permutations(seq))


@st.composite
def broken_progressions(draw):
    """A non-constant progression (length >= 3) with one interior term moved off the progression.

    The term is either moved strictly between its neighbours (min and max are unchanged, so the
    only candidate common difference is the original one, which the moved term violates) or
    replaced by a copy of a neighbour (a repeated value is only allowed in a constant progression).
    """
    n = draw(st.integers(min_value=3, max_value=20))
    d = draw(st.integers(min_value=1, max_value=500))
    start = draw(st.integers(min_value=-10000, max_value=10000 - d * (n - 1)))
    seq = [start + k * d for k in range(n)]
    i = draw(st.integers(min_value=1, max_value=n - 2))
    if d >= 2 and draw(st.booleans()):
        seq[i] = draw(st.integers(min_value=seq[i - 1] + 1, max_value=seq[i + 1] - 1).filter(lambda v: v != seq[i]))
    else:
        seq[i] = seq[i + draw(st.sampled_from([-1, 1]))]
    if draw(st.booleans()):
        seq = [-v for v in seq]
    return draw(st.permutations(seq))


small_lists = st.one_of(
    st.lists(st.integers(min_value=-6, max_value=6), min_size=2, max_size=6),
    st.lists(st.sampled_from([0, 1, 2]), min_size=2, max_size=6),
)


@prop("On short lists of small integers (length 2..6), the result matches a brute-force check of all permutations.",
      nums=small_lists)
def matches_brute_force(f, nums):
    assert f(nums) is any(is_ap(p) for p in permutations(nums))


@prop("Any shuffled arithmetic progression (including constant sequences and negative steps) gives True.",
      nums=progressions())
def progressions_accepted(f, nums):
    assert f(nums) is True


@prop("Moving one interior term of a non-constant progression off the progression gives False.",
      nums=broken_progressions())
def broken_progressions_rejected(f, nums):
    assert f(nums) is False


@prop("Any two-element list gives True.", a=st.integers(-10000, 10000), b=st.integers(-10000, 10000))
def pairs_accepted(f, a, b):
    assert f([a, b]) is True


@prop("A list with a single element gives False.", a=st.integers(-10000, 10000))
def singleton_rejected(f, a):
    assert f([a]) is False

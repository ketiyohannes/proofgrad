"""Spec for has_increasing_triplet: per test case, "YES" iff the sequence has a strictly increasing subsequence of length 3.

Domain: T >= 1 test cases given as (N, A) tuples with N == len(A) >= 1 and 1 <= A_i <= 100000.
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "has_increasing_triplet"

CLARIFICATIONS = [
    "test_cases is a list of T tuples (N, A) where A is the list of N numbers.",
    "Return a list with one string per test case, in input order: \"YES\" if there are indices i < j < k with A[i] < A[j] < A[k], otherwise \"NO\".",
]


def brute(a):
    return "YES" if any(x < y < z for x, y, z in combinations(a, 3)) else "NO"


@st.composite
def sequence(draw, max_size=10):
    shape = draw(st.sampled_from(["random", "small", "sorted", "reverse", "equal"]))
    hi = 3 if shape == "small" else 100000
    a = draw(st.lists(st.integers(1, hi), min_size=1, max_size=max_size))
    if shape == "sorted":
        a.sort()
    elif shape == "reverse":
        a.sort(reverse=True)
    elif shape == "equal":
        a = [a[0]] * len(a)
    return a


def as_cases(seqs):
    return len(seqs), [(len(a), a) for a in seqs]


@prop("Each answer agrees with checking every triple of positions.", seqs=st.lists(sequence(), min_size=1, max_size=5))
def matches_brute_force(f, seqs):
    t, cases = as_cases(seqs)
    assert f(t, cases) == [brute(a) for a in seqs]


@prop("The result is a list of T strings, each \"YES\" or \"NO\".", seqs=st.lists(sequence(30), min_size=1, max_size=6))
def output_shape(f, seqs):
    t, cases = as_cases(seqs)
    r = f(t, cases)
    assert isinstance(r, list) and len(r) == t
    assert all(x in ("YES", "NO") for x in r)


@prop("Non-increasing sequences (including all-equal ones and sequences shorter than 3) give \"NO\".",
      a=st.lists(st.integers(1, 100000), min_size=1, max_size=40).map(lambda a: sorted(a, reverse=True)))
def non_increasing_is_no(f, a):
    assert f(1, [(len(a), a)]) == ["NO"]


@prop("A sequence that contains three strictly increasing values in order (possibly far apart) gives \"YES\".",
      data=st.data(), noise=st.lists(st.integers(1, 100000), max_size=20), vals=st.lists(st.integers(1, 100000), min_size=3, max_size=3, unique=True))
def planted_triplet_is_yes(f, data, noise, vals):
    x, y, z = sorted(vals)
    a = list(noise)
    positions = sorted(data.draw(st.lists(st.integers(0, len(a)), min_size=3, max_size=3)))
    for offset, (pos, v) in enumerate(zip(positions, (x, y, z))):
        a.insert(pos + offset, v)
    assert f(1, [(len(a), a)]) == ["YES"]


@prop("Answers are per test case: a batch gives the same answers as the cases run one by one.",
      seqs=st.lists(sequence(), min_size=2, max_size=6))
def cases_independent(f, seqs):
    t, cases = as_cases(seqs)
    assert f(t, cases) == [f(1, [c])[0] for c in cases]

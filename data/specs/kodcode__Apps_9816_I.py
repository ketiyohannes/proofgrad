"""Spec for vase_sequence: any list of n integers in which every pair of adjacent elements has an even sum.

Domain: 1 <= n <= 100.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "vase_sequence"

EXCLUDE_REASON = (
    "The statement asks for 'any' vase sequence (and contradicts itself, calling [3, 5, 7] invalid and printing 1 for n = 1), "
    "while the reference and unit tests demand exactly [2, 4, ..., 2n]."
)

CLARIFICATIONS = ["Return the sequence as a list of n ints."]


@prop("The result is a list of n ints.", n=st.integers(1, 100))
def output_shape(f, n):
    r = f(n)
    assert isinstance(r, list) and len(r) == n
    assert all(isinstance(x, int) for x in r)


@prop("Every pair of adjacent elements has an even sum.", n=st.integers(1, 100))
def adjacent_sums_even(f, n):
    r = f(n)
    assert all((r[i] + r[i + 1]) % 2 == 0 for i in range(len(r) - 1))

"""Spec for letter_combinations: every string formed by picking one mapped letter per digit (phone keypad).

Domain: strings of digits 2..9, length 0..5. Output order is not checked.
"""
import itertools

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "letter_combinations"

CLARIFICATIONS = [
    "Return a list of strings with no duplicates; the empty string input returns an empty list.",
]

KEYS = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
digits = st.text(alphabet="23456789", min_size=1, max_size=5)


def expected(ds):
    return sorted("".join(p) for p in itertools.product(*(KEYS[d] for d in ds)))


@prop("The result is a list of strings with exactly one character per digit, each from that digit's letters.", ds=digits)
def each_valid(f, ds):
    r = f(ds)
    assert isinstance(r, list)
    for w in r:
        assert isinstance(w, str) and len(w) == len(ds)
        assert all(c in KEYS[d] for c, d in zip(w, ds))


@prop("The result has no duplicates and its size is the product of the letter counts.", ds=digits)
def count_and_unique(f, ds):
    r = f(ds)
    n = 1
    for d in ds:
        n *= len(KEYS[d])
    assert len(r) == n and len(set(r)) == n


@prop("The result contains exactly all combinations (in any order).", ds=digits)
def all_combinations(f, ds):
    assert sorted(f(ds)) == expected(ds)


@prop("A single digit gives its mapped letters.", d=st.sampled_from("23456789"))
def single_digit(f, d):
    assert sorted(f(d)) == sorted(KEYS[d])


@prop("Digits 7 and 9 map to four letters each.", ds=st.text(alphabet="79", min_size=1, max_size=3))
def four_letter_keys(f, ds):
    assert sorted(f(ds)) == expected(ds)


@prop("The empty input gives an empty list.", dummy=st.just(None))
def empty_input(f, dummy):
    assert f("") == []

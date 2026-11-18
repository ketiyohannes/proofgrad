"""Spec for letter_combinations: every string formed by picking one keypad letter per digit, in any order.

Domain: strings of digits 2-9 (length 0..5). The empty string gives [].
Keypad: 2 abc, 3 def, 4 ghi, 5 jkl, 6 mno, 7 pqrs, 8 tuv, 9 wxyz.
"""
from itertools import product

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "letter_combinations"

CLARIFICATIONS = ["Return a list of strings; for an empty input string return an empty list."]

KEYPAD = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
digits = st.text(alphabet="23456789", min_size=1, max_size=5)


@prop("The result contains exactly the combinations of one letter per digit (as a set).", d=digits)
def correct_set(f, d):
    r = f(d)
    assert isinstance(r, list)
    assert set(r) == {"".join(p) for p in product(*(KEYPAD[c] for c in d))}


@prop("No combination is listed twice.", d=digits)
def no_duplicates(f, d):
    r = f(d)
    assert len(r) == len(set(r))


@prop("The number of combinations is the product of the letter counts of the digits.", d=digits)
def correct_count(f, d):
    n = 1
    for c in d:
        n *= len(KEYPAD[c])
    assert len(f(d)) == n


@prop("Each combination has one letter per digit, taken from that digit's keys in order.", d=digits)
def letters_match_digits(f, d):
    for s in f(d):
        assert isinstance(s, str) and len(s) == len(d)
        assert all(ch in KEYPAD[dg] for ch, dg in zip(s, d))


@prop("The empty string gives [] and a single digit gives its letters.", c=st.sampled_from("23456789"))
def base_cases(f, c):
    assert f("") == []
    assert sorted(f(c)) == list(KEYPAD[c])

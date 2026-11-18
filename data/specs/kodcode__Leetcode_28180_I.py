"""Spec for parse_chemical_formula: map each element symbol to its total atom count.

Domain: valid formulas built from element symbols (an uppercase letter optionally followed by one
lowercase letter, as in the unit tests' "NaCl"), each optionally followed by a positive count
written without leading zeros. Elements may repeat; their counts are summed.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "parse_chemical_formula"

CLARIFICATIONS = [
    "An element symbol is an uppercase letter optionally followed by lowercase letters (e.g. \"Na\", \"Cl\").",
    "If the same element appears several times, return the sum of its counts.",
    "Return a dict mapping each element symbol to an int count; an empty formula gives an empty dict.",
]

SYMBOLS = ["H", "O", "C", "N", "S", "P", "K", "Na", "Cl", "He", "Fe", "Mg", "Ca", "Co"]

count_part = st.one_of(
    st.just(None),
    st.integers(min_value=1, max_value=9),
    st.integers(min_value=10, max_value=999),
)


@st.composite
def formulas(draw, symbols=st.sampled_from(SYMBOLS), max_parts=8):
    parts = draw(st.lists(st.tuples(symbols, count_part), min_size=1, max_size=max_parts))
    text = "".join(sym + ("" if c is None else str(c)) for sym, c in parts)
    expected = Counter()
    for sym, c in parts:
        expected[sym] += 1 if c is None else c
    return text, dict(expected)


@prop("The result is a dict equal to the total atom count of every element.", case=formulas())
def correct_counts(f, case):
    text, expected = case
    r = f(text)
    assert isinstance(r, dict)
    assert r == expected


@prop("The keys are exactly the element symbols that occur in the formula.", case=formulas())
def correct_keys(f, case):
    text, expected = case
    assert set(f(text)) == set(expected)


@prop("Elements written without a number count as one atom each.",
      syms=st.lists(st.sampled_from(SYMBOLS), unique=True, min_size=1, max_size=8))
def implicit_one(f, syms):
    assert f("".join(syms)) == {s: 1 for s in syms}


@prop("Multi-digit counts are read as whole numbers.",
      sym=st.sampled_from(SYMBOLS), n=st.integers(min_value=10, max_value=10**6))
def multi_digit(f, sym, n):
    r = f(sym + str(n))
    assert r == {sym: n}


@prop("Two-letter symbols (uppercase + lowercase) are single elements, distinct from their first letter.",
      case=formulas(symbols=st.sampled_from(["Na", "N", "Cl", "C", "Co", "He", "H"]), max_parts=6))
def two_letter_symbols(f, case):
    text, expected = case
    assert f(text) == expected


@prop("A repeated element accumulates the counts of all its occurrences.",
      sym=st.sampled_from(SYMBOLS), counts=st.lists(st.integers(min_value=1, max_value=20), min_size=2, max_size=4),
      sep=st.sampled_from(["O", "H", "Cl"]))
def repeated_element_sums(f, sym, counts, sep):
    if sym == sep:
        sep = "Mg"
    text = sep.join(sym + str(c) for c in counts)
    r = f(text)
    assert r[sym] == sum(counts)
    assert r[sep] == len(counts) - 1

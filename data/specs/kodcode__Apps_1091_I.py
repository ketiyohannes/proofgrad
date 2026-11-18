"""Spec for is_scrambled_palindrome: True iff the string's ASCII letters (case-insensitive, all other characters ignored) can be rearranged into a palindrome.

Domain: non-empty strings of ASCII letters, spaces, punctuation and digits containing at least one letter
(strings with no letters are not generated: the statement does not say what they should return).
"""
import random
import string
from itertools import permutations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_scrambled_palindrome"

CLARIFICATIONS = [
    "Return the bool True or False.",
]

NOISE = " ,.!?;:'-@#0123456789"
noise_chars = st.text(alphabet=NOISE, max_size=5)


def letters_of(s):
    return [c.lower() for c in s if c in string.ascii_letters]


def brute_can_be_palindrome(letters):
    return any(list(p) == list(p)[::-1] for p in set(permutations(letters)))


def dress(draw, letters):
    """Randomise the case of each letter and intersperse non-letter characters."""
    out = []
    for ch in letters:
        out.append(draw(noise_chars))
        out.append(ch.upper() if draw(st.booleans()) else ch)
    out.append(draw(noise_chars))
    return "".join(out)


@st.composite
def mixed_strings(draw, max_letters=7):
    """At least one letter; mixes general letters with single-letter repeats and few distinct letters."""
    alphabet = draw(st.sampled_from(["a", "ab", "abc", "abcde"]))
    letters = draw(st.lists(st.sampled_from(alphabet), min_size=1, max_size=max_letters))
    return dress(draw, letters)


@st.composite
def scrambled_palindromes(draw):
    half = draw(st.lists(st.sampled_from(string.ascii_lowercase), max_size=10))
    middle = draw(st.lists(st.sampled_from(string.ascii_lowercase), max_size=1))
    letters = half + middle + half[::-1] or ["a"]
    random.Random(draw(st.integers())).shuffle(letters)
    return dress(draw, letters)


@st.composite
def non_palindromes(draw):
    """At least two distinct letters occur an odd number of times, so no rearrangement is a palindrome."""
    pool = draw(st.lists(st.sampled_from(string.ascii_lowercase), min_size=2, max_size=6, unique=True))
    odd_count = draw(st.integers(min_value=2, max_value=len(pool)))
    letters = []
    for i, ch in enumerate(pool):
        letters.extend([ch] * (2 * draw(st.integers(min_value=0, max_value=2)) + (1 if i < odd_count else 0)))
    random.Random(draw(st.integers())).shuffle(letters)
    return dress(draw, letters)


@prop("The result matches a brute-force search over all rearrangements of the letters (lowercased, non-letters dropped).",
      s=mixed_strings())
def matches_brute_force(f, s):
    assert f(s) is brute_can_be_palindrome(letters_of(s))


@prop("Any shuffled palindrome (with random case and interspersed non-letters) gives True.", s=scrambled_palindromes())
def palindromes_accepted(f, s):
    assert f(s) is True


@prop("A string in which two or more letters occur an odd number of times gives False.", s=non_palindromes())
def odd_letters_rejected(f, s):
    assert f(s) is False


@prop("The answer is case-insensitive: swapping the case of every letter does not change it.",
      s=mixed_strings(max_letters=12))
def case_insensitive(f, s):
    assert f(s.swapcase()) is f(s)


@prop("Spaces, punctuation and digits are ignored: removing or inserting them does not change the answer.",
      s=mixed_strings(max_letters=12), seed=st.integers())
def ignores_non_letters(f, s, seed):
    rng = random.Random(seed)
    expected = f(s)
    assert f("".join(c for c in s if c in string.ascii_letters)) is expected
    assert f("".join(c + rng.choice(NOISE) for c in s)) is expected

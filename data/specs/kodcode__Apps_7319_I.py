"""Spec for is_anagram_of_palindrome: True iff some rearrangement of the string is a palindrome.

Domain: strings of lowercase ASCII letters (length 0..1000), including the empty string.
"""
from itertools import permutations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_anagram_of_palindrome"

CLARIFICATIONS = [
    "The empty string counts as an anagram of a palindrome (return True).",
    "Return a bool (True or False).",
]

lower = "abcdefghijklmnopqrstuvwxyz"

any_text = st.one_of(
    st.text(alphabet="ab", max_size=30),
    st.text(alphabet="abc", max_size=30),
    st.text(alphabet=lower, max_size=40),
    st.builds(lambda c, n: c * n, st.sampled_from("az"), st.integers(0, 50)),
)
tiny_text = st.one_of(st.text(alphabet="abc", max_size=6), st.text(alphabet="ab", max_size=6), st.text(alphabet=lower, max_size=5))


def brute(s):
    return any("".join(p) == "".join(p)[::-1] for p in set(permutations(s)))


@st.composite
def shuffled_palindromes(draw):
    half = draw(st.text(alphabet=draw(st.sampled_from(["ab", "abc", lower])), max_size=15))
    middle = draw(st.sampled_from(["", "a", "q", "z"]))
    pal = half + middle + half[::-1]
    return "".join(draw(st.permutations(list(pal))))


@st.composite
def two_odd_counts(draw):
    # Two distinct letters get odd counts, all others even: no palindrome arrangement exists.
    a, b = draw(st.lists(st.sampled_from(lower), min_size=2, max_size=2, unique=True))
    chars = [a] * (2 * draw(st.integers(0, 5)) + 1) + [b] * (2 * draw(st.integers(0, 5)) + 1)
    for c in draw(st.lists(st.sampled_from(lower), max_size=8)):
        chars += [c, c]
    if draw(st.booleans()):
        # A third odd-count letter keeps the answer False.
        c = draw(st.sampled_from([x for x in lower if x not in (a, b)]))
        chars += [c] * (2 * draw(st.integers(0, 3)) + 1)
    return "".join(draw(st.permutations(chars)))


@prop("The result agrees with trying every rearrangement of short strings.", s=tiny_text)
def matches_brute_force(f, s):
    assert f(s) == brute(s)


@prop("Any shuffle of a palindrome is reported True.", s=shuffled_palindromes())
def shuffled_palindrome_true(f, s):
    assert f(s) is True


@prop("A string in which two or more letters occur an odd number of times is reported False.", s=two_odd_counts())
def two_odd_letters_false(f, s):
    assert f(s) is False


@prop("The result is a bool and does not depend on the order of the characters.", s=any_text, data=st.data())
def bool_and_order_invariant(f, s, data):
    r = f(s)
    assert isinstance(r, bool)
    t = "".join(data.draw(st.permutations(list(s))))
    assert f(t) == r


@prop("The empty string and single characters are True; two different letters are False.", c=st.sampled_from(lower), d=st.sampled_from(lower))
def small_cases(f, c, d):
    assert f("") is True
    assert f(c) is True
    assert f(c + d) is (c == d)

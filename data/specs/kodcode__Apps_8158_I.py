"""Spec for can_form_palindrome: True iff the letters and digits of s, ignoring case, can be rearranged into a palindrome.

Domain: ASCII strings (letters, digits, spaces, punctuation), including the empty string.
Only letters and digits are considered; letters are compared case-insensitively.
"""
from itertools import permutations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_form_palindrome"

CLARIFICATIONS = [
    "Only letters and digits are considered (digits count as characters); everything else is ignored, and letters are case-insensitive.",
    "A string with no letters or digits (including the empty string) returns True.",
    "Return a bool.",
]

junk = " ,.!?'-:;"
letters = "abcABC"


def normalize(s):
    return [c.lower() for c in s if c.isascii() and c.isalnum()]


def brute(s):
    return any(list(p) == list(p)[::-1] for p in set(permutations(normalize(s))))


tiny = st.one_of(st.text(alphabet="aAbB1 ,", max_size=6), st.text(alphabet="abcC2!", max_size=6))
wide = st.one_of(
    st.text(alphabet=letters + "12" + junk, max_size=40),
    st.text(alphabet="aAbB ", max_size=40),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + junk, max_size=40),
)


def sprinkle(data, s):
    chars = list(s)
    for _ in range(data.draw(st.integers(0, 5))):
        chars.insert(data.draw(st.integers(0, len(chars))), data.draw(st.sampled_from(junk)))
    return "".join(chars)


def random_case(data, s):
    return "".join(c.upper() if data.draw(st.booleans()) else c for c in s)


@prop("The result agrees with trying every rearrangement of the (normalized) characters of short strings.", s=tiny)
def matches_brute_force(f, s):
    assert f(s) == brute(s)


@prop("A shuffled palindrome with random capitalization and inserted spaces/punctuation is reported True.",
      half=st.text(alphabet="abcdz19", max_size=12), middle=st.sampled_from(["", "x", "7"]), data=st.data())
def disguised_palindrome_true(f, half, middle, data):
    chars = data.draw(st.permutations(list(half + middle + half[::-1])))
    s = sprinkle(data, random_case(data, "".join(chars)))
    assert f(s) is True


@prop("If two different characters (letters ignoring case, or digits) occur an odd number of times, the result is False.",
      pair=st.lists(st.sampled_from("abcz1"), min_size=2, max_size=2, unique=True), evens=st.text(alphabet="abcz1", max_size=6),
      i=st.integers(0, 3), j=st.integers(0, 3), data=st.data())
def two_odd_false(f, pair, evens, i, j, data):
    a, b = pair
    chars = [a] * (2 * i + 1) + [b] * (2 * j + 1) + [c for c in evens for _ in range(2)]
    s = sprinkle(data, random_case(data, "".join(data.draw(st.permutations(chars)))))
    assert f(s) is False


@prop("Changing capitalization or adding spaces/punctuation does not change the result.", s=wide, data=st.data())
def case_and_punctuation_ignored(f, s, data):
    r = f(s)
    assert isinstance(r, bool)
    assert f(sprinkle(data, s.swapcase())) == r


@prop("Digits count as characters: a lone digit pair mismatch such as '12' is False, '121' is True.",
      d=st.sampled_from("0123456789"), e=st.sampled_from("0123456789"))
def digits_count(f, d, e):
    assert f(d + e) is (d == e)
    assert f(d + e + d) is True


@prop("Strings with no letters or digits, including the empty string, give True.", s=st.text(alphabet=junk, max_size=10))
def nothing_to_arrange(f, s):
    assert f(s) is True
    assert f("") is True

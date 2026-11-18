"""Spec for is_palindrome: True iff s reads the same both ways after lowercasing and dropping non-alphanumeric characters.

Domain: ASCII strings, including the empty string. Alphanumeric means ASCII letters and digits.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_palindrome"

CLARIFICATIONS = [
    "Alphanumeric means ASCII letters and digits; a string with no alphanumeric characters (including the empty string) is a palindrome.",
    "Return a bool.",
]

alnum = "abcABC019"
junk = " ,.:;!?'_-"
text = st.one_of(
    st.text(alphabet="aAbB1 ,", max_size=12),
    st.text(alphabet=alnum + junk, max_size=20),
    st.text(alphabet="".join(chr(c) for c in range(32, 127)), max_size=20),
)


def cleaned(s):
    return [c.lower() for c in s if c.isascii() and c.isalnum()]


def sprinkle(data, s):
    chars = list(s)
    for _ in range(data.draw(st.integers(0, 5))):
        chars.insert(data.draw(st.integers(0, len(chars))), data.draw(st.sampled_from(junk)))
    return "".join(chars)


@prop("The result agrees with comparing the cleaned, lowercased string with its reverse.", s=text)
def matches_definition(f, s):
    c = cleaned(s)
    assert f(s) == (c == c[::-1])


@prop("A palindrome disguised with random capitalization and inserted punctuation/spaces is True.",
      half=st.text(alphabet="abz09", max_size=10), mid=st.sampled_from(["", "q", "5"]), data=st.data())
def disguised_palindrome_true(f, half, mid, data):
    s = half + mid + half[::-1]
    s = "".join(c.upper() if data.draw(st.booleans()) else c for c in s)
    assert f(sprinkle(data, s)) is True


@prop("A cleaned string that differs from its reverse is False, whatever punctuation is added.",
      pre=st.text(alphabet="ab1", max_size=5), a=st.sampled_from("ab1"), b=st.sampled_from("cd2"), data=st.data())
def non_palindrome_false(f, pre, a, b, data):
    s = pre + a + b + pre[::-1]
    assert f(sprinkle(data, s)) is False


@prop("Swapping case and adding punctuation does not change the result; the result is a bool.", s=text, data=st.data())
def case_and_punctuation_ignored(f, s, data):
    r = f(s)
    assert isinstance(r, bool)
    assert f(sprinkle(data, s.swapcase())) == r


@prop("Strings with no alphanumeric characters (including the empty string) are True.", s=st.text(alphabet=junk, max_size=10))
def no_alnum_true(f, s):
    assert f(s) is True
    assert f("") is True

"""Spec for concatenate_words: the sentence with every space removed.

Domain: strings made of space characters and printable non-whitespace ASCII characters
(letters, digits, punctuation), including the empty string and all-space strings.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "concatenate_words"

CLARIFICATIONS = [
    "Leading, trailing and repeated spaces are all removed; non-space characters are kept unchanged and in order.",
]

NON_SPACE = "abcXYZ019@!.,-_#"
word = st.text(alphabet=NON_SPACE, min_size=1, max_size=6)
sentences = st.one_of(
    st.text(alphabet=NON_SPACE + "   ", max_size=30),
    st.builds(lambda ws, gaps, lead, trail: " " * lead + "".join(w + " " * g for w, g in zip(ws, gaps)).rstrip(" ") + " " * trail,
              st.lists(word, max_size=6), st.lists(st.integers(1, 4), min_size=6, max_size=6),
              st.integers(0, 3), st.integers(0, 3)),
)


def without_spaces(s):
    return "".join(c for c in s if c != " ")


@prop("The result equals the input with all spaces deleted.", s=sentences)
def deletes_all_spaces(f, s):
    assert f(s) == without_spaces(s)


@prop("The result is a str containing no spaces.", s=sentences)
def no_spaces_left(f, s):
    r = f(s)
    assert isinstance(r, str) and " " not in r


@prop("A string without spaces is returned unchanged.", s=st.text(alphabet=NON_SPACE, max_size=20))
def no_space_unchanged(f, s):
    assert f(s) == s


@prop("The empty string and all-space strings give the empty string.", n=st.integers(min_value=0, max_value=10))
def only_spaces(f, n):
    assert f(" " * n) == ""


@prop("Joining two sentences with spaces concatenates their results.", a=sentences, b=sentences, g=st.integers(1, 3))
def concatenation(f, a, b, g):
    assert f(a + " " * g + b) == f(a) + f(b)

"""Spec for concatenate_k_lexicographically: concatenation of the k lexicographically smallest words, in sorted order.

Domain: words is a list of distinct lowercase strings (possibly empty); k is a non-negative integer.
Lexicographic order is Python's default string ordering. If k > len(words) a ValueError is raised.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "concatenate_k_lexicographically"

CLARIFICATIONS = [
    "Raise a ValueError if k is greater than the number of words.",
    "Return the empty string when k is 0.",
]

word_lists = st.one_of(
    st.lists(st.text(alphabet="abc", min_size=1, max_size=4), unique=True, max_size=8),
    st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8), unique=True, max_size=8),
)


@st.composite
def valid_case(draw):
    words = draw(word_lists)
    k = draw(st.integers(min_value=0, max_value=len(words)))
    return words, k


@prop("The result is the concatenation of the k lexicographically smallest words in ascending order.", c=valid_case())
def correct_concatenation(f, c):
    words, k = c
    assert f(words, k) == "".join(sorted(words)[:k])


@prop("The result is a str whose length is the total length of the k smallest words.", c=valid_case())
def length_matches(f, c):
    words, k = c
    r = f(words, k)
    assert isinstance(r, str)
    assert len(r) == sum(len(w) for w in sorted(words)[:k])


@prop("The answer does not depend on the order of the input list.", c=valid_case(), data=st.data())
def order_invariant(f, c, data):
    words, k = c
    assert f(list(data.draw(st.permutations(words))), k) == f(words, k)


@prop("k = 0 gives the empty string and k = len(words) concatenates all words in sorted order.", words=word_lists)
def boundary_k(f, words):
    assert f(words, 0) == ""
    assert f(words, len(words)) == "".join(sorted(words))


@prop("k greater than the number of words raises ValueError.", words=word_lists, extra=st.integers(min_value=1, max_value=3))
def too_large_k_raises(f, words, extra):
    try:
        f(words, len(words) + extra)
    except ValueError:
        return
    raise AssertionError("expected ValueError")

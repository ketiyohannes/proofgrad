"""Spec for truncate_sentence: keep only the first k words of a sentence, joined by single spaces.

Domain: s is a non-empty sentence of words made of non-whitespace characters, separated by
single spaces, with no leading or trailing spaces; k >= 1. When k is at least the number of
words the whole sentence is returned, following the reference solution.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "truncate_sentence"

CLARIFICATIONS = [
    "k is at least 1. If k is greater than or equal to the number of words, return the whole sentence.",
    "Return the result as a str.",
]

word = st.one_of(
    st.text(alphabet="abcXYZ019.,!?'-", min_size=1, max_size=6),
    st.sampled_from(["a", "A", "Hello", "hello", "x1", "!"]),
)

word_lists = st.one_of(
    st.lists(word, min_size=1, max_size=10),
    st.builds(lambda w, n: [w] * n, word, st.integers(min_value=1, max_value=6)),
    st.lists(st.sampled_from(["a", "b"]), min_size=1, max_size=10),
)


@st.composite
def sentence_and_k(draw):
    words = draw(word_lists)
    k = draw(st.one_of(st.just(1), st.just(len(words)), st.integers(min_value=1, max_value=len(words))))
    return words, k


@prop("The result is a str which, split on single spaces, gives exactly the first k words.", case=sentence_and_k())
def first_k_words(f, case):
    words, k = case
    r = f(" ".join(words), k)
    assert isinstance(r, str)
    assert r.split(" ") == words[:k]


@prop("The result is a prefix of s that ends at a word boundary (end of s or just before a space).", case=sentence_and_k())
def is_prefix_at_word_boundary(f, case):
    words, k = case
    s = " ".join(words)
    r = f(s, k)
    assert s.startswith(r)
    assert len(r) == len(s) or s[len(r)] == " "


@prop("The result has no leading or trailing space.", case=sentence_and_k())
def no_outer_spaces(f, case):
    words, k = case
    r = f(" ".join(words), k)
    assert r == r.strip(" ")


@prop("The result contains exactly k - 1 spaces (k words).", case=sentence_and_k())
def exactly_k_words(f, case):
    words, k = case
    assert f(" ".join(words), k).count(" ") == k - 1


@prop("When k is at least the number of words, the whole sentence is returned.",
      words=word_lists, extra=st.integers(min_value=0, max_value=5))
def whole_sentence_when_k_large(f, words, extra):
    s = " ".join(words)
    assert f(s, len(words) + extra) == s

"""Spec for count_characters: total length of the words that can be spelled from the letters of chars.

Domain: words are non-empty lowercase strings; chars is a (possibly empty) lowercase string;
words may be empty. Each word is checked independently against the full multiset of chars.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_characters"

CLARIFICATIONS = [
    "Each word is checked independently: a word is good if every letter occurs in it at most as many times as in chars.",
    "Duplicate words in the list are each counted.",
]

small_word = st.text(alphabet="abcd", min_size=1, max_size=6)
word_lists = st.lists(st.one_of(small_word, st.text(alphabet="abcdefxyz", min_size=1, max_size=8)), max_size=8)
chars_strs = st.one_of(st.text(alphabet="abcd", max_size=12), st.text(alphabet="abcdefxyz", max_size=15))


def formable(word, chars):
    have = Counter(chars)
    return all(have[c] >= n for c, n in Counter(word).items())


@prop("The result is an int equal to the total length of all formable words.", words=word_lists, chars=chars_strs)
def matches_definition(f, words, chars):
    r = f(words, chars)
    assert isinstance(r, int)
    assert r == sum(len(w) for w in words if formable(w, chars))


@prop("A word needing a letter more times than chars provides is not counted.",
      letter=st.sampled_from("abcd"), times=st.integers(min_value=1, max_value=4), other=st.text(alphabet="xyz", max_size=4))
def multiplicity_respected(f, letter, times, other):
    chars = letter * times + other
    assert f([letter * (times + 1)], chars) == 0
    assert f([letter * times], chars) == times


@prop("Letters are reusable across different words: the result is additive over the list.",
      a=word_lists, b=word_lists, chars=chars_strs)
def additive(f, a, b, chars):
    assert f(a + b, chars) == f(a, chars) + f(b, chars)


@prop("Every permutation of chars itself, and of any sub-multiset of it, is formable.",
      data=st.data(), chars=st.text(alphabet="abcde", min_size=1, max_size=10))
def submultisets_formable(f, data, chars):
    words = []
    for _ in range(data.draw(st.integers(min_value=0, max_value=4))):
        letters = data.draw(st.permutations(list(chars)))
        k = data.draw(st.integers(min_value=1, max_value=len(chars)))
        words.append("".join(letters[:k]))
    assert f(words, chars) == sum(len(w) for w in words)


@prop("An empty word list gives 0, and empty chars gives 0.", words=word_lists, chars=chars_strs)
def empty_inputs(f, words, chars):
    assert f([], chars) == 0
    assert f(words, "") == 0

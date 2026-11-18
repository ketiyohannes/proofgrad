"""Spec for find_shortest_word_length: the length of the shortest space-separated word.

Domain: non-empty strings of 1..12 words made of letters, separated by single spaces.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_shortest_word_length"

word = st.text(alphabet="abcdeXYZ", min_size=1, max_size=10)
word_lists = st.one_of(
    st.lists(word, min_size=1, max_size=12),
    st.lists(st.text(alphabet="ab", min_size=2, max_size=3), min_size=1, max_size=8),
)


@prop("The result equals the length of the shortest word.", words=word_lists)
def shortest_length(f, words):
    assert f(" ".join(words)) == min(len(w) for w in words)


@prop("Some word has exactly the returned length and none is shorter.", words=word_lists)
def attained_and_minimal(f, words):
    n = f(" ".join(words))
    assert isinstance(n, int)
    assert n in [len(w) for w in words]
    assert all(len(w) >= n for w in words)


@prop("The order of the words does not matter.", words=word_lists, seed=st.randoms(use_true_random=False))
def order_invariant(f, words, seed):
    shuffled = words[:]
    seed.shuffle(shuffled)
    assert f(" ".join(shuffled)) == f(" ".join(words))


@prop("A shortest word at the end of the sentence is counted.",
      words=st.lists(st.text(alphabet="abc", min_size=3, max_size=8), max_size=8), last=st.text(alphabet="xyz", min_size=1, max_size=2))
def shortest_last(f, words, last):
    assert f(" ".join(words + [last])) == len(last)


@prop("A single word gives its own length.", w=word)
def single_word(f, w):
    assert f(w) == len(w)

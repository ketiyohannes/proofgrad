"""Spec for shortest_completing_word: the shortest word containing every letter of target (case-insensitive, with multiplicity).

Domain: words is a non-empty list of lowercase alphabetic words; target is an ASCII string of letters,
digits, spaces and punctuation of length >= 1. Non-letters in target are ignored; letters are
compared case-insensitively.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "shortest_completing_word"

CLARIFICATIONS = [
    "If several completing words are equally short, return the one that appears first in words.",
    "Return None if no word is a completing word.",
]

word = st.text(alphabet="abcst", min_size=1, max_size=7)
word_lists = st.lists(word, min_size=1, max_size=10)
target = st.text(alphabet="abcstABCST0123 .,!", min_size=1, max_size=8)


def letters(t):
    return [c.lower() for c in t if c.isascii() and c.isalpha()]


def completes(w, t):
    need = letters(t)
    return all(w.count(c) >= need.count(c) for c in set(need))


def expected(words, t):
    best = None
    for w in words:
        if completes(w, t) and (best is None or len(w) < len(best)):
            best = w
    return best


@prop("The result is the first shortest completing word, or None if there is none.", words=word_lists, t=target)
def matches_definition(f, words, t):
    assert f(words, t) == expected(words, t)


@prop("A returned word is from the list and contains every target letter with multiplicity.", words=word_lists, t=target)
def result_completes(f, words, t):
    r = f(words, t)
    if r is not None:
        assert r in words
        assert completes(r, t)


@prop("No completing word in the list is shorter than the result, and None only if no word completes.", words=word_lists, t=target)
def result_is_shortest(f, words, t):
    r = f(words, t)
    lengths = [len(w) for w in words if completes(w, t)]
    if r is None:
        assert not lengths
    else:
        assert len(r) == min(lengths)


@prop("Among equally short completing words the earliest is returned.", w=word, data=st.data())
def first_on_ties(f, w, data):
    shuffled = "".join(data.draw(st.permutations(w)))
    assert f([w, shuffled], w.upper()) == w


@prop("Case, digits, spaces and punctuation in target do not matter.", words=word_lists, t=target)
def target_normalized(f, words, t):
    stripped = "".join(letters(t))
    assert f(words, t) == f(words, stripped.upper() + "1 2!") == f(words, stripped + "7")


@prop("A target letter missing from every word gives None.", words=word_lists, extra=target)
def missing_letter_none(f, words, extra):
    assert f(words, extra + "z") is None

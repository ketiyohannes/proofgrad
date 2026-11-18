"""Spec for group_anagrams: partition the words into groups of mutual anagrams.

Domain: lists of distinct non-empty strings over a small mixed-case alphabet, including the empty list.
Anagrams are case-sensitive. Order (from the reference and unit tests): groups appear in the order
of their first word in the input; inside a group, words keep their input order.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "group_anagrams"

CLARIFICATIONS = [
    "Letters are case-sensitive: 'bAt' and 'tab' are not anagrams.",
    "A word with no anagram in the list forms a group by itself; return [] for an empty list.",
    "Order the groups by the position of their first word in the input, and keep the words inside each group in input order.",
]


@st.composite
def word_lists(draw):
    bases = draw(st.lists(st.text(alphabet="abcA", min_size=1, max_size=4), min_size=0, max_size=5))
    words = []
    for b in bases:
        words.append(b)
        for _ in range(draw(st.integers(0, 3))):
            words.append("".join(draw(st.permutations(list(b)))))
    words = draw(st.permutations(words))
    out, seen = [], set()
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def key(w):
    return tuple(sorted(w))


@prop("The result is a list of lists that together contain every input word exactly once.", words=word_lists())
def is_partition(f, words):
    r = f(words)
    assert isinstance(r, list) and all(isinstance(g, list) for g in r)
    assert sorted(w for g in r for w in g) == sorted(words)
    assert all(len(g) > 0 for g in r)


@prop("All words in the same group are anagrams of each other.", words=word_lists())
def groups_are_anagrams(f, words):
    assert all(len({key(w) for w in g}) == 1 for g in f(words))


@prop("Anagrams are never split across different groups.", words=word_lists())
def anagrams_not_split(f, words):
    keys = [key(g[0]) for g in f(words) if g]
    assert len(keys) == len(set(keys))


@prop("Groups follow first appearance in the input and words inside a group keep input order.", words=word_lists())
def order_preserved(f, words):
    r = f(words)
    pos = {w: i for i, w in enumerate(words)}
    assert all([pos[w] for w in g] == sorted(pos[w] for w in g) for g in r)
    firsts = [min(pos[w] for w in g) for g in r if g]
    assert firsts == sorted(firsts)


@prop("Case matters, words without anagrams stand alone, and an empty list gives [].",
      w=st.text(alphabet="abc", min_size=2, max_size=5))
def edge_cases(f, w):
    assert f([]) == []
    upper = w[0].upper() + w[1:][::-1]
    assert f([w, upper]) == [[w], [upper]]
    assert f([w]) == [[w]]

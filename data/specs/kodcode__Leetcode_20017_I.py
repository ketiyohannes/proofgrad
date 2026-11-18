"""Spec for can_construct_target: whether target is a concatenation of words (each reusable any number of times).

Domain: words is a non-empty list of non-empty lowercase strings; target is a lowercase string,
including the empty string (unit tests: empty target -> True).
"""
from functools import lru_cache

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_construct_target"

CLARIFICATIONS = [
    "Return a bool (True or False).",
    "An empty target can always be constructed (concatenating zero words), so return True.",
]

word_lists = st.lists(st.text(alphabet="ab", min_size=1, max_size=4), min_size=1, max_size=5)


def constructible(words, target):
    @lru_cache(maxsize=None)
    def go(k):
        if k == len(target):
            return True
        return any(target.startswith(w, k) and go(k + len(w)) for w in words)
    return go(0)


@st.composite
def built_case(draw):
    words = draw(word_lists)
    picks = draw(st.lists(st.sampled_from(words), min_size=1, max_size=8))
    return words, "".join(picks)


@st.composite
def random_case(draw):
    words = draw(word_lists)
    target = draw(st.text(alphabet="ab", min_size=1, max_size=14))
    return words, target


@prop("The result is a bool that matches whether target splits into words.", case=st.one_of(built_case(), random_case()))
def matches_definition(f, case):
    words, target = case
    r = f(words, target)
    assert isinstance(r, bool)
    assert r == constructible(words, target)


@prop("A target built by concatenating words from the list is constructible.", case=built_case())
def concatenations_are_constructible(f, case):
    words, target = case
    assert f(words, target) is True


@prop("A target containing a letter that no word contains is not constructible.",
      case=random_case(), pos=st.integers(0, 20))
def foreign_letter_rejected(f, case, pos):
    words, target = case
    k = pos % (len(target) + 1)
    assert f(words, target[:k] + "c" + target[k:]) is False


@prop("A target that can only be split up to a leftover suffix is not constructible.",
      case=built_case(), extra=st.text(alphabet="ab", min_size=1, max_size=3))
def leftover_rejected(f, case, extra):
    words, target = case
    t = target + extra
    assert f(words, t) is constructible(words, t)


@prop("The empty target is constructible; a single word is constructible from itself.", case=built_case())
def degenerate_cases(f, case):
    words, _ = case
    assert f(words, "") is True
    assert f([words[0]], words[0] * 3) is True

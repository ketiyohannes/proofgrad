"""Spec for canConstruct: True iff s is a concatenation of words from the list (words may be reused).

Domain: s is a lowercase string (possibly empty); the word list holds non-empty lowercase words (possibly no words).
"""
from functools import lru_cache

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "canConstruct"

CLARIFICATIONS = [
    "The empty string can always be constructed (return True).",
    "Return a bool.",
]

word = st.text(alphabet="ab", min_size=1, max_size=4)
words_list = st.lists(st.one_of(word, st.text(alphabet="abc", min_size=1, max_size=3)), max_size=6)
target = st.one_of(st.text(alphabet="ab", max_size=14), st.text(alphabet="abc", max_size=10))


def brute(s, words):
    words = set(words)

    @lru_cache(maxsize=None)
    def ok(i):
        if i == len(s):
            return True
        return any(s.startswith(w, i) and ok(i + len(w)) for w in words)

    return ok(0)


@prop("The result agrees with trying every way to split s into words from the list.", s=target, words=words_list)
def matches_brute_force(f, s, words):
    assert f(s, words) == brute(s, words)


@prop("A concatenation of list words (with reuse, in any order) is reported True.",
      words=st.lists(st.text(alphabet="abcxyz", min_size=1, max_size=5), min_size=1, max_size=5), data=st.data())
def concatenation_true(f, words, data):
    picks = data.draw(st.lists(st.sampled_from(words), min_size=1, max_size=6))
    assert f("".join(picks), words) is True


@prop("If s contains a character that appears in no word, the result is False.",
      s=st.text(alphabet="ab", max_size=8), words=st.lists(word, max_size=5), pos=st.integers(0, 8))
def foreign_char_false(f, s, words, pos):
    s = s[:pos] + "z" + s[pos:]
    assert f(s, words) is False


@prop("Using only a prefix of a valid concatenation that leaves leftover characters fails when the leftover cannot be formed.",
      w=st.text(alphabet="ab", min_size=2, max_size=5), k=st.integers(1, 4))
def partial_word_false(f, w, k):
    # Only w itself is available, so w repeated k times plus a proper prefix of w cannot be split.
    s = w * k + w[:-1]
    assert f(s, [w]) is False
    assert f(w * k, [w]) is True


@prop("The empty string gives True for any word list; the result type is bool.", words=words_list, s=target)
def empty_string_true(f, words, s):
    assert f("", words) is True
    assert isinstance(f(s, words), bool)

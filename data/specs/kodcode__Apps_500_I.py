"""Spec for reverse_words: the space-separated words in reverse order, joined by single spaces.

Domain: strings of letters, digits, punctuation and spaces (no other whitespace), including
empty strings, all-space strings, and leading, trailing and repeated spaces.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "reverse_words"

CLARIFICATIONS = ["Return an empty string if the input contains no words."]

word = st.text(alphabet="abcXYZ09!.,'", min_size=1, max_size=6)
gap = st.text(alphabet=" ", min_size=1, max_size=3)


@st.composite
def sentences(draw):
    words = draw(st.lists(word, max_size=8))
    lead = draw(st.text(alphabet=" ", max_size=3))
    trail = draw(st.text(alphabet=" ", max_size=3))
    body = ""
    for i, w in enumerate(words):
        body += (draw(gap) if i else "") + w
    return lead + body + trail, words


@prop("The result is the input's words in reverse order joined by single spaces.", case=sentences())
def reversed_words(f, case):
    s, words = case
    assert f(s) == " ".join(reversed(words))


@prop("The result has no leading or trailing spaces and no repeated spaces.", case=sentences())
def clean_spacing(f, case):
    s, _ = case
    out = f(s)
    assert isinstance(out, str)
    assert out == out.strip(" ")
    assert "  " not in out


@prop("The result contains exactly the same words as the input.", case=sentences())
def same_words(f, case):
    s, words = case
    assert sorted(f(s).split(" ")) == sorted(words) if words else f(s) == ""


@prop("A single word (with optional surrounding spaces) is returned as that word.",
      w=word, lead=st.text(alphabet=" ", max_size=3), trail=st.text(alphabet=" ", max_size=3))
def single_word(f, w, lead, trail):
    assert f(lead + w + trail) == w


@prop("An empty or all-space string gives the empty string.", s=st.text(alphabet=" ", max_size=5))
def no_words(f, s):
    assert f(s) == ""

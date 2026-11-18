"""Spec for removeDuplicates: keep the first occurrence of each word, joined by single spaces.

Domain: s consists of lowercase letters and spaces; it may be empty and may contain leading,
trailing, or repeated spaces. Words are maximal runs of letters.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "removeDuplicates"

CLARIFICATIONS = [
    "The input may contain leading, trailing, or repeated spaces; the result always uses single spaces between words.",
    "Return the resulting sentence as a string (\"\" if there are no words).",
]

word = st.one_of(st.sampled_from(["the", "cat", "a", "is", "hat", "at", "th"]),
                 st.text(alphabet="ab", min_size=1, max_size=3))


@st.composite
def sentences(draw):
    words = draw(st.lists(word, max_size=10))
    messy = draw(st.booleans())
    if not messy:
        return " ".join(words)
    gaps = [" " * draw(st.integers(1, 3)) for _ in words]
    lead = " " * draw(st.integers(0, 2))
    trail = " " * draw(st.integers(0, 2))
    return lead + "".join(w + g for w, g in zip(words, gaps)).rstrip(" ") + trail


def first_occurrences(s):
    out = []
    for w in s.split(" "):
        if w and w not in out:
            out.append(w)
    return out


@prop("The words of the result are the distinct words of the input in order of first occurrence.", s=sentences())
def first_occurrence_order(f, s):
    assert f(s) == " ".join(first_occurrences(s))


@prop("The result has no leading or trailing spaces and exactly one space between words.", s=sentences())
def normalized_spacing(f, s):
    r = f(s)
    assert isinstance(r, str)
    assert r == r.strip(" ")
    assert "  " not in r


@prop("The result contains no repeated word.", s=sentences())
def no_duplicates(f, s):
    ws = f(s).split()
    assert len(ws) == len(set(ws))


@prop("A sentence of distinct single-spaced words is returned unchanged.",
      ws=st.lists(st.text(alphabet="abcdefg", min_size=1, max_size=5), unique=True, max_size=10))
def distinct_unchanged(f, ws):
    s = " ".join(ws)
    assert f(s) == s


@prop("The empty string gives the empty string; a word repeated n times gives that word.",
      w=st.text(alphabet="xyz", min_size=1, max_size=5), n=st.integers(min_value=1, max_value=6))
def degenerate_inputs(f, w, n):
    assert f("") == ""
    assert f(" ".join([w] * n)) == w

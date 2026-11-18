"""Spec for run_length_encoding: each maximal run of a character becomes the character followed by the run length.

Domain: strings of letters (case-sensitive), spaces and punctuation, no digits (so the
encoding can be decoded unambiguously), including the empty string and long runs.
"""
import re

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "run_length_encoding"

CLARIFICATIONS = [
    "Return an empty string for an empty input.",
    "Characters are case-sensitive: 'a' and 'A' are different characters.",
]


def runs(s):
    out = []
    for ch in s:
        if out and out[-1][0] == ch:
            out[-1][1] += 1
        else:
            out.append([ch, 1])
    return out


@st.composite
def run_strings(draw):
    pieces = draw(st.lists(st.tuples(st.sampled_from("abAB !."), st.integers(1, 12)), max_size=10))
    return "".join(c * n for c, n in pieces)


texts = st.one_of(run_strings(), st.text(alphabet="abcaA", max_size=25))


def decode(enc):
    tokens = re.findall(r"(\D)(\d+)", enc)
    assert "".join(c + n for c, n in tokens) == enc, "malformed encoding"
    return tokens


@prop("The encoding is the sequence of (character, run length) pairs of the input's maximal runs.", s=texts)
def exact_encoding(f, s):
    assert f(s) == "".join(f"{c}{n}" for c, n in runs(s))


@prop("Decoding the result gives back the input.", s=texts)
def round_trip(f, s):
    out = f(s)
    assert isinstance(out, str)
    assert "".join(c * int(n) for c, n in decode(out)) == s


@prop("Adjacent encoded characters are different (runs are maximal).", s=texts)
def runs_maximal(f, s):
    chars = [c for c, _ in decode(f(s))]
    assert all(chars[i] != chars[i + 1] for i in range(len(chars) - 1))


@prop("A single run of length n (including n >= 10) encodes as the character followed by n.",
      c=st.sampled_from("aZ !"), n=st.integers(1, 30))
def single_run(f, c, n):
    assert f(c * n) == f"{c}{n}"


@prop("Characters that do not repeat get the count 1.",
      s=st.lists(st.sampled_from("abcdefABCDEF"), max_size=12).filter(lambda xs: all(xs[i] != xs[i + 1] for i in range(len(xs) - 1))).map("".join))
def singletons_get_one(f, s):
    assert f(s) == "".join(c + "1" for c in s)


@prop("The empty string encodes to the empty string.", dummy=st.just(None))
def empty_input(f, dummy):
    assert f("") == ""

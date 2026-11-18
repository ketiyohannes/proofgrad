"""Spec for has_three_consecutive_identical_chars: whether some character occurs three times in a row.

Domain: arbitrary strings (characters compared exactly), including the empty string.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "has_three_consecutive_identical_chars"

CLARIFICATIONS = [
    "Any characters count (letters, digits, punctuation, spaces), compared exactly; return a bool.",
]

strs = st.one_of(
    st.text(alphabet="ab", max_size=12),
    st.text(alphabet="abc1! ", max_size=20),
    st.text(max_size=15),
)


def has_triple(s):
    return any(s[i] == s[i + 1] == s[i + 2] for i in range(len(s) - 2))


@prop("The result is True exactly when some character appears three times consecutively.", s=strs)
def matches_definition(f, s):
    r = f(s)
    assert isinstance(r, bool)
    assert r == has_triple(s)


@prop("Inserting a run of three equal characters anywhere makes the result True.",
      s=strs, c=st.sampled_from("ab!7 "), data=st.data())
def inserted_triple(f, s, c, data):
    i = data.draw(st.integers(min_value=0, max_value=len(s)))
    assert f(s[:i] + c * 3 + s[i:]) is True


@prop("Strings made of runs of length at most two are False.",
      runs=st.lists(st.tuples(st.sampled_from("abc"), st.integers(min_value=1, max_value=2)), max_size=10))
def short_runs_false(f, runs):
    s, prev = "", None
    for c, n in runs:
        if c == prev:
            continue
        s += c * n
        prev = c
    assert f(s) is False


@prop("Three equal characters that are not adjacent do not count.", c=st.sampled_from("ab1"), sep=st.sampled_from("xyz"))
def non_adjacent(f, c, sep):
    assert f(c + c + sep + c) is False
    assert f(c + sep + c + sep + c) is False


@prop("Strings shorter than three characters are False; a string of exactly three equal characters is True.",
      s=st.text(alphabet="ab", max_size=2), c=st.sampled_from("a!9 "))
def boundaries(f, s, c):
    assert f(s) is False
    assert f(c * 3) is True

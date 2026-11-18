"""Spec for mirror_image: strip leading/trailing whitespace, then reverse the characters.

Domain: strings of letters (both cases), digits, symbols and spaces, including empty and all-space strings.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "mirror_image"

CLARIFICATIONS = [
    "Inner whitespace is kept as-is; an empty or all-whitespace string gives \"\".",
]

core = st.text(alphabet="abcXYZ019!@# ", max_size=20)
padded = st.builds(lambda l, c, r: " " * l + c + " " * r, st.integers(0, 4), core, st.integers(0, 4))


@prop("The result equals the stripped input reversed.", s=padded)
def matches_definition(f, s):
    r = f(s)
    assert isinstance(r, str)
    assert r == s.strip()[::-1]


@prop("The result has no leading or trailing spaces.", s=padded)
def no_outer_whitespace(f, s):
    r = f(s)
    assert r == r.strip()


@prop("A string with no outer whitespace is simply reversed (case and symbols preserved).",
      s=st.text(alphabet="abcXYZ019!@#", min_size=1, max_size=20))
def plain_reverse(f, s):
    assert f(s) == s[::-1]


@prop("Mirroring twice returns the stripped input.", s=padded)
def involution(f, s):
    assert f(f(s)) == s.strip()


@prop("Leading and trailing spaces do not affect the result.", s=core, left=st.integers(0, 5), right=st.integers(0, 5))
def padding_ignored(f, s, left, right):
    assert f(" " * left + s + " " * right) == f(s.strip()) == s.strip()[::-1]


@prop("Empty and all-space strings give the empty string.", n=st.integers(0, 6))
def blank_input(f, n):
    assert f(" " * n) == ""

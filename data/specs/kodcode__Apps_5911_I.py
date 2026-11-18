"""Spec for isomorphic_strings: True iff a one-to-one character mapping turns s into t.

Domain: short lowercase strings (small alphabets to force repeated characters). Strings of
different lengths are allowed and give False, as the unit tests require.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "isomorphic_strings"

CLARIFICATIONS = [
    "Return the Python booleans True or False.",
    "If s and t have different lengths, return False.",
]

small_text = st.text(alphabet="abcd", max_size=12)


def pattern(s):
    """Replace each character by the index of its first occurrence; isomorphic strings share a pattern."""
    return [s.index(c) for c in s]


@st.composite
def injective_image(draw):
    """(s, t) where t is s with every character replaced through a one-to-one mapping."""
    s = draw(st.text(alphabet="abcdefgh", max_size=20))
    chars = sorted(set(s))
    images = draw(st.lists(st.sampled_from("abcdefghijklmnop"), min_size=len(chars), max_size=len(chars), unique=True))
    mapping = dict(zip(chars, images))
    return s, "".join(mapping[c] for c in s)


@st.composite
def merged_image(draw):
    """(s, t) where two distinct characters of s are sent to the same character, so t is not isomorphic to s."""
    s = draw(st.text(alphabet="abcdefgh", max_size=20).filter(lambda x: len(set(x)) >= 2))
    chars = sorted(set(s))
    images = draw(st.lists(st.sampled_from("abcdefghijklmnop"), min_size=len(chars), max_size=len(chars), unique=True))
    mapping = dict(zip(chars, images))
    x, y = draw(st.lists(st.sampled_from(chars), min_size=2, max_size=2, unique=True))
    mapping[y] = mapping[x]
    return s, "".join(mapping[c] for c in s)


@st.composite
def same_length_pair(draw):
    n = draw(st.integers(0, 10))
    alphabet = draw(st.sampled_from(["ab", "abc", "abcdef"]))
    s = draw(st.text(alphabet=alphabet, min_size=n, max_size=n))
    t = draw(st.one_of(st.text(alphabet=alphabet, min_size=n, max_size=n), st.just(s), st.just(s[::-1])))
    return s, t


@st.composite
def one_change(draw):
    """(s, t) with t an injective image of s except at one position, which gets a different character."""
    s, t = draw(injective_image().filter(lambda p: len(p[0]) >= 1))
    i = draw(st.integers(0, len(t) - 1))
    c = draw(st.sampled_from("abcdefghijklmnop").filter(lambda c: c != t[i]))
    return s, t[:i] + c + t[i + 1:]


@prop(
    "Strings of different lengths are not isomorphic.",
    inst=st.tuples(small_text, small_text).filter(lambda p: len(p[0]) != len(p[1])),
)
def different_lengths_false(f, inst):
    s, t = inst
    assert f(s, t) is False


@prop("Applying a one-to-one character mapping to s gives a string isomorphic to s.", inst=injective_image())
def injective_mapping_true(f, inst):
    s, t = inst
    assert f(s, t) is True


@prop("If two different characters of s would have to map to the same character, the result is False.", inst=merged_image())
def merged_characters_false(f, inst):
    s, t = inst
    assert f(s, t) is False


@prop(
    "The result is True exactly when s and t have the same first-occurrence pattern.",
    inst=st.one_of(same_length_pair(), one_change()),
)
def matches_pattern_oracle(f, inst):
    s, t = inst
    assert f(s, t) is (pattern(s) == pattern(t))


@prop(
    "Isomorphism is symmetric: swapping s and t does not change the result.",
    inst=st.one_of(same_length_pair(), injective_image(), merged_image(), st.tuples(small_text, small_text)),
)
def symmetric(f, inst):
    s, t = inst
    assert f(s, t) == f(t, s)

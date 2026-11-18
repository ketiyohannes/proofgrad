"""Spec for find_extra_character: return the one character B has beyond the multiset of A.

Domain: lowercase strings, len(A) <= 40 (including empty A), B a shuffle of A plus one lowercase character.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_extra_character"

CLARIFICATIONS = ["Return the extra character as a one-character string."]

LOWER = "abcdefghijklmnopqrstuvwxyz"


@st.composite
def instances(draw, alphabet=LOWER):
    """Return (A, B, extra) where B is a shuffle of A plus the character `extra`."""
    # Bias toward degenerate A: empty, a single repeated letter, or very few distinct letters.
    a = draw(
        st.one_of(
            st.text(alphabet=alphabet, max_size=40),
            st.just(""),
            st.builds(lambda c, n: c * n, st.sampled_from(alphabet), st.integers(1, 40)),
            st.text(alphabet=alphabet[:2], max_size=40),
        )
    )
    extra = draw(st.sampled_from(alphabet))
    b_chars = draw(st.permutations(list(a) + [extra]))
    return a, "".join(b_chars), extra


@st.composite
def duplicate_extra_instances(draw):
    """The extra character also occurs in A, so it is only distinguishable by count."""
    a = draw(st.text(alphabet=LOWER, min_size=1, max_size=40))
    extra = draw(st.sampled_from(sorted(set(a))))
    b_chars = draw(st.permutations(list(a) + [extra]))
    return a, "".join(b_chars), extra


@prop("The result is a single character.", inst=instances())
def single_character(f, inst):
    a, b, _ = inst
    result = f(a, b)
    assert isinstance(result, str) and len(result) == 1


@prop("The result is exactly the extra character of B.", inst=instances())
def finds_extra(f, inst):
    a, b, extra = inst
    assert f(a, b) == extra


@prop("Removing one occurrence of the result from B leaves a permutation of A.", inst=instances(alphabet="abc"))
def removal_restores_a(f, inst):
    a, b, _ = inst
    result = f(a, b)
    remaining = Counter(b)
    remaining[result] -= 1
    assert remaining[result] >= 0
    assert +remaining == Counter(a)


@prop("When the extra character already occurs in A, it is still found (by count).", inst=duplicate_extra_instances())
def duplicate_extra(f, inst):
    a, b, extra = inst
    assert f(a, b) == extra


@prop(
    "Reordering the characters of A or B does not change the result.",
    inst=instances(alphabet="abcd"),
    data=st.data(),
)
def order_invariant(f, inst, data):
    a, b, _ = inst
    a2 = "".join(data.draw(st.permutations(list(a))))
    b2 = "".join(data.draw(st.permutations(list(b))))
    assert f(a, b) == f(a2, b2)

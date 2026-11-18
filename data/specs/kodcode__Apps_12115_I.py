"""Spec for calculate_depth: the maximum nesting depth of dictionaries, where the outer dictionary has depth 1.

Domain: dictionaries with string keys whose values are ints, strings or (recursively) dictionaries;
empty dictionaries allowed at any level. Only the first argument is passed.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "calculate_depth"

CLARIFICATIONS = [
    "The outermost dictionary has depth 1, even when it is empty; an empty nested dictionary still counts as one level (e.g. {'a': {}} has depth 2).",
    "Only dictionary values add depth; other values (ints, strings) do not. Return an int.",
]

keys = st.text(alphabet="abcdef", min_size=1, max_size=2)
leaf = st.one_of(st.integers(-100, 100), st.text(alphabet="xyz", max_size=3))
nested = st.recursive(
    st.dictionaries(keys, leaf, max_size=3),
    lambda inner: st.dictionaries(keys, st.one_of(leaf, inner), max_size=4),
    max_leaves=25,
)
flat = st.dictionaries(keys, leaf, max_size=6)


def depth(d):
    return 1 + max((depth(v) for v in d.values() if isinstance(v, dict)), default=0)


def chain(k):
    d = {}
    for _ in range(k - 1):
        d = {"k": d}
    return d


@prop("The result is an int equal to the maximum nesting depth of dictionaries.", d=nested)
def matches_definition(f, d):
    r = f(d)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == depth(d)


@prop("A dictionary with no dictionary values (including the empty one) has depth 1.", d=flat)
def flat_is_one(f, d):
    assert f(d) == 1


@prop("A chain of k nested dictionaries ending in an empty dictionary has depth k.",
      k=st.integers(min_value=1, max_value=30), leafy=st.booleans())
def chain_depth(f, k, leafy):
    d = chain(k)
    if leafy:
        d["x"] = 5
    assert f(d) == k


@prop("Wrapping a dictionary as a value of a new dictionary increases the depth by exactly one.", d=nested, other=flat)
def wrapping_adds_one(f, d, other):
    wrapped = dict(other)
    wrapped["zz"] = d
    assert f(wrapped) == f(d) + 1


@prop("Adding a sibling dictionary value yields the maximum of the existing depth and the sibling's depth plus one.",
      a=nested, b=nested)
def sibling_max(f, a, b):
    combined = dict(a)
    combined["zz"] = b
    assert f(combined) == max(f(a), f(b) + 1)

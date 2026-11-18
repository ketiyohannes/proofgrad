"""Spec for strongest_potions: identifiers of k potions with the largest total strength, in any order.

Domain: 1..30 potions with unique alphanumeric identifiers and strengths in -1000..1000
(often with ties), and 1 <= k <= len(potions). Ties may be broken arbitrarily.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "strongest_potions"

CLARIFICATIONS = ["Return a list of identifier strings; if several selections are equally strong, any of them is accepted."]


@st.composite
def instances(draw):
    ids = draw(st.lists(st.text(alphabet="abcXYZ0129 '", min_size=1, max_size=6), min_size=1, max_size=30, unique=True))
    strength = draw(st.sampled_from([st.integers(-1000, 1000), st.integers(-2, 2), st.just(7), st.integers(-1000, -1)]))
    potions = [(draw(strength), name) for name in ids]
    k = draw(st.one_of(st.integers(1, len(potions)), st.sampled_from([1, len(potions)])))
    return potions, k


@prop("The result is a list of exactly k distinct identifiers taken from the input.", inst=instances())
def k_distinct_ids(f, inst):
    potions, k = inst
    result = f(potions, k)
    assert isinstance(result, list)
    assert len(result) == k
    assert len(set(result)) == k
    assert set(result) <= {name for _, name in potions}


@prop("The total strength of the selection is the largest possible for k potions.", inst=instances())
def maximal_total(f, inst):
    potions, k = inst
    strength = {name: s for s, name in potions}
    result = f(potions, k)
    best = sum(sorted((s for s, _ in potions), reverse=True)[:k])
    assert sum(strength[name] for name in result) == best


@prop("Every selected potion is at least as strong as every unselected one.", inst=instances())
def dominates_unselected(f, inst):
    potions, k = inst
    chosen = set(f(potions, k))
    picked = [s for s, n in potions if n in chosen]
    left = [s for s, n in potions if n not in chosen]
    if picked and left:
        assert min(picked) >= max(left)


@prop("With k equal to the number of potions, all identifiers are returned.", inst=instances())
def all_when_k_is_n(f, inst):
    potions, _ = inst
    assert sorted(f(potions, len(potions))) == sorted(name for _, name in potions)

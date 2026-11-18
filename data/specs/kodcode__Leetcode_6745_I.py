"""Spec for group_and_sort_items: [[type, sorted names]] per type, types in order of first appearance.

Domain: items is a list (possibly empty) of [type, name] pairs of lowercase strings; the same name
may appear more than once within a type. Names are sorted with Python's default string order.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "group_and_sort_items"

CLARIFICATIONS = [
    "Return a list of [type, names] pairs (each a two-element list), where names is a list.",
    "Types appear in the order of their first occurrence in the input. Duplicate names are kept.",
]

TYPES = ["fruit", "veg", "bird", "a", "b"]
names = st.one_of(st.sampled_from(["apple", "banana", "cherry", "date", "b", "a", "ab"]),
                  st.text(alphabet="abcz", min_size=1, max_size=4))
items_strategy = st.lists(st.tuples(st.sampled_from(TYPES), names).map(list), max_size=15)


@prop("Each group's names are exactly that type's names from the input, sorted ascending.", items=items_strategy)
def groups_sorted_and_complete(f, items):
    r = f(items)
    for t, ns in r:
        assert list(ns) == sorted(n for it, n in items if it == t)


@prop("The types appear once each, in order of their first occurrence in the input.", items=items_strategy)
def type_order(f, items):
    expected = []
    for t, _ in items:
        if t not in expected:
            expected.append(t)
    assert [g[0] for g in f(items)] == expected


@prop("The result is a list of two-element lists [type, list of names].", items=items_strategy)
def result_shape(f, items):
    r = f(items)
    assert isinstance(r, list)
    for g in r:
        assert isinstance(g, list) and len(g) == 2 and isinstance(g[1], list)


@prop("The output contains every input item exactly once (no items lost, duplicated, or invented).", items=items_strategy)
def preserves_items(f, items):
    out = sorted((t, n) for t, ns in f(items) for n in ns)
    assert out == sorted((t, n) for t, n in items)


@prop("An empty input gives an empty list.", dummy=st.just(None))
def empty_input(f, dummy):
    assert f([]) == []

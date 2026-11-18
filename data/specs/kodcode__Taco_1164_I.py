"""Spec for generate_tournament_schedule: every unordered pair of skill levels exactly once, as (smaller, larger) tuples in lexicographic order.

Domain: n == len(skill_levels) >= 2, skill levels are distinct integers (negative values allowed).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "generate_tournament_schedule"

CLARIFICATIONS = [
    "Return the schedule as a list of matches; each match is a tuple (a, b) of two skill levels with a < b.",
    "The list must be sorted in lexicographic order of the (a, b) tuples.",
]


@st.composite
def participants(draw):
    shape = draw(st.sampled_from(["random", "sorted", "reversed", "small", "two"]))
    if shape == "two":
        levels = draw(st.lists(st.integers(-10**6, 10**6), min_size=2, max_size=2, unique=True))
    elif shape == "small":
        levels = draw(st.lists(st.integers(-5, 5), min_size=2, max_size=11, unique=True))
    else:
        levels = draw(st.lists(st.integers(-10**6, 10**6), min_size=2, max_size=14, unique=True))
        if shape == "sorted":
            levels.sort()
        elif shape == "reversed":
            levels.sort(reverse=True)
    return len(levels), levels


def expected_pairs(levels):
    return sorted((min(a, b), max(a, b)) for i, a in enumerate(levels) for b in levels[i + 1:])


@prop("The result is a list of 2-tuples of skill levels.", case=participants())
def returns_list_of_tuples(f, case):
    n, levels = case
    result = f(n, levels)
    assert isinstance(result, list)
    assert all(isinstance(m, tuple) and len(m) == 2 for m in result)


@prop("The schedule has exactly n*(n-1)/2 matches.", case=participants())
def has_correct_count(f, case):
    n, levels = case
    assert len(f(n, levels)) == n * (n - 1) // 2


@prop("Every match is between two different participants, with the smaller skill level first.", case=participants())
def each_match_valid(f, case):
    n, levels = case
    present = set(levels)
    for a, b in f(n, levels):
        assert a in present and b in present
        assert a < b


@prop("Every pair of participants meets exactly once.", case=participants())
def every_pair_once(f, case):
    n, levels = case
    result = [tuple(m) for m in f(n, levels)]
    assert sorted(result) == expected_pairs(levels)
    assert len(set(result)) == len(result)


@prop("The matches are listed in lexicographic order.", case=participants())
def lexicographic_order(f, case):
    n, levels = case
    result = [tuple(m) for m in f(n, levels)]
    assert result == sorted(result)


@prop("The result equals the full sorted list of (smaller, larger) pairs.", case=participants())
def exact_schedule(f, case):
    n, levels = case
    assert f(n, levels) == expected_pairs(levels)

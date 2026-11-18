"""Spec for days_to_reach_max_height: for each (H, G, L), the first day n >= 0 with H + n*G >= L, or "Infinity".

Domain: T == len(test_cases); 1 <= H, L <= 10**9 and 0 <= G <= 10**9 (G = 0 appears in
the sample and the unit tests even though the constraints say G > 0).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "days_to_reach_max_height"

CLARIFICATIONS = [
    "Return a list with one answer per test case, in order: an int day, or the string 'Infinity'.",
    "G may be 0; if H >= L the answer is 0 regardless of G.",
]

big = st.integers(min_value=1, max_value=10**9)
small = st.integers(min_value=1, max_value=30)
case_big = st.tuples(big, st.one_of(big, st.integers(0, 10), st.just(0)), big)
case_small = st.tuples(small, st.integers(min_value=0, max_value=8), small)
cases = st.lists(st.one_of(case_small, case_big), min_size=1, max_size=15)


def brute_day(h, g, l):
    if h >= l:
        return 0
    if g == 0:
        return "Infinity"
    n = 0
    while h + n * g < l:
        n += 1
    return n


@prop("The result is a list with one answer per test case.", test_cases=cases)
def one_answer_per_case(f, test_cases):
    result = f(len(test_cases), test_cases)
    assert isinstance(result, list)
    assert len(result) == len(test_cases)


@prop("On small inputs each answer equals the first day the height reaches the limit.",
      test_cases=st.lists(case_small, min_size=1, max_size=15))
def matches_brute_force(f, test_cases):
    assert f(len(test_cases), test_cases) == [brute_day(*c) for c in test_cases]


@prop("For growing plants below the limit, the answer d is the first day with H + d*G >= L.",
      test_cases=st.lists(st.tuples(big, st.one_of(big, st.integers(1, 1000)), big), min_size=1, max_size=15))
def minimal_day_large(f, test_cases):
    for (h, g, l), d in zip(test_cases, f(len(test_cases), test_cases)):
        if h >= l:
            continue
        assert isinstance(d, int) and d >= 1
        assert h + d * g >= l
        assert h + (d - 1) * g < l


@prop("If the initial height is at least the limit, the answer is 0.",
      test_cases=st.lists(st.tuples(big, st.integers(0, 10**9), big).map(lambda t: (max(t[0], t[2]), t[1], min(t[0], t[2]))),
                          min_size=1, max_size=10))
def already_tall(f, test_cases):
    assert f(len(test_cases), test_cases) == [0] * len(test_cases)


@prop("Zero growth below the limit gives the string 'Infinity'.",
      test_cases=st.lists(st.tuples(big, st.just(0), big).filter(lambda t: t[0] < t[2]), min_size=1, max_size=10))
def zero_growth_infinity(f, test_cases):
    assert f(len(test_cases), test_cases) == ["Infinity"] * len(test_cases)

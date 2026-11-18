"""Spec for can_buy_tea_for_all: POSSIBLE iff M * Y <= B, per test case.

Domain: T == len(test_cases) >= 1; each test case is a tuple (M, Y, B) with 1 <= M, Y <= 100 and
1 <= B <= 10000. The statement allows any letter case, so answers are compared case-insensitively.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_buy_tea_for_all"

CLARIFICATIONS = [
    "test_cases is a list of (M, Y, B) tuples; return a list of strings (\"POSSIBLE\" or \"IMPOSSIBLE\"), one per test case, in input order.",
]


@st.composite
def case(draw):
    m = draw(st.integers(1, 100))
    y = draw(st.integers(1, 100))
    kind = draw(st.sampled_from(["random", "exact", "one_short", "one_over"]))
    if kind == "exact":
        b = m * y
    elif kind == "one_short":
        b = max(1, m * y - 1)
    elif kind == "one_over":
        b = min(10000, m * y + 1)
    else:
        b = draw(st.integers(1, 10000))
    return m, y, b


cases = st.lists(case(), min_size=1, max_size=10)


def norm(result):
    return [r.upper() for r in result]


@prop("The result is a list with one string per test case.", cases=cases)
def one_answer_per_case(f, cases):
    result = f(len(cases), cases)
    assert isinstance(result, list)
    assert len(result) == len(cases)
    assert all(isinstance(r, str) for r in result)


@prop("Each answer is POSSIBLE exactly when M * Y <= B, otherwise IMPOSSIBLE (case-insensitive).", cases=cases)
def matches_definition(f, cases):
    assert norm(f(len(cases), cases)) == ["POSSIBLE" if m * y <= b else "IMPOSSIBLE" for m, y, b in cases]


@prop("A budget of exactly M * Y is enough.", m=st.integers(1, 100), y=st.integers(1, 100))
def exact_budget(f, m, y):
    assert norm(f(1, [(m, y, m * y)])) == ["POSSIBLE"]


@prop("A budget one dollar short of M * Y is not enough.", m=st.integers(1, 100), y=st.integers(1, 100))
def one_short(f, m, y):
    if m * y >= 2:
        assert norm(f(1, [(m, y, m * y - 1)])) == ["IMPOSSIBLE"]

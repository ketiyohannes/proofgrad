"""Spec for max_score: per test case, the best single-tile score where special tiles count double.

Domain: T == len(test_cases) >= 1; each test case is a tuple (N, values, specials) with
N == len(values) == len(specials) >= 1, 1 <= values[i] <= 10^9, specials[i] in {0, 1}.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_score"

CLARIFICATIONS = [
    "test_cases is a list of tuples (N, values, specials); return a list of ints, one answer per test case, in input order.",
]


@st.composite
def board(draw):
    n = draw(st.integers(1, 15))
    value = draw(st.sampled_from([st.integers(1, 10**9), st.integers(1, 6)]))
    values = draw(st.lists(value, min_size=n, max_size=n))
    mode = draw(st.sampled_from(["random", "none", "all"]))
    if mode == "none":
        specials = [0] * n
    elif mode == "all":
        specials = [1] * n
    else:
        specials = draw(st.lists(st.sampled_from([0, 1]), min_size=n, max_size=n))
    return n, values, specials


cases = st.lists(board(), min_size=1, max_size=5)


def best(values, specials):
    return max(v * 2 if s == 1 else v for v, s in zip(values, specials))


@prop("The result is a list with one int per test case.", cases=cases)
def one_answer_per_case(f, cases):
    result = f(len(cases), cases)
    assert isinstance(result, list)
    assert len(result) == len(cases)
    assert all(isinstance(r, int) for r in result)


@prop("Each answer is the maximum over tiles of the value, doubled on special tiles.", cases=cases)
def matches_definition(f, cases):
    assert f(len(cases), cases) == [best(v, s) for _, v, s in cases]


@prop("With no special tiles the answer is the largest value.", b=board())
def no_specials(f, b):
    n, values, _ = b
    assert f(1, [(n, values, [0] * n)]) == [max(values)]


@prop("With all tiles special the answer is twice the largest value.", b=board())
def all_specials(f, b):
    n, values, _ = b
    assert f(1, [(n, values, [1] * n)]) == [2 * max(values)]


@prop("Marking an extra tile as special never lowers the answer.", b=board(), data=st.data())
def monotone_in_specials(f, b, data):
    n, values, specials = b
    i = data.draw(st.integers(0, n - 1))
    more = list(specials)
    more[i] = 1
    assert f(1, [(n, values, more)])[0] >= f(1, [(n, values, specials)])[0]

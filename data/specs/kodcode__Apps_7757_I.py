"""Spec for daily_temperatures: for each day, the distance to the next strictly warmer day, or 0 if none.

Domain: N == len(temperatures), 1 <= N, temperatures in 30..100.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "daily_temperatures"

CLARIFICATIONS = [
    "A warmer day means a strictly higher temperature; an equal temperature does not count.",
    "Return a list of N ints.",
]


@st.composite
def temps(draw, max_size=40):
    shape = draw(st.sampled_from(["random", "few", "sorted", "reverse", "equal"]))
    lo, hi = (70, 72) if shape == "few" else (30, 100)
    t = draw(st.lists(st.integers(lo, hi), min_size=1, max_size=max_size))
    if shape == "sorted":
        t.sort()
    elif shape == "reverse":
        t.sort(reverse=True)
    elif shape == "equal":
        t = [t[0]] * len(t)
    return t


def call(f, t):
    return f(len(t), t)


@prop("The result is a list of N ints.", t=temps())
def output_shape(f, t):
    r = call(f, t)
    assert isinstance(r, list) and len(r) == len(t)
    assert all(isinstance(x, int) for x in r)


@prop("Every positive answer points to a later day within range that is strictly warmer.", t=temps())
def points_to_warmer_day(f, t):
    r = call(f, t)
    for i, d in enumerate(r):
        assert d >= 0
        if d > 0:
            assert i + d < len(t) and t[i + d] > t[i]


@prop("No day strictly between a day and its answer is warmer (the answer is the nearest warmer day).", t=temps())
def nearest_warmer_day(f, t):
    r = call(f, t)
    for i, d in enumerate(r):
        if d > 0:
            assert all(t[j] <= t[i] for j in range(i + 1, i + d))


@prop("The answer is 0 exactly when no later day is strictly warmer.", t=temps())
def zero_iff_no_warmer(f, t):
    r = call(f, t)
    for i in range(len(t)):
        assert (r[i] == 0) == (not any(t[j] > t[i] for j in range(i + 1, len(t))))


@prop("A single day gives [0]; strictly increasing temperatures give all 1s except a final 0.",
      x=st.integers(30, 100), t=st.lists(st.integers(30, 100), min_size=1, max_size=30, unique=True).map(sorted))
def simple_cases(f, x, t):
    assert f(1, [x]) == [0]
    assert call(f, t) == [1] * (len(t) - 1) + [0]

"""Spec for highest_average_score: the largest per-session mean score, rounded to two decimals.

Domain: n == len(sessions) >= 1; each session is a non-empty list of integer scores 0..10^6.
Rounding is checked with a tolerance of half a cent (so any standard rounding of exact ties is
accepted) plus the requirement that the value has at most two decimals.
"""
from fractions import Fraction

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "highest_average_score"

CLARIFICATIONS = [
    "Return the answer as a float rounded to two decimal places (e.g. 450.0 or 12.5), not a formatted string.",
]

score = st.one_of(st.integers(0, 10**6), st.integers(0, 10), st.just(0))
session = st.lists(score, min_size=1, max_size=12)
sessions = st.one_of(
    st.lists(session, min_size=1, max_size=8),
    st.lists(st.lists(st.integers(0, 3), min_size=1, max_size=7), min_size=1, max_size=8),
)


def best_mean(ss):
    return max(Fraction(sum(s), len(s)) for s in ss)


def two_decimals(x):
    return abs(x * 100 - round(x * 100)) < 1e-6


@prop("The result is a float.", ss=sessions)
def is_float(f, ss):
    assert isinstance(f(len(ss), ss), float)


@prop("The result is within half a cent of the highest session average.", ss=sessions)
def close_to_best_mean(f, ss):
    r = f(len(ss), ss)
    assert abs(Fraction(r) - best_mean(ss)) <= Fraction(1, 200) + Fraction(1, 10**9)


@prop("The result has at most two decimal places.", ss=sessions)
def rounded_to_cents(f, ss):
    assert two_decimals(f(len(ss), ss))


@prop("Session averages that are whole cents are returned exactly.",
      ss=st.lists(st.sampled_from([1, 2, 4, 5]).flatmap(lambda k: st.lists(score, min_size=k, max_size=k)), min_size=1, max_size=6))
def exact_when_representable(f, ss):
    assert f(len(ss), ss) == float(best_mean(ss))


@prop("Reordering sessions, or the games inside a session, does not change the answer.", ss=sessions, data=st.data())
def order_invariant(f, ss, data):
    shuffled = [list(data.draw(st.permutations(s))) for s in data.draw(st.permutations(ss))]
    assert f(len(shuffled), shuffled) == f(len(ss), ss)


@prop("A single session with a single game returns that score.", x=st.integers(0, 10**6))
def single_game(f, x):
    assert f(1, [[x]]) == float(x)

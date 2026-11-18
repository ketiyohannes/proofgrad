"""Spec for exam_result: map an integer score to "Excellent", "Good", "Pass" or "Fail".

Domain: integer scores; mostly 0..100, with some values outside that range, which the
statement's open-ended bands ("90 or above", "below 50") still cover.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "exam_result"

boundaries = st.sampled_from([48, 49, 50, 51, 68, 69, 70, 71, 88, 89, 90, 91, 0, 100])
scores = st.one_of(st.integers(min_value=0, max_value=100), boundaries, st.integers(min_value=-50, max_value=200))


@prop("Scores of 90 or above give \"Excellent\".", score=st.one_of(st.integers(90, 100), st.just(90), st.integers(90, 1000)))
def excellent_band(f, score):
    assert f(score) == "Excellent"


@prop("Scores from 70 to 89 inclusive give \"Good\".", score=st.one_of(st.integers(70, 89), st.sampled_from([70, 89])))
def good_band(f, score):
    assert f(score) == "Good"


@prop("Scores from 50 to 69 inclusive give \"Pass\".", score=st.one_of(st.integers(50, 69), st.sampled_from([50, 69])))
def pass_band(f, score):
    assert f(score) == "Pass"


@prop("Scores below 50 give \"Fail\".", score=st.one_of(st.integers(0, 49), st.just(49), st.integers(-1000, 49)))
def fail_band(f, score):
    assert f(score) == "Fail"


@prop("The result never gets worse as the score increases.", score=scores, delta=st.integers(min_value=0, max_value=30))
def monotone(f, score, delta):
    rank = {"Fail": 0, "Pass": 1, "Good": 2, "Excellent": 3}
    assert rank[f(score)] <= rank[f(score + delta)]

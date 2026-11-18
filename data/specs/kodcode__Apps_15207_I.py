"""Spec for can_form_teams: "Yes <n // k>" when k divides n, otherwise "No".

Domain: 1 <= n <= 10**9, 1 <= k <= 10**5.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_form_teams"

CLARIFICATIONS = [
    "Return the output as a string instead of printing it: \"Yes <students per team>\" (one space) or \"No\".",
]

ns = st.one_of(st.integers(1, 10**9), st.integers(1, 30))
ks = st.one_of(st.integers(1, 10**5), st.integers(1, 12))


@prop("The result is \"No\" or \"Yes \" followed by a positive integer.", n=ns, k=ks)
def well_formed(f, n, k):
    r = f(n, k)
    assert isinstance(r, str)
    assert r == "No" or (r.startswith("Yes ") and r[4:].isdigit() and int(r[4:]) >= 1)


@prop("The answer is Yes exactly when n is a multiple of k.", n=ns, k=ks)
def yes_iff_divisible(f, n, k):
    assert f(n, k).startswith("Yes") == (n % k == 0)


@prop("Exact multiples q * k give \"Yes q\".", q=st.integers(1, 10**4), k=ks)
def multiples(f, q, k):
    assert f(q * k, k) == f"Yes {q}"


@prop("Non-multiples give exactly \"No\".", q=st.integers(0, 10**4), k=st.integers(2, 10**5), data=st.data())
def non_multiples(f, q, k, data):
    r = data.draw(st.integers(1, k - 1))
    assert f(q * k + r, k) == "No"


@prop("One team takes everyone; n teams of n students take one each.", n=ns)
def trivial_splits(f, n):
    assert f(n, 1) == f"Yes {n}"
    if n <= 10**5:
        assert f(n, n) == "Yes 1"

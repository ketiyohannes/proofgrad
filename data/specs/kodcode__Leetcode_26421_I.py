"""Spec for calculate_average_scores: per-student averages, rounded to 2 decimals, sorted by average desc then name asc.

Domain: lists of dicts with "name" (str, duplicates allowed) and integer scores 0..100 under
"math", "science", "english"; the empty list gives [].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "calculate_average_scores"

CLARIFICATIONS = [
    "Each output dictionary has exactly the keys \"name\" and \"average\"; the average is a float rounded to 2 decimal places (e.g. 83.33, 76.67).",
    "Sort by the rounded average, highest first; break ties alphabetically by name. Students with the same name are kept as separate entries.",
    "Return [] for an empty list.",
]

names = st.sampled_from(["Alice", "Bob", "Charlie", "Dave", "Eve", "alice", "Zed"])
score = st.one_of(st.integers(0, 100), st.integers(70, 72))


@st.composite
def students(draw):
    n = draw(st.integers(0, 8))
    same = draw(st.booleans())
    base = (draw(score), draw(score), draw(score))
    out = []
    for _ in range(n):
        m, s, e = base if same and draw(st.booleans()) else (draw(score), draw(score), draw(score))
        out.append({"name": draw(names), "math": m, "science": s, "english": e})
    return out


def avg(s):
    return round((s["math"] + s["science"] + s["english"]) / 3, 2)


def close(a, b):
    return abs(a - b) < 1e-9


@prop("The result is a list of dicts with keys name and average, one per student.", studs=students())
def shape(f, studs):
    r = f(studs)
    assert isinstance(r, list) and len(r) == len(studs)
    assert all(isinstance(d, dict) and set(d) == {"name", "average"} for d in r)


@prop("The output pairs each student's name with their average rounded to 2 decimals.", studs=students())
def correct_averages(f, studs):
    r = f(studs)
    got = sorted((d["name"], round(d["average"], 6)) for d in r)
    want = sorted((s["name"], round(avg(s), 6)) for s in studs)
    assert got == want
    assert all(close(d["average"], round(d["average"], 2)) for d in r)


@prop("Entries are sorted by average in descending order.", studs=students())
def sorted_by_average(f, studs):
    a = [d["average"] for d in f(studs)]
    assert all(x >= y - 1e-9 for x, y in zip(a, a[1:]))


@prop("Entries with equal averages are ordered alphabetically by name.", studs=students())
def ties_by_name(f, studs):
    r = f(studs)
    for x, y in zip(r, r[1:]):
        if close(x["average"], y["average"]):
            assert x["name"] <= y["name"]


@prop("The full output matches the expected list exactly.", studs=students())
def exact_output(f, studs):
    want = sorted(({"name": s["name"], "average": avg(s)} for s in studs), key=lambda d: (-d["average"], d["name"]))
    r = f(studs)
    assert [d["name"] for d in r] == [d["name"] for d in want]
    assert all(close(x["average"], y["average"]) for x, y in zip(r, want))


@prop("An empty list gives [] and a single student gives a one-element list.", s=students())
def small_cases(f, s):
    assert f([]) == []
    if s:
        r = f(s[:1])
        assert len(r) == 1 and r[0]["name"] == s[0]["name"] and close(r[0]["average"], avg(s[0]))

"""Spec for manage_participants: process Add/Delete/Count queries and return the Count results in order.

Domain: queries is a list of strings "Add name score", "Delete name" or "Count lo hi" with names of
letters only, 1 <= score <= 10^7 and lo <= hi. Deleting an absent name does nothing; adding an
existing name replaces its score.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "manage_participants"

CLARIFICATIONS = [
    "queries is a list of query strings; return a list of ints holding the result of each Count query, in order (do not print).",
    "Deleting a name that is not in the list does nothing.",
]

names = st.sampled_from(["Alice", "Bob", "Charlie", "Dave", "Eve"])
scores = st.one_of(st.integers(1, 10), st.integers(1, 10**7))


@st.composite
def query(draw):
    kind = draw(st.sampled_from(["Add", "Add", "Delete", "Count"]))
    if kind == "Add":
        return f"Add {draw(names)} {draw(scores)}"
    if kind == "Delete":
        return f"Delete {draw(names)}"
    lo = draw(scores)
    hi = draw(st.one_of(st.just(lo), st.integers(lo, lo + 10), st.integers(lo, 10**7)))
    return f"Count {lo} {hi}"


query_lists = st.lists(query(), max_size=25)


def simulate(queries):
    """Replay the queries on an explicit list of (name, score) entries."""
    entries = []
    out = []
    for q in queries:
        parts = q.split()
        if parts[0] == "Add":
            entries = [e for e in entries if e[0] != parts[1]] + [(parts[1], int(parts[2]))]
        elif parts[0] == "Delete":
            entries = [e for e in entries if e[0] != parts[1]]
        else:
            lo, hi = int(parts[1]), int(parts[2])
            out.append(len([1 for _, s in entries if lo <= s <= hi]))
    return out


@prop("The result is a list with one int per Count query.", qs=query_lists)
def one_result_per_count(f, qs):
    result = f(qs)
    assert isinstance(result, list)
    assert len(result) == sum(q.startswith("Count") for q in qs)
    assert all(isinstance(r, int) for r in result)


@prop("Every Count result equals the number of current participants with lo <= score <= hi.", qs=query_lists)
def matches_simulation(f, qs):
    assert f(qs) == simulate(qs)


@prop("Re-adding a participant replaces their score instead of adding a second entry.", name=names, a=st.integers(1, 100), b=st.integers(1, 100))
def add_updates(f, name, a, b):
    assert f([f"Add {name} {a}", f"Add {name} {b}", "Count 1 100", f"Count {b} {b}"]) == [1, 1]


@prop("Deleting removes a participant; deleting an absent one changes nothing.", name=names, other=names, s=st.integers(1, 100))
def delete_behaviour(f, name, other, s):
    qs = [f"Add {name} {s}", f"Delete {other}", f"Count {s} {s}", f"Delete {name}", f"Count 1 100"]
    assert f(qs) == [0 if other == name else 1, 0]


@prop("Count bounds are inclusive at both ends.", s=st.integers(2, 10**7 - 1))
def inclusive_bounds(f, s):
    qs = [f"Add A {s}", f"Count {s} {s + 1}", f"Count {s - 1} {s}", f"Count {s + 1} {s + 2}", f"Count {s - 1} {s - 1}"]
    assert f(qs) == [1, 1, 0, 0]


@prop("With no Count queries the result is empty.", qs=st.lists(query().filter(lambda q: not q.startswith("Count")), max_size=10))
def no_counts(f, qs):
    assert f(qs) == []

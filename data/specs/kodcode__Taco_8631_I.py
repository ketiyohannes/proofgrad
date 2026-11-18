"""Spec for can_form_teams: whether participants can be split into teams so every preference pair shares a team.

Domain: 1 <= n <= 12, 1 <= k <= n, preferences are (u, v) tuples with 1 <= u, v <= n, u != v, p == len(preferences).
The reference answers "YES" iff every connected component of the preference graph has at most k
members, i.e. it treats k as a maximum team size and ignores how components pack into teams of k.
The statement asks for "teams of k participants each", and its first sample (k = 2, answer YES
via teams of size 3) contradicts the reference, which returns "NO" for it.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_form_teams"

EXCLUDE_REASON = (
    "The statement asks for teams of exactly k participants and its first sample (k=2, expected YES with "
    "teams of 3) contradicts the reference, which treats k as a maximum team size and returns NO for that sample."
)

CLARIFICATIONS = [
    "Teams may have at most k members, and the number of teams is unrestricted.",
    "Return the string \"YES\" or \"NO\".",
]


@st.composite
def instance(draw):
    n = draw(st.integers(1, 12))
    k = draw(st.integers(1, n))
    pairs = [(u, v) for u in range(1, n + 1) for v in range(1, n + 1) if u != v]
    prefs = draw(st.lists(st.sampled_from(pairs), max_size=15)) if pairs else []
    return n, k, prefs


def components(n, prefs):
    label = list(range(n + 1))
    changed = True
    while changed:
        changed = False
        for u, v in prefs:
            m = min(label[u], label[v])
            if label[u] != m or label[v] != m:
                label[u] = label[v] = m
                changed = True
    sizes = {}
    for x in range(1, n + 1):
        sizes[label[x]] = sizes.get(label[x], 0) + 1
    return list(sizes.values())


@prop("The answer is YES exactly when every group of participants linked by preferences fits in one team of at most k.", inst=instance())
def matches_definition(f, inst):
    n, k, prefs = inst
    expected = "YES" if max(components(n, prefs)) <= k else "NO"
    assert f(n, len(prefs), k, prefs) == expected


@prop("Without preferences the answer is YES.", n=st.integers(1, 100), data=st.data())
def no_preferences(f, n, data):
    k = data.draw(st.integers(1, n))
    assert f(n, 0, k, []) == "YES"


@prop("A chain linking m participants needs k >= m.", m=st.integers(2, 10), k=st.integers(1, 10))
def chain(f, m, k):
    prefs = [(i, i + 1) for i in range(1, m)]
    n = max(m, k)
    assert f(n, len(prefs), k, prefs) == ("YES" if m <= k else "NO")

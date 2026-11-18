"""Spec for smallest_friendship_closure: n if all employees are connected through chains of friendships, else -1.

Domain: n >= 1; friendships is a list of 2-tuples of distinct IDs in 0..n-1 (duplicates possible).
Interpretation (from the reference and unit tests): direct and indirect friends both count as friends,
so the only closure containing everyone has size n, and it exists iff the friendship graph is connected.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "smallest_friendship_closure"

CLARIFICATIONS = [
    "Indirect friends (connected through a chain of friendships) count as friends, so if every employee is directly or indirectly friends with every other, the answer is n; otherwise return -1.",
    "A single employee with no friendships forms a closure of size 1.",
]


@st.composite
def graphs(draw):
    n = draw(st.integers(1, 9))
    if n == 1:
        return 1, []
    pairs = [(a, b) for a in range(n) for b in range(n) if a != b]
    shape = draw(st.sampled_from(["random", "tree", "tree_minus", "sparse"]))
    if shape in ("tree", "tree_minus"):
        order = draw(st.permutations(list(range(n))))
        edges = [(order[i], order[draw(st.integers(0, i - 1))]) for i in range(1, n)]
        edges += draw(st.lists(st.sampled_from(pairs), max_size=4))
        if shape == "tree_minus":
            edges = edges[:n - 2] if draw(st.booleans()) else edges[1:n - 1]
    else:
        edges = draw(st.lists(st.sampled_from(pairs), max_size=n if shape == "sparse" else 2 * n))
    edges = draw(st.permutations(edges))
    return n, [tuple(e) for e in edges]


def connected(n, edges):
    reach = {0}
    changed = True
    while changed:
        changed = False
        for a, b in edges:
            if (a in reach) != (b in reach):
                reach |= {a, b}
                changed = True
    return len(reach) == n


@prop("The result is n when all employees are connected and -1 otherwise.", g=graphs())
def matches_definition(f, g):
    n, edges = g
    assert f(n, edges) == (n if connected(n, edges) else -1)


@prop("The result is always either n or -1.", g=graphs())
def result_range(f, g):
    n, edges = g
    r = f(n, edges)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r in (n, -1)


@prop("Adding friendships never turns a full closure into -1.", g=graphs(), data=st.data())
def adding_edges_monotone(f, g, data):
    n, edges = g
    if n > 1 and f(n, edges) == n:
        extra = data.draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)).filter(lambda e: e[0] != e[1]), max_size=3))
        assert f(n, edges + extra) == n


@prop("A chain 0-1-...-(n-1) connects everyone; dropping a link disconnects it.", n=st.integers(2, 12), cut=st.integers(0, 20))
def chain(f, n, cut):
    edges = [(i, i + 1) for i in range(n - 1)]
    assert f(n, edges) == n
    c = cut % (n - 1)
    assert f(n, edges[:c] + edges[c + 1:]) == -1


@prop("One employee gives 1 and several employees without friendships give -1.", n=st.integers(2, 12))
def edge_cases(f, n):
    assert f(1, []) == 1
    assert f(n, []) == -1

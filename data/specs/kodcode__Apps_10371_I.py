"""Spec for max_infection_time: the largest BFS distance (in streets) from S to any neighborhood reachable from S.

Domain: N in 2..9 neighborhoods numbered 1..N, M == len(streets) >= 1, streets are pairs (u, v)
of neighborhoods (u != v, duplicates allowed), S in 1..N.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_infection_time"

CLARIFICATIONS = [
    "streets is a list of (u, v) pairs and M == len(streets); streets are bidirectional.",
    "Return the answer as an int; neighborhoods not reachable from S are ignored.",
]


@st.composite
def graphs(draw, shape=None):
    n = draw(st.integers(min_value=2, max_value=9))
    shape = shape or draw(st.sampled_from(["random", "path", "sparse", "dense"]))
    if shape == "path":
        order = draw(st.permutations(list(range(1, n + 1))))
        edges = [(order[i], order[i + 1]) for i in range(n - 1)]
        extra = draw(st.lists(st.tuples(st.integers(1, n), st.integers(1, n)).filter(lambda p: p[0] != p[1]), max_size=2))
        edges += extra
    else:
        size = {"random": (1, 12), "sparse": (1, 3), "dense": (8, 20)}[shape]
        edges = draw(st.lists(st.tuples(st.integers(1, n), st.integers(1, n)).filter(lambda p: p[0] != p[1]),
                              min_size=size[0], max_size=size[1]))
    edges = list(draw(st.permutations(edges)))
    s = draw(st.integers(1, n))
    return n, edges, s


def distances(n, edges, s):
    """Shortest street-count distance from s to each reachable node, by repeated relaxation."""
    dist = {s: 0}
    changed = True
    while changed:
        changed = False
        for u, v in edges:
            for a, b in ((u, v), (v, u)):
                if a in dist and (b not in dist or dist[a] + 1 < dist[b]):
                    dist[b] = dist[a] + 1
                    changed = True
    return dist


@prop("The result is an int equal to the largest shortest-path distance from S to a reachable neighborhood.", g=graphs())
def matches_eccentricity(f, g):
    n, edges, s = g
    r = f(n, len(edges), edges, s)
    assert isinstance(r, int)
    assert r == max(distances(n, edges, s).values())


@prop("When S has no streets, the result is 0.", g=graphs(shape="sparse"))
def isolated_start(f, g):
    n, edges, s = g
    used = {x for e in edges for x in e}
    isolated = [x for x in range(1, n + 1) if x not in used]
    if isolated:
        assert f(n, len(edges), edges, isolated[0]) == 0


@prop("On a simple path, starting from an end gives (path length - 1) minutes.",
      n=st.integers(min_value=2, max_value=30))
def path_from_end(f, n):
    edges = [(i, i + 1) for i in range(1, n)]
    assert f(n, len(edges), edges, 1) == n - 1
    assert f(n, len(edges), edges, n) == n - 1


@prop("Streets in other components do not change the answer.", g=graphs())
def other_components_ignored(f, g):
    n, edges, s = g
    extra = [(n + 1, n + 2), (n + 2, n + 3), (n + 3, n + 4), (n + 4, n + 5)]
    all_edges = edges + extra
    assert f(n + 5, len(all_edges), all_edges, s) == max(distances(n, edges, s).values())


@prop("Reordering streets or swapping the ends of a street does not change the answer.", g=graphs(), data=st.data())
def order_invariant(f, g, data):
    n, edges, s = g
    shuffled = [(v, u) for u, v in data.draw(st.permutations(edges))]
    assert f(n, len(edges), edges, s) == f(n, len(shuffled), shuffled, s)


@prop("A star centered at S takes 1 minute, and from a leaf it takes 2 minutes (with at least 3 nodes).",
      n=st.integers(min_value=2, max_value=20))
def star(f, n):
    edges = [(1, i) for i in range(2, n + 1)]
    assert f(n, len(edges), edges, 1) == 1
    assert f(n, len(edges), edges, n) == (1 if n == 2 else 2)

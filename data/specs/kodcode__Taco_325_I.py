"""Spec for largest_connected_component: size of the largest connected component of an undirected graph on vertices 1..n.

Domain: n >= 1, edges is a list of tuples (u, v) with 1 <= u, v <= n, u != v, and no pair of vertices
joined twice (in either orientation). Isolated vertices count as components of size 1.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "largest_connected_component"

CLARIFICATIONS = [
    "edges is a list of (u, v) tuples; vertices that appear in no edge are components of size 1.",
    "Return the size as an int.",
]


@st.composite
def graphs(draw, max_n=12):
    n = draw(st.integers(1, max_n))
    pairs = [(u, v) for u in range(1, n + 1) for v in range(u + 1, n + 1)]
    density = draw(st.sampled_from([0.0, 0.1, 0.25, 0.5, 1.0]))
    chosen = [p for p in pairs if draw(st.floats(0, 1)) < density] if pairs else []
    edges = [(v, u) if draw(st.booleans()) else (u, v) for u, v in chosen]
    edges = list(draw(st.permutations(edges)))
    return n, edges


def component_sizes(n, edges):
    """Label propagation: repeatedly give both ends of every edge the smaller label until stable."""
    label = list(range(n + 1))
    changed = True
    while changed:
        changed = False
        for u, v in edges:
            m = min(label[u], label[v])
            if label[u] != m or label[v] != m:
                label[u] = label[v] = m
                changed = True
    sizes = {}
    for x in range(1, n + 1):
        sizes[label[x]] = sizes.get(label[x], 0) + 1
    return sorted(sizes.values())


@prop("The result is an int equal to the size of the largest connected component.", g=graphs())
def matches_definition(f, g):
    n, edges = g
    result = f(n, edges)
    assert isinstance(result, int)
    assert result == component_sizes(n, edges)[-1]


@prop("With no edges the answer is 1.", n=st.integers(1, 1000))
def no_edges(f, n):
    assert f(n, []) == 1


@prop("A path through all vertices in any order gives n.", n=st.integers(1, 30), data=st.data())
def path_spans_all(f, n, data):
    order = data.draw(st.permutations(list(range(1, n + 1))))
    edges = [(order[i], order[i + 1]) for i in range(n - 1)]
    assert f(n, edges) == n


@prop("Renumbering the vertices does not change the answer.", g=graphs(), data=st.data())
def relabel_invariant(f, g, data):
    n, edges = g
    perm = data.draw(st.permutations(list(range(1, n + 1))))
    mapped = [(perm[u - 1], perm[v - 1]) for u, v in edges]
    assert f(n, mapped) == f(n, edges)


@prop("Adding isolated vertices does not change the answer.", g=graphs(), extra=st.integers(1, 5))
def isolated_vertices_ignored(f, g, extra):
    n, edges = g
    expected = component_sizes(n, edges)[-1]
    assert f(n + extra, edges) == expected


@prop("Two disjoint cliques: the answer is the larger clique size.", a=st.integers(1, 7), b=st.integers(1, 7))
def two_cliques(f, a, b):
    edges = [(u, v) for u in range(1, a + 1) for v in range(u + 1, a + 1)]
    edges += [(a + u, a + v) for u in range(1, b + 1) for v in range(u + 1, b + 1)]
    assert f(a + b, edges) == max(a, b)

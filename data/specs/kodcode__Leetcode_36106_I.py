"""Spec for bfs_shortest_path: number of edges on a shortest path between start and end, or -1.

Domain: undirected graphs given as symmetric adjacency dicts whose keys are every node (integers
1..n, isolated nodes map to []); start and end are nodes of the graph. The graph may be
disconnected (the unit tests expect -1 then).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "bfs_shortest_path"

CLARIFICATIONS = [
    "The graph may be disconnected; return -1 when end is unreachable from start.",
    "The path length is the number of edges; it is 0 when start equals end.",
]

INF = float("inf")


@st.composite
def graphs(draw, max_n=8):
    n = draw(st.integers(min_value=1, max_value=max_n))
    pairs = [(a, b) for a in range(1, n + 1) for b in range(a + 1, n + 1)]
    density = draw(st.sampled_from([0.15, 0.3, 0.6]))
    edges = [p for p in pairs if draw(st.floats(min_value=0, max_value=1, exclude_max=True)) < density]
    graph = {v: [] for v in range(1, n + 1)}
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    start = draw(st.integers(min_value=1, max_value=n))
    end = draw(st.integers(min_value=1, max_value=n))
    return graph, start, end


def distances(graph):
    """Floyd-Warshall all-pairs shortest path lengths."""
    nodes = list(graph)
    d = {(a, b): (0 if a == b else (1 if b in graph[a] else INF)) for a in nodes for b in nodes}
    for k in nodes:
        for a in nodes:
            for b in nodes:
                if d[a, k] + d[k, b] < d[a, b]:
                    d[a, b] = d[a, k] + d[k, b]
    return d


def expected(graph, s, e):
    v = distances(graph)[s, e]
    return -1 if v == INF else v


@prop("The result is an int equal to the shortest-path edge count, or -1 when end is unreachable.", case=graphs())
def matches_shortest(f, case):
    g, s, e = case
    r = f(g, s, e)
    assert isinstance(r, int)
    assert r == expected(g, s, e)


@prop("Shortest path length is symmetric in an undirected graph.", case=graphs())
def symmetric(f, case):
    g, s, e = case
    assert f(g, s, e) == f(g, e, s)


@prop("On a simple path graph 1-2-...-n, the distance between i and j is |i - j|.",
      n=st.integers(min_value=1, max_value=15), data=st.data())
def path_graph(f, n, data):
    g = {v: [u for u in (v - 1, v + 1) if 1 <= u <= n] for v in range(1, n + 1)}
    i = data.draw(st.integers(min_value=1, max_value=n))
    j = data.draw(st.integers(min_value=1, max_value=n))
    assert f(g, i, j) == abs(i - j)


@prop("A shortcut edge is used: in a cycle the shorter way around is taken.",
      n=st.integers(min_value=3, max_value=14), data=st.data())
def cycle_graph(f, n, data):
    g = {v: [(v % n) + 1, ((v - 2) % n) + 1] for v in range(1, n + 1)}
    j = data.draw(st.integers(min_value=1, max_value=n))
    assert f(g, 1, j) == min(j - 1, n - (j - 1))


@prop("Nodes in different components give -1; any node to itself gives 0.", case=graphs(max_n=6))
def disconnected_and_self(f, case):
    g, s, e = case
    n = len(g)
    shifted = {v + n: [u + n for u in nbrs] for v, nbrs in g.items()}
    merged = {**g, **shifted}
    assert f(merged, s, e + n) == -1
    assert f(merged, s, s) == 0

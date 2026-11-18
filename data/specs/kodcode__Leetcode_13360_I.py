"""Spec for find_min_max_edge_path: a start-to-end path whose largest edge weight is as small as possible, or [] if unreachable.

Domain: n nodes 0..n-1, undirected edges [u, v, w] with u != v (parallel edges allowed) and non-negative integer
weights. Per the unit tests the graph may be disconnected, in which case [] is returned when end is unreachable.
If start == end the path is just [start].
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_min_max_edge_path"

CLARIFICATIONS = [
    "Return the path as a list of node labels beginning with start and ending with end, where consecutive nodes are joined by an edge.",
    "Edge weights are non-negative; the graph may be disconnected, and if end cannot be reached return [].",
    "If start == end, return [start].",
]


@st.composite
def graphs(draw, connected=None):
    n = draw(st.integers(1, 7))
    wmax = draw(st.sampled_from([1, 3, 20]))
    edges = []
    if connected if connected is not None else draw(st.booleans()):
        # A random spanning tree guarantees connectivity.
        for v in range(1, n):
            edges.append([draw(st.integers(0, v - 1)), v, draw(st.integers(0, wmax))])
    if n >= 2:
        extra = draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1), st.integers(0, wmax)), max_size=10))
        edges += [[u, v, w] for u, v, w in extra if u != v]
    order = draw(st.permutations(range(len(edges))))
    edges = [edges[i] for i in order]
    start = draw(st.integers(0, n - 1))
    end = draw(st.integers(0, n - 1))
    return n, edges, start, end


def reachable(n, edges, start, end, limit=None):
    adj = {v: set() for v in range(n)}
    for u, v, w in edges:
        if limit is None or w <= limit:
            adj[u].add(v)
            adj[v].add(u)
    seen, stack = {start}, [start]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return end in seen


def best_bottleneck(n, edges, start, end):
    """Smallest weight w such that end is reachable using only edges of weight <= w (0 for start == end)."""
    if start == end:
        return 0
    for w in sorted({e[2] for e in edges}):
        if reachable(n, edges, start, end, w):
            return w
    return None


def path_cost(edges, path):
    """Largest edge used by the path, picking the lightest edge between each consecutive pair; None if not a path."""
    cost = 0
    for a, b in zip(path, path[1:]):
        ws = [w for u, v, w in edges if {u, v} == {a, b}]
        if not ws:
            return None
        cost = max(cost, min(ws))
    return cost


@prop("When end is reachable, the result is a list from start to end whose consecutive nodes are joined by edges.", g=graphs())
def valid_path(f, g):
    n, edges, start, end = g
    if not reachable(n, edges, start, end):
        return
    p = f(n, edges, start, end)
    assert isinstance(p, list) and len(p) >= 1
    assert p[0] == start and p[-1] == end
    assert path_cost(edges, p) is not None


@prop("The largest edge weight on the returned path is the smallest possible over all start-to-end paths.", g=graphs(connected=True))
def bottleneck_is_minimal(f, g):
    n, edges, start, end = g
    p = f(n, edges, start, end)
    cost = path_cost(edges, p)
    assert cost is not None and p[0] == start and p[-1] == end
    assert cost == best_bottleneck(n, edges, start, end)


@prop("If end cannot be reached from start, the result is [].", g=graphs(connected=False))
def unreachable_empty(f, g):
    n, edges, start, end = g
    # Cut every edge touching `end` so it is isolated (unless it is the start).
    if start == end:
        return
    cut = [e for e in edges if end not in (e[0], e[1])]
    assert f(n, cut, start, end) == []


@prop("A cheap detour is preferred over an expensive direct edge.", w_direct=st.integers(5, 100), w_cheap=st.integers(0, 4), hops=st.integers(1, 4))
def prefers_cheap_detour(f, w_direct, w_cheap, hops):
    n = hops + 2
    end = n - 1
    edges = [[0, end, w_direct]] + [[i, i + 1, w_cheap] for i in range(end)]
    assert f(n, edges, 0, end) == list(range(n))


@prop("When start equals end the path is just [start].", g=graphs(connected=True))
def start_equals_end(f, g):
    n, edges, start, _ = g
    assert f(n, edges, start, start) == [start]

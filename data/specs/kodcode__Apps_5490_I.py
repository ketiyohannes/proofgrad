"""Spec for process_queries: apply updates and answer "max value reachable" queries on a grid.

A move goes to a 4-neighbour whose value is >= the current cell's value. Domain: grids
with 1..5 rows and columns, values in a small range (to create ties) or up to +-10**9;
queries use 1-based indices; there is at least one type-2 query.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "process_queries"

CLARIFICATIONS = [
    "Queries are lists: [1, i, j, val] for an update and [2, i, j] for a reachability query, with 1-based row i and column j.",
    "Return a list with the answers of the type-2 queries, in query order.",
    "Updates persist for all later queries.",
]


def reach_max(grid, i, j):
    rows, cols = len(grid), len(grid[0])
    seen = {(i, j)}
    stack = [(i, j)]
    while stack:
        r, c = stack.pop()
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in seen and grid[nr][nc] >= grid[r][c]:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return max(grid[r][c] for r, c in seen)


@st.composite
def instances(draw, allow_updates=True):
    m = draw(st.integers(1, 5))
    n = draw(st.integers(1, 5))
    values = draw(st.sampled_from([st.integers(-3, 3), st.integers(0, 9), st.integers(-10**9, 10**9)]))
    grid = [[draw(values) for _ in range(n)] for _ in range(m)]
    queries = []
    for _ in range(draw(st.integers(1, 10))):
        i, j = draw(st.integers(1, m)), draw(st.integers(1, n))
        if allow_updates and draw(st.booleans()):
            queries.append([1, i, j, draw(values)])
        else:
            queries.append([2, i, j])
    if not any(q[0] == 2 for q in queries):
        queries.append([2, draw(st.integers(1, m)), draw(st.integers(1, n))])
    return m, n, grid, queries


def expected(grid, queries):
    g = [row[:] for row in grid]
    out = []
    for q in queries:
        if q[0] == 1:
            g[q[1] - 1][q[2] - 1] = q[3]
        else:
            out.append(reach_max(g, q[1] - 1, q[2] - 1))
    return out


@prop("The result has one answer per type-2 query.", inst=instances())
def answer_count(f, inst):
    m, n, grid, queries = inst
    result = f(m, n, grid, queries)
    assert isinstance(result, list)
    assert len(result) == sum(1 for q in queries if q[0] == 2)


@prop("Without updates, each answer is the maximum value reachable through non-decreasing moves.",
      inst=instances(allow_updates=False))
def static_answers(f, inst):
    m, n, grid, queries = inst
    assert f(m, n, grid, queries) == expected(grid, queries)


@prop("Without updates, every answer is at least the value of the starting cell.", inst=instances(allow_updates=False))
def at_least_start(f, inst):
    m, n, grid, queries = inst
    for q, ans in zip(queries, f(m, n, grid, queries)):
        assert ans >= grid[q[1] - 1][q[2] - 1]


@prop("Updates change the grid for all later queries.", inst=instances())
def with_updates(f, inst):
    m, n, grid, queries = inst
    assert f(m, n, grid, queries) == expected(grid, queries)


@prop("A cell with no neighbour of greater or equal value answers its own value.",
      m=st.integers(1, 5), n=st.integers(1, 5), data=st.data())
def isolated_peak(f, m, n, data):
    i, j = data.draw(st.integers(1, m)), data.draw(st.integers(1, n))
    grid = [[data.draw(st.integers(-100, 99)) for _ in range(n)] for _ in range(m)]
    grid[i - 1][j - 1] = 100
    assert f(m, n, grid, [[2, i, j]]) == [100]

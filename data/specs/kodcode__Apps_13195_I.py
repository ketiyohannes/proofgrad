"""Spec for can_reach_end: whether the bottom-right cell is 4-directionally reachable from the top-left through 'O' cells.

Domain: rectangular grids of 'O'/'X', 1..7 rows and 1..7 columns, with both corners 'O'; separately,
grids whose top-left or bottom-right corner is 'X' (the unit tests check an obstructed start).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_reach_end"

CLARIFICATIONS = [
    "A 1x1 grid (start equals end) returns True.",
    "If the top-left or bottom-right cell is 'X', return False.",
]


@st.composite
def grids(draw, min_side=1):
    n = draw(st.integers(min_side, 7))
    m = draw(st.integers(min_side, 7))
    density = draw(st.sampled_from([0.0, 0.2, 0.35, 0.5, 0.7]))
    cells = draw(st.lists(st.floats(0, 1), min_size=n * m, max_size=n * m))
    g = [["X" if cells[i * m + j] < density else "O" for j in range(m)] for i in range(n)]
    g[0][0] = "O"
    g[n - 1][m - 1] = "O"
    return g


def reachable(g):
    n, m = len(g), len(g[0])
    seen = {(0, 0)}
    changed = True
    while changed:
        changed = False
        for i in range(n):
            for j in range(m):
                if (i, j) not in seen and g[i][j] == "O":
                    if any((i + di, j + dj) in seen for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        seen.add((i, j))
                        changed = True
    return (n - 1, m - 1) in seen


@prop("The result is a bool that is True exactly when a 4-directional path of 'O' cells connects the corners.", g=grids())
def matches_reachability(f, g):
    r = f(g)
    assert r is True or r is False
    assert r == reachable(g)


@prop("A grid with no obstructions is always passable.", n=st.integers(1, 8), m=st.integers(1, 8))
def open_grid(f, n, m):
    assert f([["O"] * m for _ in range(n)]) is True


@prop("A full wall of 'X' across a middle row blocks every path.", g=grids(), data=st.data())
def row_wall_blocks(f, g, data):
    n = len(g)
    if n >= 3:
        r = data.draw(st.integers(1, n - 2))
        g = [row[:] for row in g]
        g[r] = ["X"] * len(g[r])
        assert f(g) is False


SERPENTINE = [
    ["O", "O", "O", "O"],
    ["X", "X", "X", "O"],
    ["O", "O", "O", "O"],
    ["O", "X", "X", "X"],
    ["O", "O", "O", "O"],
]
U_SHAPE = [
    ["O", "X", "O", "O", "O"],
    ["O", "X", "O", "X", "O"],
    ["O", "O", "O", "X", "O"],
    ["X", "X", "X", "X", "O"],
]


@prop("Paths may need to move left and up, not only right and down.", flip=st.booleans())
def needs_left_and_up_moves(f, flip):
    g = U_SHAPE if flip else SERPENTINE
    assert f([row[:] for row in g]) is True
    # Closing the only corridor makes it unreachable.
    blocked = [row[:] for row in g]
    if flip:
        blocked[1][2] = "X"
    else:
        blocked[3][0] = "X"
    assert f(blocked) is False


@prop("Diagonal adjacency does not count as a connection.", n=st.integers(2, 7))
def no_diagonal_moves(f, n):
    g = [["O" if i == j else "X" for j in range(n)] for i in range(n)]
    assert f(g) is False


@prop("If the start or the end cell is obstructed, the result is False.", g=grids(), which=st.sampled_from(["start", "end", "both"]))
def obstructed_corner(f, g, which):
    g = [row[:] for row in g]
    if which in ("start", "both"):
        g[0][0] = "X"
    if which in ("end", "both"):
        g[-1][-1] = "X"
    assert f(g) is False

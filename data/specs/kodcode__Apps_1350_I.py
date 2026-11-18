"""Spec for spiral_order: list every matrix element once, walking clockwise from the top-left (right, down, left, up) and spiralling inwards.

Domain: rectangular matrices of integers with 1..8 rows and 1..8 columns, plus the empty matrix [] that the
unit tests check. Matrices with empty rows (e.g. [[]]) are not generated.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "spiral_order"

CLARIFICATIONS = [
    "Return the elements as a list; an empty matrix [] gives [].",
]


@st.composite
def matrices(draw, distinct=False):
    """Rectangular matrices, biased toward single rows, single columns, squares and 2-wide shapes."""
    m = draw(st.one_of(st.just(1), st.just(2), st.integers(min_value=1, max_value=8)))
    n = draw(st.one_of(st.just(1), st.just(2), st.just(m), st.integers(min_value=1, max_value=8)))
    if distinct:
        flat = draw(st.lists(st.integers(-1000, 1000), min_size=m * n, max_size=m * n, unique=True))
    else:
        flat = draw(st.lists(st.integers(-9, 9), min_size=m * n, max_size=m * n))
    return [flat[r * n:(r + 1) * n] for r in range(m)]


def walk(matrix):
    """Move in the current direction until the next cell is off-grid or already visited, then turn clockwise."""
    m, n = len(matrix), len(matrix[0])
    seen = [[False] * n for _ in range(m)]
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r = c = d = 0
    out = []
    for _ in range(m * n):
        out.append(matrix[r][c])
        seen[r][c] = True
        nr, nc = r + dirs[d][0], c + dirs[d][1]
        if not (0 <= nr < m and 0 <= nc < n) or seen[nr][nc]:
            d = (d + 1) % 4
            nr, nc = r + dirs[d][0], c + dirs[d][1]
        r, c = nr, nc
    return out


def rotate_ccw(matrix):
    """Rotate counter-clockwise so that the old last column becomes the new first row."""
    if not matrix:
        return []
    return [list(col) for col in zip(*matrix)][::-1]


@prop("The output matches a step-by-step clockwise walk that turns right whenever it would leave the grid or revisit a cell.",
      matrix=matrices(distinct=True))
def matches_walk(f, matrix):
    assert f(matrix) == walk(matrix)


@prop("The output is the first row followed by the spiral order of the remaining rows rotated counter-clockwise.",
      matrix=matrices())
def recursive_peel(f, matrix):
    rest = rotate_ccw(matrix[1:])
    expected_tail = f(rest) if rest and rest[0] else []
    assert f(matrix) == matrix[0] + expected_tail


@prop("The output is a list containing every matrix entry exactly once.", matrix=matrices(distinct=True))
def is_permutation(f, matrix):
    out = f(matrix)
    assert isinstance(out, list)
    assert sorted(out) == sorted(x for row in matrix for x in row)


@prop("A single-row matrix is returned left to right.", row=st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def single_row(f, row):
    assert f([list(row)]) == row


@prop("A single-column matrix is returned top to bottom.", col=st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def single_column(f, col):
    assert f([[x] for x in col]) == col


@prop("An empty matrix yields an empty list.", dummy=st.just(None))
def empty_matrix(f, dummy):
    assert f([]) == []

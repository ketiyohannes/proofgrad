"""Spec for find_diagonal_order: matrix elements listed anti-diagonal by anti-diagonal, each top to bottom.

Domain: rectangular integer matrices (all rows equal length), plus the empty matrices [] and [[]].
Order (from the reference and unit tests): anti-diagonals by increasing row+col; within one
anti-diagonal, elements from the top row downward.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_diagonal_order"

CLARIFICATIONS = [
    "Each diagonal consists of the cells with the same row + column sum; output the diagonals in increasing order of that sum.",
    "Within one diagonal, list elements from the top row to the bottom row (i.e. moving down and to the left).",
    "Return [] for an empty matrix ([] or [[]]).",
]


@st.composite
def matrices(draw, distinct=False):
    m = draw(st.integers(1, 6))
    n = draw(st.integers(1, 6))
    if distinct:
        vals = draw(st.permutations(list(range(m * n))))
        vals = [v * 3 - 7 for v in vals]
    else:
        vals = draw(st.lists(st.integers(-5, 5), min_size=m * n, max_size=m * n))
    return [vals[i * n:(i + 1) * n] for i in range(m)]


def expected(mat):
    m, n = len(mat), len(mat[0])
    out = []
    for d in range(m + n - 1):
        for i in range(m):
            j = d - i
            if 0 <= j < n:
                out.append(mat[i][j])
    return out


@prop("The result is a list holding exactly the matrix elements (a permutation of them).", mat=matrices())
def is_permutation(f, mat):
    r = f(mat)
    assert isinstance(r, list)
    assert sorted(r) == sorted(x for row in mat for x in row)


@prop("Elements appear grouped by anti-diagonal in increasing order of row + column.", mat=matrices(distinct=True))
def diagonals_in_order(f, mat):
    where = {mat[i][j]: i + j for i in range(len(mat)) for j in range(len(mat[0]))}
    sums = [where[x] for x in f(mat)]
    assert sums == sorted(sums)


@prop("Within each anti-diagonal elements go from the top row to the bottom row.", mat=matrices(distinct=True))
def top_to_bottom_within_diagonal(f, mat):
    where = {mat[i][j]: (i + j, i) for i in range(len(mat)) for j in range(len(mat[0]))}
    keys = [where[x] for x in f(mat)]
    assert keys == sorted(keys)


@prop("The output matches the anti-diagonal order exactly.", mat=matrices())
def exact_order(f, mat):
    assert f(mat) == expected(mat)


@prop("A single row or a single column is returned in its natural order.", xs=st.lists(st.integers(-9, 9), min_size=1, max_size=8))
def row_and_column(f, xs):
    assert f([list(xs)]) == xs
    assert f([[x] for x in xs]) == xs


@prop("Empty matrices give an empty list.", dummy=st.just(None))
def empty_matrix(f, dummy):
    assert f([]) == []
    assert f([[]]) == []

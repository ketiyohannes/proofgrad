"""Spec for kth_smallest: the k-th smallest value (1-indexed, counting duplicates) in a matrix with sorted rows.

Domain used below: non-empty rectangular matrices whose rows AND columns are non-decreasing, 1 <= k <= m * n.
The statement only promises sorted rows, but the reference returns wrong answers when columns are unsorted
(e.g. [[5], [1]] with k = 1 gives 5), so the problem is excluded.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "kth_smallest"

EXCLUDE_REASON = (
    "The statement only guarantees that each row is sorted, but the reference only scans the first k rows and so "
    "returns wrong answers when columns are unsorted (e.g. [[5], [1]], k = 1 returns 5 instead of 1)."
)

CLARIFICATIONS = ["k is 1-indexed and duplicates count separately (k-th element of the sorted list of all values)."]


@st.composite
def matrix_and_k(draw):
    m = draw(st.integers(1, 6))
    n = draw(st.integers(1, 6))
    step = draw(st.sampled_from([0, 1, 5]))
    # Sorted rows and columns: each cell is >= its upper and left neighbours.
    mat = []
    for i in range(m):
        row = []
        for j in range(n):
            base = max(mat[i - 1][j] if i else -20, row[j - 1] if j else -20)
            row.append(base + draw(st.integers(0, step)))
        mat.append(row)
    k = draw(st.integers(1, m * n))
    return mat, k


@prop("The result is the k-th element of the sorted list of all matrix values.", case=matrix_and_k())
def matches_sorted_order(f, case):
    mat, k = case
    assert f(mat, k) == sorted(v for row in mat for v in row)[k - 1]


@prop("Exactly fewer than k values are strictly smaller than the result, and at least k are smaller or equal.", case=matrix_and_k())
def rank_condition(f, case):
    mat, k = case
    r = f(mat, k)
    vals = [v for row in mat for v in row]
    assert sum(v < r for v in vals) < k <= sum(v <= r for v in vals)


@prop("k = 1 gives the minimum and k = m * n gives the maximum.", case=matrix_and_k())
def extremes(f, case):
    mat, _ = case
    vals = [v for row in mat for v in row]
    assert f(mat, 1) == min(vals)
    assert f(mat, len(vals)) == max(vals)

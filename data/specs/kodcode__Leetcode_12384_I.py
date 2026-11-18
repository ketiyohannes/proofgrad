"""Spec for trapWater: total rain water trapped by an elevation map of unit-width bars.

Domain: arr is a (possibly empty) list of non-negative integer heights, as the reference
docstring states; negative heights are not generated.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "trapWater"

CLARIFICATIONS = [
    "All heights are non-negative integers.",
    "Return 0 for an empty array.",
    "Return the total as an int.",
]

h = st.integers(min_value=0, max_value=8)

heights = st.one_of(
    st.lists(h, min_size=0, max_size=20),
    st.lists(st.integers(min_value=0, max_value=2), min_size=0, max_size=20),
    st.builds(lambda x, n: [x] * n, h, st.integers(min_value=0, max_value=8)),
    st.lists(h, min_size=0, max_size=20).map(sorted),
    st.lists(h, min_size=0, max_size=20).map(lambda xs: sorted(xs, reverse=True)),
    st.builds(lambda a, b: sorted(a, reverse=True) + sorted(b), st.lists(h, max_size=10), st.lists(h, max_size=10)),
)


def water_by_levels(arr):
    """Count, level by level, the empty cells that have a wall at least that high on both sides."""
    total = 0
    for level in range(1, max(arr, default=0) + 1):
        for i, x in enumerate(arr):
            if x < level and any(y >= level for y in arr[:i]) and any(y >= level for y in arr[i + 1:]):
                total += 1
    return total


@prop("The result is an int equal to the number of unit water cells bounded by walls on both sides.", arr=heights)
def matches_level_count(f, arr):
    result = f(arr)
    assert isinstance(result, int)
    assert result == water_by_levels(arr)


@prop("Reversing the elevation map does not change the trapped water.", arr=heights)
def reversal_invariant(f, arr):
    assert f(arr) == f(arr[::-1])


@prop("Raising every bar by the same amount does not change the trapped water.",
      arr=heights, c=st.integers(min_value=1, max_value=50))
def shift_invariant(f, arr, c):
    assert f(arr) == f([x + c for x in arr])


@prop("An empty map, or one with fewer than three bars, traps no water.",
      small=st.lists(st.integers(min_value=0, max_value=100), max_size=2))
def too_few_bars_trap_nothing(f, small):
    assert f(small) == 0


@prop("A non-decreasing or non-increasing map traps no water.", arr=heights, descending=st.booleans())
def monotone_traps_nothing(f, arr, descending):
    assert f(sorted(arr, reverse=descending)) == 0


@prop("Between two walls of height h, every inner bar of height <= h is filled up to h.",
      wall=st.integers(min_value=0, max_value=20),
      inner=st.lists(st.integers(min_value=0, max_value=20), max_size=15))
def basin_fills_to_wall(f, wall, inner):
    inner = [min(x, wall) for x in inner]
    assert f([wall] + inner + [wall]) == sum(wall - x for x in inner)

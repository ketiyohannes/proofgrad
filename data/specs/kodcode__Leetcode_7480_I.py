"""Spec for can_rearrange_string: whether the letters of s can be ordered with no two equal neighbours.

Domain: s consists only of 'a' and 'b' (possibly empty).
"""
from itertools import combinations

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_rearrange_string"

CLARIFICATIONS = [
    "Return a bool. The empty string and single-letter strings count as possible (True).",
]

ab_strings = st.one_of(
    st.text(alphabet="ab", max_size=12),
    st.builds(lambda a, b: "a" * a + "b" * b, st.integers(0, 6), st.integers(0, 6)),
)


def possible(s):
    """Try every distinct arrangement (choice of positions for the 'a's)."""
    n, a = len(s), s.count("a")
    for pos in combinations(range(n), a):
        arr = ["b"] * n
        for i in pos:
            arr[i] = "a"
        if all(x != y for x, y in zip(arr, arr[1:])):
            return True
    return n == 0


@prop("The result is True exactly when some ordering of the letters has no two equal adjacent letters.", s=ab_strings)
def matches_definition(f, s):
    assert f(s) == possible(s)


@prop("The result is a bool.", s=ab_strings)
def returns_bool(f, s):
    assert isinstance(f(s), bool)


@prop("The answer depends only on the letter counts, not their order, and is symmetric in 'a' and 'b'.",
      s=st.text(alphabet="ab", max_size=60), data=st.data())
def count_based(f, s, data):
    r = f(s)
    shuffled = "".join(data.draw(st.permutations(list(s))))
    swapped = s.translate(str.maketrans("ab", "ba"))
    assert f(shuffled) == r
    assert f(swapped) == r


@prop("With counts p and q, the result is True exactly when they differ by at most one.",
      p=st.integers(min_value=0, max_value=200), q=st.integers(min_value=0, max_value=200), data=st.data())
def count_rule(f, p, q, data):
    q = data.draw(st.sampled_from([q, p, p + 1, max(p - 1, 0), p + 2]))
    assert f("a" * p + "b" * q) == (abs(p - q) <= 1)


@prop("The empty string and single letters are possible; two or more copies of one letter alone are not.",
      c=st.sampled_from("ab"), n=st.integers(min_value=2, max_value=30))
def small_cases(f, c, n):
    assert f("") is True
    assert f(c) is True
    assert f(c * n) is False

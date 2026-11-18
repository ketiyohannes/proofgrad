"""Spec for max_ones_after_inversion: most '1's reachable by flipping at most one contiguous block of bits.

Domain: n == len(binary_string) >= 1, string of '0'/'1' characters.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "max_ones_after_inversion"

CLARIFICATIONS = [
    "Return the count as an int.",
]

bits = st.one_of(
    st.text(alphabet="01", min_size=1, max_size=24),
    st.builds(lambda c, k: c * k, st.sampled_from("01"), st.integers(1, 20)),
    st.lists(st.sampled_from(["0", "1", "00", "11", "000", "111"]), min_size=1, max_size=10).map("".join),
)


def best_after_flip(s):
    best = s.count("1")
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            flipped = s[:i] + "".join("1" if c == "0" else "0" for c in s[i:j]) + s[j:]
            best = max(best, flipped.count("1"))
    return best


@prop("The result is an int equal to the best count over all single-block flips (or no flip).", s=bits)
def matches_bruteforce(f, s):
    result = f(len(s), s)
    assert isinstance(result, int)
    assert result == best_after_flip(s)


@prop("The result is never below the current number of '1's and never above n.", s=bits)
def bounds(f, s):
    r = f(len(s), s)
    assert s.count("1") <= r <= len(s)


@prop("A string of all '0's becomes all '1's.", n=st.integers(1, 1000))
def all_zero(f, n):
    assert f(n, "0" * n) == n


@prop("A string of all '1's is left unchanged.", n=st.integers(1, 1000))
def all_one(f, n):
    assert f(n, "1" * n) == n


@prop("Reversing the string does not change the answer.", s=bits)
def reverse_invariant(f, s):
    assert f(len(s), s[::-1]) == f(len(s), s)


@prop("With at least one '0', the answer exceeds the current number of '1's.", s=bits.filter(lambda s: "0" in s))
def a_zero_helps(f, s):
    assert f(len(s), s) > s.count("1")

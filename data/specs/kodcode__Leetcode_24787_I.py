"""Spec for rearrange_string: a permutation of s in which equal characters are at least k positions apart, or "".

Domain: lowercase strings (up to 10 characters over a few letters), 0 <= k <= 4.
Interpretation (from the reference and unit tests): "no character repeats within any span of k
positions" means any two equal characters are at least k indices apart; k <= 1 imposes no constraint,
and k == 0 returns s unchanged.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "rearrange_string"

CLARIFICATIONS = [
    "The constraint is defined by k alone: any two equal characters must be at least k positions apart (their indices differ by >= k). For k <= 1 every rearrangement is valid.",
    "If k == 0, return s unchanged.",
    "Return \"\" if no valid rearrangement exists.",
]

texts = st.one_of(
    st.text(alphabet="abc", max_size=10),
    st.text(alphabet="ab", max_size=10),
    st.text(alphabet="abcd", max_size=10),
    st.builds(lambda c, n: c * n, st.sampled_from("az"), st.integers(1, 6)),
)
ks = st.integers(0, 4)


def ok(t, k):
    last = {}
    for i, c in enumerate(t):
        if c in last and i - last[c] < k:
            return False
        last[c] = i
    return True


def feasible(s, k):
    counts = Counter(s)
    n = len(s)

    def go(pos, last):
        if pos == n:
            return True
        for c in sorted(counts):
            if counts[c] and (c not in last or pos - last[c] >= k):
                counts[c] -= 1
                prev = last.get(c)
                last[c] = pos
                if go(pos + 1, last):
                    counts[c] += 1
                    if prev is None:
                        del last[c]
                    else:
                        last[c] = prev
                    return True
                counts[c] += 1
                if prev is None:
                    del last[c]
                else:
                    last[c] = prev
        return False

    return go(0, {})


@prop("The result is a string that is either empty or a rearrangement of s.", s=texts, k=ks)
def is_permutation_or_empty(f, s, k):
    r = f(s, k)
    assert isinstance(r, str)
    assert r == "" or sorted(r) == sorted(s)


@prop("A non-empty result keeps equal characters at least k positions apart.", s=texts, k=ks)
def respects_distance(f, s, k):
    r = f(s, k)
    assert r == "" or ok(r, k)


@prop("The result is empty exactly when no valid rearrangement exists.", s=texts, k=st.integers(1, 4))
def empty_iff_impossible(f, s, k):
    if s:
        assert (f(s, k) == "") == (not feasible(s, k))


@prop("With k == 0 the string is returned unchanged.", s=texts)
def k_zero_identity(f, s):
    assert f(s, 0) == s


@prop("With k == 1 any rearrangement is valid, so a rearrangement of s is returned.", s=st.text(alphabet="abc", min_size=1, max_size=10))
def k_one_always_possible(f, s):
    assert sorted(f(s, 1)) == sorted(s)


@prop("A single repeated letter is impossible for k >= 2, and a single character always works.",
      c=st.sampled_from("az"), n=st.integers(2, 6), k=st.integers(2, 4))
def repeated_letter(f, c, n, k):
    assert f(c * n, k) == ""
    assert f(c, k) == c

"""Spec for can_make_bouquets: is there a day on which m disjoint bouquets of k adjacent bloomed flowers can be picked?

Domain: flowers is a non-empty list of positive integers (bloom days), k >= 1, m >= 1.
On day d a flower has bloomed iff its bloom day <= d; each flower goes into at most one bouquet.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_make_bouquets"

CLARIFICATIONS = [
    "A flower can be picked on day d once its blooming day is <= d, and each flower can be used in at most one bouquet.",
    "flowers is non-empty and k, m >= 1; return a bool.",
]

days = st.one_of(st.integers(1, 5), st.integers(1, 10**9))


@st.composite
def cases(draw):
    flowers = draw(st.lists(days, min_size=1, max_size=15))
    k = draw(st.integers(1, 6))
    m = draw(st.integers(1, 6))
    return flowers, k, m


def max_bouquets_on(flowers, k, day):
    """Best number of disjoint bouquets: split bloomed flowers into maximal adjacent runs."""
    total, run = 0, 0
    for b in flowers + [day + 1]:
        if b <= day:
            run += 1
        else:
            total += run // k
            run = 0
    return total


def possible(flowers, k, m):
    return any(max_bouquets_on(flowers, k, d) >= m for d in set(flowers))


@prop("The result is a bool telling whether some day allows m bouquets.", case=cases())
def matches_definition(f, case):
    flowers, k, m = case
    r = f(flowers, k, m)
    assert isinstance(r, bool)
    assert r == possible(flowers, k, m)


@prop("If m bouquets are possible then fewer bouquets are possible too.", case=cases())
def monotone_in_m(f, case):
    flowers, k, m = case
    if f(flowers, k, m) and m > 1:
        assert f(flowers, k, m - 1) is True


@prop("Needing more flowers than exist (k * m > len(flowers)) is impossible.", case=cases())
def too_few_flowers(f, case):
    flowers, k, m = case
    m = len(flowers) // k + 1
    assert f(flowers, k, m) is False


@prop("Using exactly all flowers (k * m == len(flowers)) is possible once all have bloomed.",
      flowers=st.lists(days, min_size=1, max_size=15), data=st.data())
def exact_fit(f, flowers, data):
    n = len(flowers)
    k = data.draw(st.sampled_from([d for d in range(1, n + 1) if n % d == 0]))
    assert f(flowers, k, n // k) is True


@prop("Single-flower bouquets are possible iff m <= number of flowers.",
      flowers=st.lists(days, min_size=1, max_size=10), m=st.integers(1, 12))
def single_flower_bouquets(f, flowers, m):
    assert f(flowers, 1, m) is (m <= len(flowers))

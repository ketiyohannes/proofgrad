"""Spec for can_measure_exact_volume: whether volume is a sum of capacities, each usable any number of times.

Domain: 1..20 capacities in 1..1000 and a volume in 0..10000; the oracle property uses
smaller values so the definition-following recursive oracle stays fast.
"""
from functools import lru_cache
from math import gcd

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_measure_exact_volume"

CLARIFICATIONS = [
    "Each container capacity may be used any number of times (including zero times), so a volume of 0 is always measurable.",
]


def reachable(capacities, volume):
    caps = tuple(sorted(set(capacities)))

    @lru_cache(maxsize=None)
    def can(v):
        return v == 0 or any(c <= v and can(v - c) for c in caps)

    return can(volume)


small_caps = st.lists(st.integers(min_value=1, max_value=30), min_size=1, max_size=6)
even_caps = st.lists(st.integers(min_value=1, max_value=15).map(lambda x: 2 * x), min_size=1, max_size=5)


@prop("The result is True exactly when the volume is a sum of capacities, each used any number of times.",
      capacities=st.one_of(small_caps, even_caps,
                           st.lists(st.sampled_from([6, 9, 10, 15, 20, 7, 14, 21]), min_size=1, max_size=4)),
      volume=st.integers(min_value=0, max_value=200))
def matches_definition(f, capacities, volume):
    assert f(capacities, volume) is reachable(capacities, volume)


@prop("A volume built as a combination of capacities is measurable.",
      data=st.data(),
      capacities=st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=8))
def constructed_volume_true(f, data, capacities):
    picks = data.draw(st.lists(st.integers(min_value=0, max_value=len(capacities) - 1), max_size=4))
    volume = sum(capacities[i] for i in picks)
    assert f(capacities, volume) is True


@prop("A volume not divisible by the gcd of the capacities is not measurable.",
      capacities=st.lists(st.integers(min_value=1, max_value=200).map(lambda x: 3 * x), min_size=1, max_size=6),
      volume=st.integers(min_value=0, max_value=1000).map(lambda v: 3 * v + 1))
def gcd_obstruction_false(f, capacities, volume):
    assert gcd(*capacities) > 1
    assert f(capacities, volume) is False


@prop("A volume smaller than every capacity is measurable only if it is 0.",
      capacities=st.lists(st.integers(min_value=50, max_value=1000), min_size=1, max_size=20),
      volume=st.integers(min_value=0, max_value=49))
def below_smallest(f, capacities, volume):
    assert f(capacities, volume) is (volume == 0)


@prop("A volume of 0 is always measurable.", capacities=st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=20))
def zero_volume(f, capacities):
    assert f(capacities, 0) is True

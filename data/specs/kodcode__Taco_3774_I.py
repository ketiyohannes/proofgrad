"""Spec for count_duplicate_timestamps: number of distinct timestamps that occur more than once.

Domain: non-empty lists of "HH:MM" strings (00:00 .. 23:59).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_duplicate_timestamps"

CLARIFICATIONS = [
    "Count each repeated timestamp once, however many times it repeats; return an int.",
]

all_times = st.builds(lambda h, m: f"{h:02d}:{m:02d}", st.integers(0, 23), st.integers(0, 59))
few_times = st.sampled_from(["10:00", "10:30", "11:45", "00:00", "23:59"])
stamp_lists = st.one_of(
    st.lists(few_times, min_size=1, max_size=30),
    st.lists(all_times, min_size=1, max_size=30),
    st.lists(all_times, min_size=1, max_size=30, unique=True),
    st.builds(lambda t, k: [t] * k, all_times, st.integers(1, 20)),
)


def repeated_count(stamps):
    return sum(1 for t in set(stamps) if stamps.count(t) > 1)


@prop("The result is an int equal to the number of distinct timestamps occurring at least twice.", stamps=stamp_lists)
def matches_definition(f, stamps):
    result = f(stamps)
    assert isinstance(result, int)
    assert result == repeated_count(stamps)


@prop("All-distinct timestamps give 0.", stamps=st.lists(all_times, min_size=1, max_size=40, unique=True))
def distinct_gives_zero(f, stamps):
    assert f(stamps) == 0


@prop("The same timestamp repeated k >= 2 times counts once.", t=all_times, k=st.integers(2, 50))
def repeated_counts_once(f, t, k):
    assert f([t] * k) == 1


@prop("Reordering the timestamps does not change the answer.", stamps=stamp_lists, data=st.data())
def order_invariant(f, stamps, data):
    shuffled = list(data.draw(st.permutations(stamps)))
    assert f(shuffled) == f(stamps)


@prop("Doubling the whole list makes every distinct timestamp a duplicate.", stamps=stamp_lists)
def doubling(f, stamps):
    assert f(stamps + stamps) == len(set(stamps))

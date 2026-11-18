"""Spec for min_meeting_rooms: minimum rooms so that meetings [end - duration, end) never overlap within a room.

Domain: end_times is a list of integers in 0..100 (possibly empty, duplicates allowed);
duration is a positive integer. Each meeting occupies the half-open interval
[end - duration, end), so a meeting may start exactly when another ends in the same room.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_meeting_rooms"

CLARIFICATIONS = [
    "Each meeting starts at end_time - duration and ends at end_time; duration is a positive integer.",
    "Return 0 for an empty list of end times.",
]

durations = st.integers(min_value=1, max_value=30)
end_lists = st.one_of(
    st.lists(st.integers(min_value=0, max_value=100), max_size=12),
    st.lists(st.integers(min_value=0, max_value=15), max_size=12),
    st.lists(st.sampled_from([10, 20, 30, 40]), max_size=12),
)


def max_overlap(end_times, duration):
    """Largest number of meetings in progress at any single moment (half-open intervals)."""
    starts = [e - duration for e in end_times]
    return max((sum(1 for e in end_times if e - duration <= t < e) for t in starts), default=0)


@prop("The result equals the largest number of meetings in progress at the same moment.",
      end_times=end_lists, duration=durations)
def equals_max_overlap(f, end_times, duration):
    assert f(end_times, duration) == max_overlap(end_times, duration)


@prop("An empty list of meetings needs 0 rooms.", duration=durations)
def empty_needs_zero(f, duration):
    assert f([], duration) == 0


@prop("Meetings whose end times are spaced at least `duration` apart (touching allowed) fit in one room.",
      start=st.integers(min_value=0, max_value=50), duration=durations,
      gaps=st.lists(st.integers(min_value=0, max_value=5), min_size=1, max_size=8), data=st.data())
def back_to_back_one_room(f, start, duration, gaps, data):
    ends = [start + duration]
    for g in gaps[1:]:
        ends.append(ends[-1] + duration + g)
    ends = data.draw(st.permutations(ends))
    assert f(list(ends), duration) == 1


@prop("n meetings with the same end time need n rooms.",
      end=st.integers(min_value=0, max_value=100), n=st.integers(min_value=1, max_value=10), duration=durations)
def identical_meetings(f, end, n, duration):
    assert f([end] * n, duration) == n


@prop("The answer does not depend on the order of the end times.",
      end_times=end_lists, duration=durations, data=st.data())
def order_invariant(f, end_times, duration, data):
    shuffled = data.draw(st.permutations(end_times))
    assert f(list(shuffled), duration) == f(end_times, duration)


@prop("The result is an int between 1 and the number of meetings for a non-empty list.",
      end_times=st.lists(st.integers(min_value=0, max_value=60), min_size=1, max_size=12), duration=durations)
def bounded_int(f, end_times, duration):
    r = f(end_times, duration)
    assert isinstance(r, int) and 1 <= r <= len(end_times)

"""Spec for minMeetingRooms: the minimum number of rooms so that no two meetings sharing a room overlap.

Domain: a list (possibly empty) of (start, end) integer tuples with 0 <= start < end; intervals are half-open,
so a meeting ending at t and another starting at t can share a room.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "minMeetingRooms"

CLARIFICATIONS = ["Return an int; an empty list of meetings needs 0 rooms."]


@st.composite
def meetings(draw, min_size=0):
    hi = draw(st.sampled_from([5, 20, 1000]))
    raw = draw(st.lists(st.tuples(st.integers(0, hi), st.integers(1, max(1, hi // 2))), min_size=min_size, max_size=12))
    return [(s, s + d) for s, d in raw]


def max_overlap(intervals):
    # The busiest moment always coincides with some meeting's start.
    return max((sum(s <= t < e for s, e in intervals) for t, _ in intervals), default=0)


@prop("The result equals the largest number of meetings in progress at the same moment.", ms=meetings())
def matches_max_overlap(f, ms):
    assert f(ms) == max_overlap(ms)


@prop("Meetings that only touch end-to-start (half-open intervals) fit in one room.",
      lengths=st.lists(st.integers(1, 10), min_size=1, max_size=10), start=st.integers(0, 100))
def back_to_back_one_room(f, lengths, start):
    ms, t = [], start
    for d in lengths:
        ms.append((t, t + d))
        t += d
    assert f(ms) == 1


@prop("k copies of the same meeting need k rooms.", s=st.integers(0, 100), d=st.integers(1, 50), k=st.integers(1, 10))
def identical_meetings(f, s, d, k):
    assert f([(s, s + d)] * k) == k


@prop("Shifting all meetings by the same amount or reordering them does not change the answer.", ms=meetings(1), shift=st.integers(0, 1000), data=st.data())
def shift_and_order_invariant(f, ms, shift, data):
    r = f(ms)
    assert isinstance(r, int)
    assert f([(s + shift, e + shift) for s, e in ms]) == r
    assert f(data.draw(st.permutations(ms))) == r


@prop("No meetings need 0 rooms and a single meeting needs 1.", s=st.integers(0, 100), d=st.integers(1, 50))
def empty_and_single(f, s, d):
    assert f([]) == 0
    assert f([(s, s + d)]) == 1

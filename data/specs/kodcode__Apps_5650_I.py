"""Spec for min_meeting_rooms: the maximum number of half-open meetings [start, end) overlapping at once.

Domain: lists of up to 25 (start, end) tuples with 0 <= start < end <= 10000; the empty list is
covered by the unit tests although the constraints say N >= 1.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_meeting_rooms"

CLARIFICATIONS = [
    "The function receives the meetings directly as a list of (start, end) tuples and returns an int.",
    "A meeting that ends at time t does not conflict with a meeting that starts at time t.",
    "Return 0 for an empty list of meetings.",
]


def meeting(max_time):
    return (
        st.tuples(st.integers(0, max_time), st.integers(0, max_time))
        .filter(lambda t: t[0] != t[1])
        .map(lambda t: (min(t), max(t)))
    )


# A small time range forces many shared endpoints; a large one covers the full constraint range.
@st.composite
def identical(draw):
    return [draw(meeting(30))] * draw(st.integers(1, 25))


meetings_small = st.one_of(
    st.lists(meeting(30), min_size=1, max_size=25),
    st.lists(meeting(4), min_size=1, max_size=25),
    identical(),
    st.lists(meeting(30), min_size=1, max_size=1),
    st.lists(meeting(30), min_size=1, max_size=25).map(sorted),
)
meetings_any = st.one_of(meetings_small, st.lists(meeting(10000), min_size=1, max_size=25))


def brute_force(meetings):
    """Peak number of meetings in progress at any instant; a meeting ending at t frees its room for one starting at t."""
    times = {t for m in meetings for t in m}
    return max(sum(1 for s, e in meetings if s <= t < e) for t in times)


@st.composite
def back_to_back(draw):
    """A chain of meetings where each starts exactly when the previous one ends."""
    points = draw(st.lists(st.integers(0, 10000), min_size=2, max_size=20, unique=True))
    points.sort()
    meetings = list(zip(points, points[1:]))
    return draw(st.permutations(meetings))


@st.composite
def common_point(draw):
    """Meetings that all contain a shared instant t, so they pairwise conflict."""
    t = draw(st.integers(1, 9999))
    n = draw(st.integers(1, 20))
    return [(draw(st.integers(0, t)), draw(st.integers(t + 1, 10000))) for _ in range(n)]


@prop("An empty list of meetings needs 0 rooms.", meetings=st.just([]))
def empty_needs_zero(f, meetings):
    assert f(meetings) == 0


@prop("The result equals the peak number of simultaneously running meetings.", meetings=meetings_any)
def matches_peak_overlap(f, meetings):
    assert f(meetings) == brute_force(meetings)


@prop("Meetings that touch only at an endpoint can share one room.", meetings=back_to_back())
def back_to_back_share_room(f, meetings):
    assert f(list(meetings)) == 1


@prop("Meetings that all overlap at one instant each need their own room.", meetings=common_point())
def all_overlapping(f, meetings):
    assert f(meetings) == len(meetings)


@prop("Reordering the meetings does not change the result.", meetings=meetings_small, data=st.data())
def order_invariant(f, meetings, data):
    shuffled = list(data.draw(st.permutations(meetings)))
    assert f(meetings) == f(shuffled)


@prop(
    "Adding one meeting never decreases the result and raises it by at most one.",
    meetings=meetings_small,
    extra=meeting(30),
)
def adding_meeting_monotone(f, meetings, extra):
    before = f(meetings)
    after = f(meetings + [extra])
    assert before <= after <= before + 1

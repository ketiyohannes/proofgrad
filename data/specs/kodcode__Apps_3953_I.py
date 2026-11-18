"""Spec for minConferenceRooms: the maximum number of events in progress at the same moment.

Domain: lists of (start, end) tuples with 0 <= start < end; the empty list (unit tests) gives 0.
Events are half-open [start, end): one ending at t and another starting at t do not overlap.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "minConferenceRooms"

CLARIFICATIONS = [
    "An event that ends at time t and another that starts at time t can use the same room.",
    "Return 0 for an empty list of events.",
]


def max_overlap(events):
    return max((sum(1 for s, e in events if s <= t < e) for t, _ in events), default=0)


def event(max_time):
    return st.tuples(st.integers(0, max_time - 1), st.integers(1, max_time)).filter(lambda p: p[0] < p[1])


event_lists = st.one_of(
    st.lists(event(12), max_size=25),
    st.lists(event(4), max_size=15),
    st.lists(st.integers(0, 10).map(lambda s: (s, s + 1)), max_size=15),
    st.lists(event(10**9), max_size=20),
)


@prop("The result equals the maximum number of events in progress at the same time.", events=event_lists)
def equals_max_overlap(f, events):
    assert f(events) == max_overlap(events)


@prop("Back-to-back events (one ending exactly when the next starts) need only one room.",
      cuts=st.lists(st.integers(0, 10**6), min_size=2, max_size=15, unique=True), seed=st.randoms(use_true_random=False))
def back_to_back_one_room(f, cuts, seed):
    cuts = sorted(cuts)
    events = list(zip(cuts, cuts[1:]))
    seed.shuffle(events)
    assert f(events) == 1


@prop("k copies of the same event need k rooms.", s=st.integers(0, 100), length=st.integers(1, 50), k=st.integers(1, 12))
def identical_events(f, s, length, k):
    assert f([(s, s + length)] * k) == k


@prop("The order of the events does not matter.", events=event_lists, seed=st.randoms(use_true_random=False))
def order_invariant(f, events, seed):
    shuffled = events[:]
    seed.shuffle(shuffled)
    assert f(shuffled) == f(events)


@prop("No events need 0 rooms and a single event needs 1.", ev=event(1000), empty=st.booleans())
def degenerate(f, ev, empty):
    if empty:
        assert f([]) == 0
    else:
        assert f([ev]) == 1

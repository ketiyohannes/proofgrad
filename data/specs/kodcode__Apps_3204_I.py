"""Spec for update_books: net inventory change per "<title> by <author>" key (+1 per return, -1 per borrow).

Domain: log lists whose titles contain no double quote and whose authors have no
leading/trailing spaces; titles and authors use letters, digits, spaces, dots and apostrophes.

The statement's own worked example says a book borrowed once and then returned once
ends at 1, while the reference and unit tests (test_mixed_logs, on the same logs) give 0.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "update_books"

EXCLUDE_REASON = (
    "The statement's example maps a borrow followed by a return of the same book to 1, "
    "but the reference and unit tests return 0 for those exact logs."
)

CLARIFICATIONS = [
    "Every book starts at 0; each borrow subtracts 1 and each return adds 1.",
    "Books whose net count is 0 are still included in the result with value 0.",
]

word = st.text(alphabet="abcXYZ019.'", min_size=1, max_size=6)
name = st.lists(word, min_size=1, max_size=3).map(" ".join)
books = st.lists(st.tuples(name, name), min_size=1, max_size=4, unique=True)


@st.composite
def logs(draw):
    pool = draw(books)
    events = draw(st.lists(st.tuples(st.sampled_from(["borrowed", "returned"]), st.sampled_from(pool)), max_size=20))
    return [f'{action} "{title}" by {author}' for action, (title, author) in events], events


def expected(events):
    inv = {}
    for action, (title, author) in events:
        key = f"{title} by {author}"
        inv[key] = inv.get(key, 0) + (1 if action == "returned" else -1)
    return inv


@prop("The keys are exactly the \"<title> by <author>\" strings of the books in the logs.", case=logs())
def keys_match(f, case):
    lines, events = case
    result = f(lines)
    assert isinstance(result, dict)
    assert set(result) == {f"{t} by {a}" for _, (t, a) in events}


@prop("Each value equals the number of returns minus the number of borrows of that book.", case=logs())
def values_are_net_counts(f, case):
    lines, events = case
    assert f(lines) == expected(events)


@prop("Reordering the log entries does not change the result.", case=logs(), seed=st.randoms(use_true_random=False))
def order_independent(f, case, seed):
    lines, _ = case
    shuffled = lines[:]
    seed.shuffle(shuffled)
    assert f(shuffled) == f(lines)


@prop("An empty log gives an empty dictionary.", dummy=st.just(None))
def empty_logs(f, dummy):
    assert f([]) == {}

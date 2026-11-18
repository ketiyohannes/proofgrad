"""Spec for count_unprocessed_messages: number of messages from sender_id whose 'processed' flag is False.

Domain: messages is a list of dicts with keys 'id', 'sender_id', 'timestamp', 'processed' (bool);
sender_id is a string that may or may not appear in the list.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "count_unprocessed_messages"

CLARIFICATIONS = [
    "Each message is a dict with keys 'id', 'sender_id', 'timestamp' and 'processed' (a bool that is True once the message has been processed).",
    "Return the count as an int (0 when the sender has no unprocessed messages or the list is empty).",
]

senders = st.sampled_from(["A", "B", "C", "D"])


@st.composite
def message_lists(draw):
    n = draw(st.integers(0, 25))
    flag = st.one_of(st.booleans(), st.just(draw(st.booleans())))
    return [
        {"id": i + 1, "sender_id": draw(senders), "timestamp": 1633072800 + 100 * i + draw(st.integers(0, 50)),
         "processed": draw(flag)}
        for i in range(n)
    ]


def count(messages, sender):
    return len([m for m in messages if m["sender_id"] == sender and m["processed"] is False])


@prop("The result is an int equal to the number of unprocessed messages from the sender.", msgs=message_lists(), sender=senders)
def matches_definition(f, msgs, sender):
    r = f(msgs, sender)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == count(msgs, sender)


@prop("Processed messages are never counted.", msgs=message_lists(), sender=senders)
def processed_ignored(f, msgs, sender):
    for m in msgs:
        m["processed"] = True
    assert f(msgs, sender) == 0


@prop("Messages from other senders are never counted.", msgs=message_lists(), sender=senders)
def other_senders_ignored(f, msgs, sender):
    others = [m for m in msgs if m["sender_id"] != sender]
    assert f(others, sender) == 0


@prop("Counts over all senders add up to the total number of unprocessed messages.", msgs=message_lists())
def counts_partition(f, msgs):
    assert sum(f(msgs, s) for s in ["A", "B", "C", "D"]) == sum(1 for m in msgs if not m["processed"])


@prop("Message order does not affect the count.", msgs=message_lists(), sender=senders, data=st.data())
def order_invariant(f, msgs, sender, data):
    shuffled = data.draw(st.permutations(msgs))
    assert f(list(shuffled), sender) == f(msgs, sender)


@prop("An empty message list gives 0.", sender=senders)
def empty_list(f, sender):
    assert f([], sender) == 0

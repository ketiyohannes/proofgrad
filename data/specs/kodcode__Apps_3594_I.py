"""Spec for group_and_sort_orders: output lines [count, sender, "receiver:items", ...] grouped by sender.

Domain: n == len(orders) (0..30 orders); senders, receivers and items are short lowercase
strings; each order has 1..4 items; items are unique across all orders.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "group_and_sort_orders"

CLARIFICATIONS = [
    "Return the output lines as a list of strings instead of printing them; the first element is the number of unique senders as a string.",
    "Sender sections appear in alphabetical order of the sender's name.",
    "Orders from the same sender with the same receiver keep their input order.",
    "With no orders, return [\"0\"].",
]

names = st.sampled_from(["anna", "bob", "carol", "dave", "al", "b", "zed", "bobby"])


@st.composite
def order_lists(draw):
    k = draw(st.integers(min_value=0, max_value=30))
    senders = draw(st.lists(names, min_size=1, max_size=4, unique=True))
    receivers = draw(st.lists(names, min_size=1, max_size=4, unique=True))
    counter = 0
    orders = []
    for _ in range(k):
        s = draw(st.sampled_from(senders))
        r = draw(st.sampled_from(receivers))
        m = draw(st.integers(min_value=1, max_value=4))
        items = []
        for _ in range(m):
            items.append("item" + "".join(chr(ord("a") + int(d)) for d in str(counter)))
            counter += 1
        orders.append((s, r, items))
    return [f"{s}:{r}:{','.join(items)}" for s, r, items in orders], orders


def sections(lines, senders):
    """Split output lines (after the count) into {sender: [order lines]} using known sender names."""
    result, current, order = {}, None, []
    for line in lines[1:]:
        if ":" not in line:
            current = line
            order.append(line)
            result[current] = []
        else:
            result[current].append(line)
    return order, result


@prop("The result is a list whose first element is the number of unique senders, as a string.", case=order_lists())
def count_line(f, case):
    lines, orders = case
    result = f(len(lines), lines)
    assert isinstance(result, list)
    assert result[0] == str(len({s for s, _, _ in orders}))


@prop("The result has one header line per sender plus one line per order.", case=order_lists())
def line_count(f, case):
    lines, orders = case
    result = f(len(lines), lines)
    assert len(result) == 1 + len({s for s, _, _ in orders}) + len(orders)


@prop("Sender headers appear once each, in alphabetical order.", case=order_lists())
def senders_sorted(f, case):
    lines, orders = case
    headers, _ = sections(f(len(lines), lines), None)
    assert headers == sorted({s for s, _, _ in orders})


@prop("Each sender's section holds exactly that sender's orders, as \"receiver:item1,item2,...\" lines.", case=order_lists())
def sections_hold_right_orders(f, case):
    lines, orders = case
    _, groups = sections(f(len(lines), lines), None)
    for sender in {s for s, _, _ in orders}:
        expected = sorted(f"{r}:{','.join(items)}" for s, r, items in orders if s == sender)
        assert sorted(groups[sender]) == expected


@prop("Within each sender, orders are sorted by receiver, ties keeping input order.", case=order_lists())
def receivers_sorted_stable(f, case):
    lines, orders = case
    _, groups = sections(f(len(lines), lines), None)
    for sender in {s for s, _, _ in orders}:
        mine = [(r, items) for s, r, items in orders if s == sender]
        expected = [f"{r}:{','.join(items)}" for r, items in sorted(mine, key=lambda x: x[0])]
        assert groups[sender] == expected


@prop("No orders give [\"0\"]; a single order gives [\"1\", sender, line].",
      single=st.tuples(names, names, st.lists(st.sampled_from(["x", "yy", "zzz"]), min_size=1, max_size=3, unique=True)),
      empty=st.booleans())
def degenerate(f, single, empty):
    if empty:
        assert f(0, []) == ["0"]
    else:
        s, r, items = single
        line = f"{s}:{r}:{','.join(items)}"
        assert f(1, [line]) == ["1", s, f"{r}:{','.join(items)}"]

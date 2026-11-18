"""Spec for min_steps_to_one: fewest operations (subtract 1, halve if even, divide by 3 if divisible) to reach 1 from m.

Domain: 1 <= m <= 1000.
"""
from collections import deque

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "min_steps_to_one"

CLARIFICATIONS = ["Return an int; m = 1 needs 0 steps."]


def bfs(m):
    dist = {m: 0}
    queue = deque([m])
    while queue:
        x = queue.popleft()
        if x == 1:
            return dist[x]
        nexts = [x - 1]
        if x % 2 == 0:
            nexts.append(x // 2)
        if x % 3 == 0:
            nexts.append(x // 3)
        for y in nexts:
            if y >= 1 and y not in dist:
                dist[y] = dist[x] + 1
                queue.append(y)
    raise AssertionError("unreachable")


m_values = st.one_of(st.integers(1, 1000), st.integers(1, 30))


@prop("The result equals the shortest number of allowed moves, found by breadth-first search over all reachable numbers.", m=m_values)
def matches_bfs(f, m):
    assert f(m) == bfs(m)


@prop("One move never helps by more than one step: f(m) <= f(m - 1) + 1, f(m) <= f(m / 2) + 1 and f(m) <= f(m / 3) + 1 where allowed.",
      m=st.integers(2, 1000))
def one_move_relations(f, m):
    r = f(m)
    assert r <= f(m - 1) + 1
    if m % 2 == 0:
        assert r <= f(m // 2) + 1
    if m % 3 == 0:
        assert r <= f(m // 3) + 1


@prop("No move shrinks a number by more than a factor of 3, so 3 ** f(m) >= m.", m=st.integers(1, 1000))
def lower_bound(f, m):
    r = f(m)
    assert isinstance(r, int)
    assert 3 ** r >= m


@prop("Small cases: f(1) = 0, f(2) = f(3) = 1, and powers of 3 need exactly their exponent.", e=st.integers(0, 6))
def small_cases(f, e):
    assert f(1) == 0
    assert f(2) == 1 and f(3) == 1
    assert f(3 ** e) == e

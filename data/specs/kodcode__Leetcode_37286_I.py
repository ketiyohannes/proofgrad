"""Spec for numRescueBoats: minimum boats, each holding at most two people with total weight <= limit.

Domain: limit is a positive integer and every weight is an integer in 1..limit
(so everyone fits in a boat alone); people may be empty.
"""
from functools import lru_cache

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "numRescueBoats"

CLARIFICATIONS = [
    "Every person's weight is at most limit. Return 0 when there are no people.",
]


@st.composite
def case(draw, max_n=8):
    limit = draw(st.integers(min_value=1, max_value=20))
    w = st.one_of(st.integers(min_value=1, max_value=limit),
                  st.sampled_from(sorted({1, max(1, limit // 2), (limit + 1) // 2, limit})))
    people = draw(st.lists(w, max_size=max_n))
    return people, limit


def oracle(people, limit):
    @lru_cache(maxsize=None)
    def best(rest):
        if not rest:
            return 0
        first, others = rest[0], rest[1:]
        options = [1 + best(others)]
        for i, w in enumerate(others):
            if first + w <= limit:
                options.append(1 + best(others[:i] + others[i + 1:]))
        return min(options)

    return best(tuple(sorted(people)))


@prop("The result equals the true minimum number of boats.", c=case())
def is_minimum(f, c):
    people, limit = c
    assert f(people, limit) == oracle(people, limit)


@prop("The result is at least ceil(n / 2) and at most n.", c=case(max_n=30))
def within_bounds(f, c):
    people, limit = c
    r = f(people, limit)
    assert isinstance(r, int)
    assert (len(people) + 1) // 2 <= r <= len(people)


@prop("When any two people fit together, exactly ceil(n / 2) boats are needed.",
      people=st.lists(st.integers(min_value=1, max_value=50), max_size=30), extra=st.integers(min_value=0, max_value=10))
def everyone_pairs(f, people, extra):
    limit = 2 * max(people, default=1) + extra
    assert f(people, limit) == (len(people) + 1) // 2


@prop("When no two people fit together, everyone needs their own boat.",
      limit=st.integers(min_value=1, max_value=40), data=st.data())
def nobody_pairs(f, limit, data):
    people = data.draw(st.lists(st.integers(min_value=limit // 2 + 1, max_value=limit), max_size=15))
    assert f(people, limit) == len(people)


@prop("No people need 0 boats and one person needs 1 boat.",
      limit=st.integers(min_value=1, max_value=100), data=st.data())
def tiny_inputs(f, limit, data):
    w = data.draw(st.integers(min_value=1, max_value=limit))
    assert f([], limit) == 0
    assert f([w], limit) == 1


@prop("The answer does not depend on the order of the people.", c=case(max_n=15), data=st.data())
def order_invariant(f, c, data):
    people, limit = c
    assert f(list(data.draw(st.permutations(people))), limit) == f(people, limit)

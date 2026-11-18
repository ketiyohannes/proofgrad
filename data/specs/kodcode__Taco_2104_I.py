"""Spec for highest_possible_power: the best a single wizard can end with when others may donate their original power to him.

Domain: n == len(powers) >= 1, powers are non-negative integers (the statement says >= 1; the unit
tests also use 0 and values above 10^9). Negative powers are not generated: the statement excludes
them and the natural reading ("can choose to donate") would disagree with a plain total for them.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "highest_possible_power"

CLARIFICATIONS = [
    "Return the answer as an int.",
]

power_lists = st.one_of(
    st.lists(st.integers(1, 10**9), min_size=1, max_size=30),
    st.lists(st.integers(0, 3), min_size=1, max_size=30),
    st.builds(lambda v, k: [v] * k, st.integers(0, 10**9), st.integers(1, 20)),
    st.lists(st.integers(10**9, 3 * 10**9), min_size=1, max_size=5),
)


def best_receiver_total(powers):
    """For each possible receiver, everyone else chooses whether to donate; donating never hurts for non-negative power."""
    best = None
    for r, own in enumerate(powers):
        total = own + sum(max(p, 0) for j, p in enumerate(powers) if j != r)
        best = total if best is None else max(best, total)
    return best


@prop("The result is an int equal to the best total any single wizard can collect.", powers=power_lists)
def matches_definition(f, powers):
    result = f(len(powers), powers)
    assert isinstance(result, int) and not isinstance(result, bool)
    assert result == best_receiver_total(powers)


@prop("The result is at least the largest initial power.", powers=power_lists)
def at_least_max(f, powers):
    assert f(len(powers), powers) >= max(powers)


@prop("Reordering the wizards does not change the answer.", powers=power_lists, data=st.data())
def order_invariant(f, powers, data):
    shuffled = data.draw(st.permutations(powers))
    assert f(len(powers), powers) == f(len(shuffled), list(shuffled))


@prop("Adding one more wizard with power p increases the answer by exactly p.", powers=power_lists, p=st.integers(0, 10**9))
def adding_wizard_adds_power(f, powers, p):
    assert f(len(powers) + 1, powers + [p]) == f(len(powers), powers) + p


@prop("A single wizard keeps his own power.", p=st.integers(0, 3 * 10**9))
def single_wizard(f, p):
    assert f(1, [p]) == p

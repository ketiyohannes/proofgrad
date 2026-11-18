"""Spec for change: number of unordered combinations (multisets) of coins summing to amount.

Domain: amount >= 0; coins is a non-empty list of distinct positive integers. amount == 0 gives 1
(the empty combination).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "change"

CLARIFICATIONS = [
    "Return 1 when amount is 0 (using no coins is one combination).",
    "Coin denominations are distinct positive integers.",
]

coin_lists = st.lists(st.integers(1, 12), unique=True, min_size=1, max_size=5)
amounts = st.integers(0, 30)


def ways(amount, coins):
    """Enumerate how many of each coin to use, one denomination at a time."""
    if not coins:
        return 1 if amount == 0 else 0
    c, rest = coins[0], coins[1:]
    return sum(ways(amount - c * k, rest) for k in range(amount // c + 1))


@prop("The result is an int equal to the number of unordered coin combinations.", amount=amounts, coins=coin_lists)
def matches_definition(f, amount, coins):
    r = f(amount, coins)
    assert isinstance(r, int) and not isinstance(r, bool)
    assert r == ways(amount, coins)


@prop("The order of the coin list does not change the count.", amount=amounts, coins=coin_lists, data=st.data())
def coin_order_invariant(f, amount, coins, data):
    assert f(amount, list(data.draw(st.permutations(coins)))) == f(amount, coins)


@prop("Adding a new denomination never decreases the count.", amount=amounts, coins=coin_lists, extra=st.integers(1, 15))
def adding_coin_monotone(f, amount, coins, extra):
    if extra not in coins:
        assert f(amount, coins + [extra]) >= f(amount, coins)


@prop("With a single coin the count is 1 if it divides the amount and 0 otherwise.", amount=amounts, c=st.integers(1, 12))
def single_coin(f, amount, c):
    assert f(amount, [c]) == (1 if amount % c == 0 else 0)


@prop("Amount 0 gives 1; with coins 1 and 2 the count is amount // 2 + 1.", coins=coin_lists, amount=amounts)
def small_cases(f, coins, amount):
    assert f(0, coins) == 1
    assert f(amount, [1, 2]) == amount // 2 + 1
    assert f(amount, [2, 1]) == amount // 2 + 1

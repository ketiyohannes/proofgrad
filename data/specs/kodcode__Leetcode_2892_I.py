"""Spec for can_travel: whether destinationCity is reachable from startCity over undirected flight routes.

Domain: routes is a list of [cityA, cityB] pairs of city-name strings (possibly empty, possibly with
cycles, self-loops and duplicate routes); start and destination may or may not appear in any route.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "can_travel"

CLARIFICATIONS = [
    "Every route can be flown in both directions.",
    "A city that appears in no route can only reach itself.",
    "Return a bool (True or False).",
]

CITIES = list("ABCDEFGH")
city = st.sampled_from(CITIES)
routes_st = st.lists(st.lists(city, min_size=2, max_size=2), max_size=10)


def reachable(routes, start):
    seen = {start}
    changed = True
    while changed:
        changed = False
        for a, b in routes:
            if (a in seen) != (b in seen):
                seen |= {a, b}
                changed = True
    return seen


@prop("The result is True exactly when a chain of routes connects start to destination.",
      routes=routes_st, start=city, dest=city)
def matches_reachability(f, routes, start, dest):
    r = f(routes, start, dest)
    assert isinstance(r, bool)
    assert r == (dest in reachable(routes, start))


@prop("Reachability is symmetric: swapping start and destination gives the same answer.",
      routes=routes_st, start=city, dest=city)
def symmetric(f, routes, start, dest):
    assert f(routes, start, dest) == f(routes, dest, start)


@prop("A city can always reach itself, even if it appears in no route.", routes=routes_st, start=st.sampled_from(CITIES + ["Z"]))
def same_city_true(f, routes, start):
    assert f(routes, start, start) is True


@prop("Along a chain of routes (listed in any order and direction) the two ends are connected.",
      data=st.data(), chain=st.lists(city, min_size=2, max_size=8, unique=True))
def chain_connected(f, data, chain):
    legs = [[a, b] if data.draw(st.booleans()) else [b, a] for a, b in zip(chain, chain[1:])]
    legs = data.draw(st.permutations(legs))
    assert f(list(legs), chain[0], chain[-1]) is True


@prop("Cities in different components cannot reach each other.",
      left=routes_st.map(lambda rs: [[a.lower(), b.lower()] for a, b in rs]), right=routes_st, a=city, b=city)
def components_separate(f, left, right, a, b):
    routes = left + right + [[a.lower(), a.lower()]]
    assert f(routes, a.lower(), b) is False
    assert f(routes, "Z", a) is False

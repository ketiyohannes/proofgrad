"""Spec for find_order: a topological order of the projects, or [] if the dependencies contain a cycle.

Domain: projects is a list of unique integer IDs; every dependency [a, b] refers to IDs in projects
(duplicate dependencies and self-dependencies may occur; a self-dependency is a cycle).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_order"

CLARIFICATIONS = [
    "Every ID in dependencies appears in projects; the returned order must contain every project exactly once.",
    "A project that depends on itself, or any dependency cycle, means no valid order exists, so return [].",
]


@st.composite
def dag_case(draw):
    """Projects with dependencies that always admit a valid order."""
    ids = draw(st.lists(st.integers(-50, 50), unique=True, min_size=1, max_size=9))
    hidden = draw(st.permutations(ids))
    n = len(hidden)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    density = draw(st.sampled_from([0.0, 0.2, 0.5, 1.0]))
    chosen = [p for p in pairs if draw(st.floats(0, 1)) < density] if pairs else []
    deps = [[hidden[i], hidden[j]] for i, j in chosen]
    if deps and draw(st.booleans()):
        deps.append(list(draw(st.sampled_from(deps))))
    deps = draw(st.permutations(deps))
    return list(ids), [list(d) for d in deps]


@st.composite
def cyclic_case(draw):
    """Projects whose dependencies definitely contain a cycle."""
    ids, deps = draw(dag_case())
    cycle = draw(st.lists(st.sampled_from(ids), unique=True, min_size=1, max_size=len(ids)))
    for k in range(len(cycle)):
        deps.append([cycle[k], cycle[(k + 1) % len(cycle)]])
    deps = draw(st.permutations(deps))
    return ids, [list(d) for d in deps]


def has_cycle(ids, deps):
    adj = {p: set() for p in ids}
    for a, b in deps:
        adj[a].add(b)
    for start in ids:
        seen, stack = set(), list(adj[start])
        while stack:
            x = stack.pop()
            if x == start:
                return True
            if x not in seen:
                seen.add(x)
                stack.extend(adj[x])
    return False


any_case = st.one_of(dag_case(), cyclic_case())


@prop("For acyclic dependencies the result is a list containing every project exactly once.", case=dag_case())
def acyclic_is_permutation(f, case):
    ids, deps = case
    r = f(ids, deps)
    assert isinstance(r, list)
    assert sorted(r) == sorted(ids)


@prop("For acyclic dependencies every dependency [a, b] has a placed before b.", case=dag_case())
def acyclic_respects_dependencies(f, case):
    ids, deps = case
    r = f(ids, deps)
    pos = {p: i for i, p in enumerate(r)}
    assert all(a in pos and b in pos and pos[a] < pos[b] for a, b in deps)


@prop("When the dependencies contain a cycle the result is an empty list.", case=cyclic_case())
def cycle_gives_empty(f, case):
    ids, deps = case
    assert f(ids, deps) == []


@prop("The result is empty exactly when the dependencies contain a cycle.", case=any_case)
def empty_iff_cycle(f, case):
    ids, deps = case
    assert (f(ids, deps) == []) == has_cycle(ids, deps)


@prop("With no dependencies every project is returned once; a single project returns [project].",
      ids=st.lists(st.integers(-50, 50), unique=True, min_size=1, max_size=10))
def no_dependencies(f, ids):
    r = f(ids, [])
    assert sorted(r) == sorted(ids)
    assert f([ids[0]], []) == [ids[0]]

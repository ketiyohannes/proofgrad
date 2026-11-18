"""Spec for reorganize_boxes: a rearrangement of the boxes with no two adjacent equal weights.

Domain: non-empty lists of weights in 1..10000 for which a valid arrangement exists, i.e.
the most frequent weight appears at most (len - its count) + 1 times. Any valid arrangement is accepted.
"""
from collections import Counter

from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "reorganize_boxes"

CLARIFICATIONS = [
    "Inputs always admit a valid arrangement; return it as a list containing every box exactly once.",
]


def feasible(boxes):
    top = max(Counter(boxes).values())
    return top <= len(boxes) - top + 1


@st.composite
def boxes_strategy(draw):
    kind = draw(st.sampled_from(["random", "few", "tight"]))
    if kind == "random":
        boxes = draw(st.lists(st.integers(1, 10000), min_size=1, max_size=40))
    elif kind == "few":
        boxes = draw(st.lists(st.integers(1, 4), min_size=1, max_size=40))
    else:
        others = draw(st.lists(st.integers(2, 6), min_size=0, max_size=20))
        boxes = others + [1] * (len(others) + 1)
        boxes = list(draw(st.permutations(boxes)))
    if not feasible(boxes):
        counts = Counter(boxes)
        top_weight, top = counts.most_common(1)[0]
        excess = top - (len(boxes) - top + 1)
        for _ in range(excess):
            boxes.remove(top_weight)
    return boxes


@prop("The result is a list containing exactly the input boxes (a permutation).", boxes=boxes_strategy())
def is_permutation(f, boxes):
    result = f(boxes)
    assert isinstance(result, list)
    assert Counter(result) == Counter(boxes)


@prop("No two adjacent boxes in the result have the same weight.", boxes=boxes_strategy())
def no_adjacent_equal(f, boxes):
    result = f(boxes)
    assert all(result[i] != result[i + 1] for i in range(len(result) - 1))


@prop("Tight inputs (one weight filling every other slot) are fully arranged.",
      others=st.lists(st.integers(2, 9), max_size=15), seed=st.randoms(use_true_random=False))
def tight_case(f, others, seed):
    boxes = others + [1] * (len(others) + 1)
    seed.shuffle(boxes)
    result = f(boxes)
    assert Counter(result) == Counter(boxes)
    assert result[0::2] == [1] * (len(others) + 1)


@prop("A single box is returned as is.", w=st.integers(1, 10000))
def single_box(f, w):
    assert f([w]) == [w]

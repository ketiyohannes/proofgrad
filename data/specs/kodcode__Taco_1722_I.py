"""Spec for do_rectangles_overlap: "Overlap" iff the two axis-aligned rectangles intersect with positive area.

Domain: non-degenerate rectangles (x1 < x2, y1 < y2, a1 < a2, b1 < b2) with integer coordinates.
The reference (and unit tests) report rectangles that touch only along an edge or at a corner as
"No Overlap", while the statement defines overlap as sharing at least one point.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "do_rectangles_overlap"

EXCLUDE_REASON = (
    "The statement defines overlap as sharing at least one point, but the reference and unit tests "
    "return 'No Overlap' for rectangles that touch at an edge or corner, e.g. (1,1,2,2) and (2,2,3,3)."
)

CLARIFICATIONS = [
    "Rectangles that only touch along an edge or at a corner do not overlap; return \"No Overlap\" for them.",
]


@st.composite
def rect(draw, lo=-6, hi=6):
    x1 = draw(st.integers(lo, hi - 1))
    x2 = draw(st.integers(x1 + 1, hi))
    y1 = draw(st.integers(lo, hi - 1))
    y2 = draw(st.integers(y1 + 1, hi))
    return x1, y1, x2, y2


@st.composite
def wide_rect(draw):
    x1 = draw(st.integers(-10**9, 10**9 - 1))
    x2 = draw(st.integers(x1 + 1, 10**9))
    y1 = draw(st.integers(-10**9, 10**9 - 1))
    y2 = draw(st.integers(y1 + 1, 10**9))
    return x1, y1, x2, y2


pairs = st.one_of(st.tuples(rect(), rect()), st.tuples(rect(-2, 2), rect(-2, 2)), st.tuples(wide_rect(), wide_rect()))


def overlaps(r, s):
    """Positive-area intersection: the open interiors share a point."""
    x1, y1, x2, y2 = r
    a1, b1, a2, b2 = s
    return max(x1, a1) < min(x2, a2) and max(y1, b1) < min(y2, b2)


@prop("The result is the string 'Overlap' or 'No Overlap' matching whether the interiors intersect.", rs=pairs)
def matches_definition(f, rs):
    r, s = rs
    assert f(*r, *s) == ("Overlap" if overlaps(r, s) else "No Overlap")


@prop("Swapping the two rectangles does not change the answer.", rs=pairs)
def symmetric(f, rs):
    r, s = rs
    assert f(*r, *s) == f(*s, *r)


@prop("A rectangle overlaps itself and any rectangle containing it.", r=rect(), grow=st.integers(0, 3))
def overlaps_container(f, r, grow):
    x1, y1, x2, y2 = r
    assert f(*r, *r) == "Overlap"
    assert f(*r, x1 - grow, y1 - grow, x2 + grow, y2 + grow) == "Overlap"


@prop("Rectangles that only touch along an edge or a corner do not overlap.", r=rect(), w=st.integers(1, 4),
      side=st.sampled_from(["right", "top", "corner", "left"]))
def touching_is_not_overlap(f, r, w, side):
    x1, y1, x2, y2 = r
    if side == "right":
        s = (x2, y1, x2 + w, y2)
    elif side == "top":
        s = (x1, y2, x2, y2 + w)
    elif side == "left":
        s = (x1 - w, y1, x1, y2)
    else:
        s = (x2, y2, x2 + w, y2 + w)
    assert f(*r, *s) == "No Overlap"

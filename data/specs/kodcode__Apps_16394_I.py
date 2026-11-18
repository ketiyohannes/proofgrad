"""Spec for find_best_rated_product_in_category: ID of the highest-rated product in a category (first on ties).

Domain: 1..10 well-formed records "ID:Category:Price:Stock:Rating" with alphanumeric IDs, alphabetic
categories, prices like "12.50", integer stock and ratings in 1.0..5.0 written with one decimal.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "find_best_rated_product_in_category"

CLARIFICATIONS = [
    "Instead of reading input, the function receives the category string and a list of record strings, and returns the ProductID string (or \"No products found\") instead of printing it.",
    "Ratings are compared numerically; categories are matched exactly.",
]

CATEGORIES = ["Electronics", "Home", "Furniture", "Toys", "Books"]
ratings = st.one_of(st.sampled_from(["4.5", "4.7", "3.0"]), st.integers(10, 50).map(lambda r: f"{r // 10}.{r % 10}"))


@st.composite
def records(draw, min_size=1):
    n = draw(st.integers(min_size, 10))
    cats = draw(st.lists(st.sampled_from(CATEGORIES[:draw(st.integers(1, 5))]), min_size=n, max_size=n))
    out = []
    for i, c in enumerate(cats):
        pid = draw(st.sampled_from("ABCDEFGH")) + str(100 + i)
        price = f"{draw(st.integers(1, 99999)) / 100:.2f}"
        stock = draw(st.integers(0, 500))
        out.append(f"{pid}:{c}:{price}:{stock}:{draw(ratings)}")
    return out


def parse(rec):
    pid, cat, _price, _stock, rating = rec.split(":")
    return pid, cat, float(rating)


def expected(category, recs):
    best = None
    for rec in recs:
        pid, cat, r = parse(rec)
        if cat == category and (best is None or r > best[1]):
            best = (pid, r)
    return best[0] if best else "No products found"


@prop("The result is a string: a ProductID of the given category or \"No products found\".",
      recs=records(), category=st.sampled_from(CATEGORIES))
def returns_valid_id(f, recs, category):
    r = f(category, recs)
    assert isinstance(r, str)
    ids = [parse(x)[0] for x in recs if parse(x)[1] == category]
    assert r in ids or (r == "No products found" and not ids)


@prop("The returned product has the highest rating in its category.", recs=records(), category=st.sampled_from(CATEGORIES))
def highest_rating(f, recs, category):
    in_cat = [parse(x) for x in recs if parse(x)[1] == category]
    r = f(category, recs)
    if in_cat:
        rating = next(rt for pid, _c, rt in in_cat if pid == r)
        assert rating == max(rt for _p, _c, rt in in_cat)


@prop("Among equally top-rated products, the one appearing first is returned.", recs=records(), category=st.sampled_from(CATEGORIES))
def first_on_ties(f, recs, category):
    assert f(category, recs) == expected(category, recs)


@prop("A category with no products gives \"No products found\".", recs=records())
def missing_category(f, recs):
    assert f("Garden", recs) == "No products found"


@prop("Products in other categories are ignored, even if rated higher.", recs=records(), category=st.sampled_from(CATEGORIES))
def other_categories_ignored(f, recs, category):
    other = "Zeta" if category != "Zeta" else "Eta"
    extra = [f"Z{i}:{other}:1.00:1:5.0" for i in range(2)]
    assert f(category, extra + recs + extra) == expected(category, recs)


@prop("All products in the category tied gives the first of them.",
      n=st.integers(1, 6), rating=ratings, cat=st.sampled_from(CATEGORIES))
def all_tied(f, n, rating, cat):
    recs = [f"P{i}:{cat}:9.99:3:{rating}" for i in range(n)]
    assert f(cat, recs) == "P0"

"""Spec for product_except_self: element i of the result is the product of all elements except index i.

Domain: lists of integers including zeros (one or several), negatives, a single element
(gives [1]) and the empty list (gives []).
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "product_except_self"

CLARIFICATIONS = [
    "For a single-element list return [1]; for an empty list return [].",
]


def product(xs):
    p = 1
    for x in xs:
        p *= x
    return p


int_lists = st.one_of(
    st.lists(st.integers(-10, 10), max_size=12),
    st.lists(st.integers(-3, 3), max_size=10),
    st.lists(st.sampled_from([0, 1, 2, -1]), max_size=8),
    st.lists(st.integers(-1000, 1000), min_size=1, max_size=6),
)


@prop("The result is a list with the same length as the input.", nums=int_lists)
def same_length(f, nums):
    result = f(nums)
    assert isinstance(result, list)
    assert len(result) == len(nums)


@prop("Each element is the product of all other elements.", nums=int_lists)
def exact_products(f, nums):
    assert f(nums) == [product(nums[:i] + nums[i + 1:]) for i in range(len(nums))]


@prop("With exactly one zero, only the zero's position is nonzero (when the other elements are nonzero).",
      others=st.lists(st.integers(-6, 6).filter(lambda x: x != 0), max_size=8), data=st.data())
def one_zero(f, others, data):
    pos = data.draw(st.integers(0, len(others)))
    nums = others[:pos] + [0] + others[pos:]
    result = f(nums)
    assert result[pos] == product(others)
    assert all(v == 0 for i, v in enumerate(result) if i != pos)


@prop("With two or more zeros, every entry is 0.",
      nums=st.lists(st.integers(-5, 5), max_size=8).map(lambda xs: xs + [0, 0]), seed=st.randoms(use_true_random=False))
def many_zeros(f, nums, seed):
    seed.shuffle(nums)
    assert f(nums) == [0] * len(nums)


@prop("A single-element list gives [1] and the empty list gives [].", x=st.integers(-100, 100), empty=st.booleans())
def degenerate(f, x, empty):
    if empty:
        assert f([]) == []
    else:
        assert f([x]) == [1]

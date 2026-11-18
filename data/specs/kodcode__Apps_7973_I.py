"""Spec for is_balanced: True iff the round and square brackets are matched and properly nested.

Domain: strings over ( ) [ ]; per the unit tests, any other character (e.g. { }) is ignored.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "is_balanced"

CLARIFICATIONS = [
    "Any character other than (, ), [ and ] (for example { or }) is ignored.",
    "The empty string is balanced.",
    "Return a bool.",
]


def reduce_oracle(s):
    s = "".join(c for c in s if c in "()[]")
    while True:
        t = s.replace("()", "").replace("[]", "")
        if t == s:
            return s == ""
        s = t


balanced = st.recursive(
    st.just(""),
    lambda inner: st.one_of(
        st.builds(lambda x: "(" + x + ")", inner),
        st.builds(lambda x: "[" + x + "]", inner),
        st.builds(lambda a, b: a + b, inner, inner),
    ),
    max_leaves=12,
)

brackets = st.one_of(
    st.text(alphabet="()[]", max_size=14),
    st.text(alphabet="()", max_size=14),
    balanced,
    # Near-balanced: a balanced string with one character changed, removed or added.
    st.builds(lambda s, i, c, op: (s[:i] + c + s[i + 1:]) if op == 0 else (s[:i] + s[i + 1:]) if op == 1 else (s[:i] + c + s[i:]),
              balanced, st.integers(0, 30), st.sampled_from("()[]"), st.integers(0, 2)),
)


@prop("The result agrees with repeatedly deleting adjacent '()' and '[]' pairs until nothing is left.", s=brackets)
def matches_reduction_oracle(f, s):
    assert f(s) == reduce_oracle(s)


@prop("Properly nested strings built from matched pairs are balanced.", s=balanced)
def balanced_is_true(f, s):
    assert f(s) is True


@prop("Crossed or mismatched pairs such as '([)]' or '(]' are not balanced.", pre=balanced, mid=balanced, post=balanced,
      kind=st.sampled_from(["([)]", "[(])", "(]", "[)"]))
def mismatched_is_false(f, pre, mid, post, kind):
    s = pre + kind[: len(kind) // 2] + mid + kind[len(kind) // 2:] + post
    assert f(s) is False


@prop("Unmatched opening or closing brackets make the expression unbalanced.", s=balanced, c=st.sampled_from("()[]"), at_end=st.booleans())
def extra_bracket_is_false(f, s, c, at_end):
    assert f(s + c if at_end else c + s) is False


@prop("Characters other than brackets are ignored.", s=brackets, data=st.data())
def other_chars_ignored(f, s, data):
    chars = list(s)
    for _ in range(data.draw(st.integers(1, 4))):
        chars.insert(data.draw(st.integers(0, len(chars))), data.draw(st.sampled_from("{}a1 +")))
    assert f("".join(chars)) == reduce_oracle(s)


@prop("The empty string is balanced and the result is a bool.", s=brackets)
def empty_and_type(f, s):
    assert f("") is True
    assert isinstance(f(s), bool)

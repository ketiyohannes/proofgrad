"""Spec for evaluate_rpn: evaluate a Reverse Polish Notation token list, or raise ValueError("Invalid RPN expression").

Domain: token lists built from integer literals (possibly negative, e.g. "-3") and the
operators + - * /. Valid expressions are generated from random expression trees whose
divisions never divide by zero; operand magnitudes are bounded so intermediate values stay small.
Invalid expressions: empty list, leftover operands, missing operands, unknown operator tokens.
"""
from hypothesis import strategies as st
from proof_ft.spec_runtime import prop

ENTRY_POINT = "evaluate_rpn"

CLARIFICATIONS = [
    "A token that is neither an integer nor one of + - * / makes the expression invalid.",
    "An empty expression is invalid.",
    "Inputs never divide by zero.",
]

MESSAGE = "Invalid RPN expression"


def trunc_div(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def apply(op, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return trunc_div(a, b)


@st.composite
def expression(draw, max_leaves=8, ops="+-*/"):
    """Return (tokens, value) for a random valid expression tree."""
    n_leaves = draw(st.integers(min_value=1, max_value=max_leaves))

    def build(n):
        if n == 1:
            v = draw(st.integers(min_value=-9, max_value=9))
            return [str(v)], v
        k = draw(st.integers(min_value=1, max_value=n - 1))
        lt, lv = build(k)
        rt, rv = build(n - k)
        op = draw(st.sampled_from(ops))
        if op == "/" and rv == 0:
            op = draw(st.sampled_from("+-*"))
        return lt + rt + [op], apply(op, lv, rv)

    return build(n_leaves)


def raises_invalid(f, tokens):
    try:
        f(tokens)
    except ValueError as exc:
        assert str(exc) == MESSAGE, f"wrong message {str(exc)!r}"
        return
    raise AssertionError("expected ValueError")


@prop("A valid expression evaluates to the value of its expression tree.", case=expression())
def evaluates_correctly(f, case):
    tokens, value = case
    assert f(tokens) == value


@prop("A single integer token evaluates to that integer.", v=st.integers(min_value=-10**6, max_value=10**6))
def single_number(f, v):
    assert f([str(v)]) == v


@prop("Division truncates toward zero, also for negative operands.",
      a=st.integers(min_value=-100, max_value=100),
      b=st.integers(min_value=-20, max_value=20).filter(lambda x: x != 0))
def division_truncates(f, a, b):
    assert f([str(a), str(b), "/"]) == trunc_div(a, b)


@prop("Subtraction and division take the earlier operand as the left-hand side.",
      a=st.integers(min_value=-50, max_value=50), b=st.integers(min_value=1, max_value=9),
      op=st.sampled_from("-/"))
def operand_order(f, a, b, op):
    assert f([str(a), str(b), op]) == apply(op, a, b)


@prop("Too many operands (leftover values on the stack) raise ValueError(\"Invalid RPN expression\").",
      first=expression(max_leaves=4), second=expression(max_leaves=4))
def too_many_operands(f, first, second):
    raises_invalid(f, first[0] + second[0])


@prop("Too many operators, an unknown operator or an empty list raise ValueError(\"Invalid RPN expression\").",
      case=expression(max_leaves=5), kind=st.sampled_from(["extra_op", "unknown_op", "empty", "lone_op"]),
      op=st.sampled_from("+-*/"), bad=st.sampled_from(["%", "^", "x", "//"]))
def malformed_raises(f, case, kind, op, bad):
    tokens, _ = case
    if kind == "extra_op":
        tokens = tokens + [op]
    elif kind == "unknown_op":
        tokens = tokens + ["2", bad]
    elif kind == "empty":
        tokens = []
    else:
        tokens = [tokens[0], op] if len(tokens) == 1 else [op] + tokens
    raises_invalid(f, tokens)

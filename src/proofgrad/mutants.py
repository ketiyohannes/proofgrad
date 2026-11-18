"""Single-point AST mutants of a reference solution.

A spec is only a useful reward if it rejects wrong code. We measure that by
mutating the verified reference (flip a comparison, nudge a constant, swap an
operator) and counting how many mutants the spec kills, next to how many the
original unit tests kill. Some mutants are semantically equivalent to the
reference and can never be killed, so scores are compared relatively, not
against 100%.
"""

from __future__ import annotations

import ast
import random
from collections.abc import Iterator

_COMPARE_SWAPS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}
_BINOP_SWAPS: dict[type[ast.operator], type[ast.operator]] = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.Add,
    ast.FloorDiv: ast.Mult,
    ast.Mod: ast.FloorDiv,
}
_BOOLOP_SWAPS: dict[type[ast.boolop], type[ast.boolop]] = {ast.And: ast.Or, ast.Or: ast.And}
_BUILTIN_SWAPS = {"min": "max", "max": "min", "any": "all", "all": "any"}
_DELETABLE = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr, ast.If, ast.For, ast.While)


def _is_docstring(node: ast.AST) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def _mutation_sites(tree: ast.AST) -> Iterator[tuple[int, str]]:
    """Yield (node index, mutation kind) for every mutable node, in walk order."""
    for index, node in enumerate(ast.walk(tree)):
        if isinstance(node, ast.Compare):
            for op_index, op in enumerate(node.ops):
                if type(op) in _COMPARE_SWAPS:
                    yield index, f"compare:{op_index}"
        elif isinstance(node, (ast.BinOp, ast.AugAssign)) and type(node.op) in _BINOP_SWAPS:
            yield index, "binop"
        elif isinstance(node, ast.BoolOp) and type(node.op) in _BOOLOP_SWAPS:
            yield index, "boolop"
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            yield index, "drop_not"
        elif isinstance(node, ast.Constant) and type(node.value) is int:
            yield index, "const:+1"
            yield index, "const:-1"
        elif isinstance(node, ast.Constant) and type(node.value) is bool:
            yield index, "bool"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _BUILTIN_SWAPS:
            yield index, "builtin"
        if isinstance(node, _DELETABLE) and not _is_docstring(node):
            yield index, "delete"


class _Apply(ast.NodeTransformer):
    def __init__(self, target_index: int, kind: str, node_order: dict[int, int]) -> None:
        self.target_index = target_index
        self.kind = kind
        self.node_order = node_order

    def visit(self, node: ast.AST) -> ast.AST:
        node = self.generic_visit(node)
        if self.node_order.get(id(node)) != self.target_index:
            return node
        kind = self.kind
        if kind.startswith("compare:") and isinstance(node, ast.Compare):
            i = int(kind.split(":")[1])
            node.ops[i] = _COMPARE_SWAPS[type(node.ops[i])]()
        elif kind == "binop" and isinstance(node, (ast.BinOp, ast.AugAssign)):
            node.op = _BINOP_SWAPS[type(node.op)]()
        elif kind == "boolop" and isinstance(node, ast.BoolOp):
            node.op = _BOOLOP_SWAPS[type(node.op)]()
        elif kind == "drop_not" and isinstance(node, ast.UnaryOp):
            return node.operand
        elif kind.startswith("const:") and isinstance(node, ast.Constant):
            node.value += 1 if kind.endswith("+1") else -1
        elif kind == "bool" and isinstance(node, ast.Constant):
            node.value = not node.value
        elif kind == "builtin" and isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            node.func.id = _BUILTIN_SWAPS[node.func.id]
        elif kind == "delete" and isinstance(node, _DELETABLE):
            return ast.copy_location(ast.Pass(), node)
        return node


def generate_mutants(source: str, limit: int = 30, seed: int = 0) -> list[str]:
    """Return up to ``limit`` distinct, compilable single-point mutants of ``source``."""
    original = ast.unparse(ast.parse(source))
    sites = list(_mutation_sites(ast.parse(source)))
    random.Random(seed).shuffle(sites)

    mutants: list[str] = []
    seen = {original}
    for index, kind in sites:
        tree = ast.parse(source)
        order = {id(node): i for i, node in enumerate(ast.walk(tree))}
        mutated = ast.fix_missing_locations(_Apply(index, kind, order).visit(tree))
        try:
            text = ast.unparse(mutated)
            compile(text, "<mutant>", "exec")
        except (SyntaxError, ValueError):
            continue
        if text not in seen:
            seen.add(text)
            mutants.append(text)
        if len(mutants) >= limit:
            break
    return mutants

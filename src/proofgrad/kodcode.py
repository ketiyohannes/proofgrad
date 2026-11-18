"""Select spec-friendly problems from KodCode-V1 (https://huggingface.co/datasets/KodCode/KodCode-V1).

KodCode already gives us a natural-language question, a verified reference
solution and pytest unit tests. We keep only problems a property-based spec can
check: a single pure top-level function using the standard library only, with
low similarity to the benchmarks we evaluate on.

Usage: python -m proofgrad.kodcode data/raw/*.parquet (or .jsonl exports) --out data/candidates.jsonl --limit 200
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import sys
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any

SOURCE = "KodCode/KodCode-V1"
SUBSETS = {"Leetcode", "Algorithm", "Filter", "Apps", "Taco", "Evol", "Prefill"}
DIFFICULTIES = {"easy", "medium"}
MAX_BENCHMARK_SIMILARITY = 0.8
MAX_SOLUTION_LINES = 60
# Modules that make a function impure, nondeterministic or able to touch the system.
BANNED_MODULES = {
    "asyncio", "datetime", "http", "io", "multiprocessing", "os", "pathlib", "random", "requests",
    "shutil", "socket", "subprocess", "sys", "tempfile", "threading", "time", "urllib",
}
BANNED_CALLS = {"input", "print", "open", "exec", "eval", "compile", "__import__", "globals", "setattr"}


def _imported_modules(tree: ast.Module) -> set[str]:
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def _signature(func: ast.FunctionDef) -> str:
    stub = ast.FunctionDef(
        name=func.name,
        args=func.args,
        body=[ast.Expr(ast.Constant(...))],
        decorator_list=[],
        returns=func.returns,
        type_params=[],
    )
    return ast.unparse(ast.fix_missing_locations(stub)).split("\n", 1)[0]


def _tested_function(test_code: str) -> str | None:
    """The single name the tests import from ``solution``, if there is exactly one."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(test_code)
    except SyntaxError:
        return None
    names = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "solution"
        for alias in node.names
    ]
    return names[0] if len(names) == 1 and names[0] != "*" else None


def screen(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Return (candidate, "ok") or (None, rejection reason)."""
    if row["subset"] not in SUBSETS:
        return None, "subset"
    if row["style"] != "instruct":
        return None, "style"
    if row["gpt_difficulty"] not in DIFFICULTIES:
        return None, "difficulty"
    if (row["benchmark_similarity"] or 0.0) >= MAX_BENCHMARK_SIMILARITY:
        return None, "benchmark_similarity"
    solution = row["solution"]
    if solution.count("\n") + 1 > MAX_SOLUTION_LINES:
        return None, "too_long"
    entry_point = _tested_function(row["test"])
    if entry_point is None:
        return None, "test_imports"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(solution)
    except SyntaxError:
        return None, "syntax"

    top_level = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    func = top_level.get(entry_point)
    if not isinstance(func, ast.FunctionDef):
        return None, "entry_point_not_function"
    if any(isinstance(node, ast.ClassDef) for node in tree.body):
        return None, "defines_class"
    modules = _imported_modules(tree)
    if modules - set(sys.stdlib_module_names) or modules & BANNED_MODULES:
        return None, "imports"
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    if called & BANNED_CALLS:
        return None, "impure_call"
    if not func.args.args:
        return None, "no_arguments"

    candidate = {
        "id": f"kodcode/{row['question_id']}",
        "source": SOURCE,
        "subset": row["subset"],
        "difficulty": row["gpt_difficulty"],
        "gpt_pass_percentage": row["gpt_pass_percentage"],
        "benchmark_similarity": row["benchmark_similarity"],
        "question": row["question"].strip(),
        "entry_point": entry_point,
        "signature": _signature(func),
        "reference_solution": solution.strip() + "\n",
        "unit_tests": row["test"].strip() + "\n",
    }
    return candidate, "ok"


def _rows(paths: list[Path]) -> Iterator[dict[str, Any]]:
    columns = ["question_id", "subset", "style", "gpt_difficulty", "gpt_pass_percentage",
               "benchmark_similarity", "question", "solution", "test"]
    for path in paths:
        if path.suffix == ".jsonl":
            with path.open() as fh:
                yield from (json.loads(line) for line in fh)
            continue
        import pyarrow.parquet as pq

        yield from pq.read_table(path, columns=columns).to_pylist()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("parquet", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=200, help="sample this many candidates")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    kept: list[dict[str, Any]] = []
    reasons: dict[str, int] = {}
    seen_questions: set[str] = set()
    for row in _rows(args.parquet):
        candidate, reason = screen(row)
        if candidate is not None:
            key = hashlib.sha256(candidate["question"].lower().encode()).hexdigest()
            if key in seen_questions:
                candidate, reason = None, "duplicate"
            seen_questions.add(key)
        reasons[reason] = reasons.get(reason, 0) + 1
        if candidate is not None:
            kept.append(candidate)

    random.Random(args.seed).shuffle(kept)
    sample = sorted(kept[: args.limit], key=lambda c: c["id"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        for candidate in sample:
            fh.write(json.dumps(candidate) + "\n")

    print(f"screened {sum(reasons.values())} rows: {dict(sorted(reasons.items(), key=lambda kv: -kv[1]))}")
    print(f"eligible {len(kept)}, wrote {len(sample)} to {args.out}")


if __name__ == "__main__":
    main()

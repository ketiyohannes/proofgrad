"""Independent judge and thin-test control for a problem.

The judge decides whether an answer is really correct. It is never used as a
training reward, so neither arm of an experiment grades itself:

- the full unit tests, plus
- differential testing: the answer must return what the reference solution
  returns on inputs recorded from the spec's input generators. Only the
  generators are reused; the spec's properties play no part.

Differential testing assumes one correct output per input. ``attach`` reports
problems where that looks false (see ``--help``), so they can be left out.

The thin tests are the first ``--thin`` test functions of the unit tests: the
"one or two examples" most problems outside curated datasets come with.

    uv run --no-sync python -m proofgrad.judge --problems data/problems_full.jsonl --out data/problems_judged.jsonl
"""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import json
import pickle
import random
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from proofgrad.verifier import verify_many

MAX_CASES = 300
MAX_CASE_BYTES = 4096
RECORD_EXAMPLES = 150

_TEMPLATE = '''

# --- judge: differential test against the reference solution ---
import base64 as _judge_b64, copy as _judge_copy, math as _judge_math, pickle as _judge_pickle
from solution import {entry_point} as _judge_candidate

_JUDGE_CASES = _judge_pickle.loads(_judge_b64.b64decode("{payload}"))


def _judge_same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return _judge_math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) or (a != a and b != b)
        except TypeError:
            return False
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_judge_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_judge_same(a[k], b[k]) for k in a)
    return a == b


def test_judge_differential():
    for args, kwargs, raised, expected in _JUDGE_CASES:
        try:
            got = _judge_candidate(*_judge_copy.deepcopy(args), **_judge_copy.deepcopy(kwargs))
        except Exception:
            assert raised, f"raised on {{args!r}}"
            continue
        assert not raised, f"reference raises on {{args!r}}"
        assert _judge_same(got, expected), f"{{args!r}}: got {{got!r}}, reference gives {{expected!r}}"
'''


def first_tests(unit_tests: str, k: int) -> str:
    """Keep imports and helpers but only the first ``k`` test functions."""
    kept, seen = [], 0
    for node in ast.parse(unit_tests).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            seen += 1
            if seen > k:
                continue
        kept.append(node)
    return ast.unparse(ast.Module(body=kept, type_ignores=[]))


def record_cases(problem: dict[str, Any]) -> list[tuple[tuple[Any, ...], dict[str, Any], bool, Any]]:
    """Run the spec's properties against the reference and record every call:
    ``(args, kwargs, reference raised, reference output)``.

    Executes the reference and the spec in this process; both are our own
    validated data, not model output. Call it through ``attach`` to get a
    separate process.
    """
    from hypothesis import HealthCheck, Phase, given, settings

    from proofgrad._runner import _bind, _load_module
    from proofgrad.spec_runtime import collect

    with tempfile.TemporaryDirectory(prefix="proofgrad_judge_") as tmp:
        (Path(tmp) / "reference.py").write_text(problem["reference_solution"])
        (Path(tmp) / "spec_module.py").write_text(problem["spec"])
        reference = getattr(_load_module("reference", Path(tmp) / "reference.py"), problem["entry_point"])
        spec_module = _load_module("spec_module", Path(tmp) / "spec_module.py")

    cases: dict[bytes, tuple[tuple[Any, ...], dict[str, Any], bool, Any]] = {}

    def recording(*args: Any, **kwargs: Any) -> Any:
        try:
            key = pickle.dumps((args, kwargs))
        except Exception:  # noqa: BLE001 - inputs we cannot store are simply not recorded
            key = None
        kept = (copy.deepcopy(args), copy.deepcopy(kwargs))
        try:
            result = reference(*copy.deepcopy(args), **copy.deepcopy(kwargs))
        except Exception:
            if key is not None and len(key) <= MAX_CASE_BYTES:
                cases.setdefault(key, (*kept, True, None))
            raise
        if key is not None and len(key) <= MAX_CASE_BYTES:
            try:
                pickle.dumps(result)
                cases.setdefault(key, (*kept, False, copy.deepcopy(result)))
            except Exception:  # noqa: BLE001 - unpicklable outputs (generators) cannot be compared later
                pass
        return result

    profile = settings(
        max_examples=RECORD_EXAMPLES, deadline=None, derandomize=True, database=None,
        phases=[Phase.explicit, Phase.generate], suppress_health_check=list(HealthCheck),
    )
    for prop in collect(spec_module):
        try:
            profile(given(**prop.strategies)(_bind(prop, recording)))()
        except Exception:  # noqa: BLE001 - only the recorded calls matter here
            pass
    recorded = list(cases.values())
    if len(recorded) > MAX_CASES:
        recorded = random.Random(0).sample(recorded, MAX_CASES)
    return recorded


def differential_tests(entry_point: str, cases: list[Any]) -> str:
    payload = base64.b64encode(pickle.dumps(cases)).decode()
    return _TEMPLATE.format(entry_point=entry_point, payload=payload)


def _judge_fields(problem: dict[str, Any], thin: int) -> dict[str, Any]:
    cases = record_cases(problem)
    return {
        "thin_tests": first_tests(problem["unit_tests"], thin),
        "judge_tests": problem["unit_tests"] + differential_tests(problem["entry_point"], cases),
        "judge_cases": len(cases),
    }


def attach(problems: list[dict[str, Any]], thin: int = 1) -> tuple[list[dict[str, Any]], list[str]]:
    """Add ``thin_tests`` and ``judge_tests`` to each problem.

    Returns the judged problems and the ids dropped because the reference
    itself fails the judge (too few recorded cases, or a non-deterministic
    reference)."""
    with ProcessPoolExecutor() as pool:
        fields = list(pool.map(_judge_fields, problems, [thin] * len(problems)))
    judged = [{**p, **f} for p, f in zip(problems, fields)]
    verdicts = verify_many(
        {"code": p["reference_solution"], "entry_point": p["entry_point"], "unit_tests": p["judge_tests"]} for p in judged
    )
    kept = [p for p, v in zip(judged, verdicts) if v.tests_passed and p["judge_cases"] >= 10]
    dropped = sorted({p["id"] for p in judged} - {p["id"] for p in kept})
    return kept, dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--ids", type=Path, help="JSON list of problem ids to keep (default: all)")
    parser.add_argument("--thin", type=int, default=1, help="number of leading test functions in the thin suite")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    problems = [json.loads(line) for line in args.problems.read_text().splitlines() if line.strip()]
    if args.ids:
        wanted = set(json.loads(args.ids.read_text()))
        problems = [p for p in problems if p["id"] in wanted]
    judged, dropped = attach(problems, args.thin)
    args.out.write_text("".join(json.dumps(p) + "\n" for p in judged))
    cases = sorted(p["judge_cases"] for p in judged)
    print(f"judged {len(judged)} problems; differential cases per problem: min {cases[0]}, median {cases[len(cases) // 2]}, max {cases[-1]}")
    if dropped:
        print(f"dropped {len(dropped)} (reference fails its own judge or < 10 cases): {dropped}")


if __name__ == "__main__":
    main()

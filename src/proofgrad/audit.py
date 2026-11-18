"""Audit an experiment from artifacts already on disk (no model needed).

Four checks, each answering one "could this run have worked?" question:

1. training signal: per-completion rewards parsed from TRL's ``log_completions``
   tables. How many groups had no correct answer, and how much of the advantage
   came from ranking wrong answers by partial credit?
2. reward floor: reward earned by trivial stubs (``return None``, ``return []``).
3. split leakage: held-out problems whose entry point also appears in train.
4. thin tests: how often the first k unit tests accept answers the judge
   (spec AND full unit tests) rejects, on completions saved by ``evaluate``.

    uv run --no-sync python -m proofgrad.audit --problems data/problems_full.jsonl \
        --logs spec=runs/full/train_spec.log tests=runs/full/train_tests.log \
        --reports runs/full/heldout_*.json runs/thinking/heldout_*.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from proofgrad.judge import first_tests
from proofgrad.prompts import extract_code
from proofgrad.verifier import verify_many

_PANEL = re.compile(r"╭─+ Step (\d+) ─+╮")
_HEADER = re.compile(r"┃ Prompt\s+┃ Completion\s+┃ (\w+)")
_ROW = re.compile(r"│ │ USER\s+│ ASSISTANT\s+│\s+(-?[\d.]+) │\s+(-?[\d.]+) │\s+(-?[\d.]+) │ │")
STUBS = ("None", "args[0] if args else None", "0", "[]", "''", "True", "False")


def parse_groups(log: Path) -> list[list[tuple[float, float, float]]]:
    """Return one group per step as ``(spec reward, test reward, advantage)`` per completion.

    Needs a run with ``--monitor``. TRL prints the training reward first, so the
    column order depends on the run; the table header tells which.
    """
    text = log.read_text(errors="replace")
    header = _HEADER.search(text)
    if header is None:
        raise ValueError(f"{log}: no completion tables (was log_completions on?)")
    spec_first = header.group(1).startswith("spec")
    parts = _PANEL.split(text)
    groups: dict[int, list[tuple[float, float, float]]] = {}
    for step, body in zip(parts[1::2], parts[2::2]):
        rows = [tuple(map(float, m)) for m in _ROW.findall(body)]
        if rows:  # a panel can be printed twice; the step number identifies it
            groups[int(step)] = [(a, b, adv) if spec_first else (b, a, adv) for a, b, adv in rows]
    return [groups[step] for step in sorted(groups)]


def training_signal(log: Path, reward: str) -> dict[str, Any]:
    groups = parse_groups(log)
    own = 0 if reward == "spec" else 1
    completions = [c for group in groups for c in group]
    no_correct = [g for g in groups if not any(c[own] == 1.0 for c in g)]
    passes = Counter(sum(c[own] == 1.0 for c in g) for g in groups)
    total_advantage = sum(abs(c[2]) for c in completions) or 1.0
    tests_passing = [c for c in completions if c[1] == 1.0]
    spec_passing = [c for c in completions if c[0] == 1.0]
    return {
        "groups": len(groups),
        "completions": len(completions),
        "groups_without_correct_answer": len(no_correct) / len(groups),
        "groups_in_learnable_band": sum(n for k, n in passes.items() if 2 <= k <= 5) / len(groups),
        "advantage_share_from_groups_without_correct_answer": sum(abs(c[2]) for g in no_correct for c in g) / total_advantage,
        "reward_exactly_zero": sum(c[own] == 0.0 for c in completions) / len(completions),
        "tests_pass_spec_fail": sum(c[0] < 1.0 for c in tests_passing) / (len(tests_passing) or 1),
        "spec_pass_tests_fail": sum(c[1] < 1.0 for c in spec_passing) / (len(spec_passing) or 1),
    }


def _reward(fraction: float, passed: bool) -> float:
    return 0.5 * fraction + 0.5 * float(passed)


def reward_floor(problems: list[dict[str, Any]]) -> dict[str, float]:
    """Mean reward of the best trivial stub per problem: what partial credit pays for junk."""
    best_spec = [0.0] * len(problems)
    best_tests = [0.0] * len(problems)
    for value in STUBS:
        jobs = [
            {"code": f"def {p['entry_point']}(*args, **kwargs):\n    return {value}\n", "entry_point": p["entry_point"],
             "spec": p["spec"], "unit_tests": p["unit_tests"]}
            for p in problems
        ]
        for i, verdict in enumerate(verify_many(jobs)):
            best_spec[i] = max(best_spec[i], _reward(verdict.property_score, verdict.spec_passed))
            best_tests[i] = max(best_tests[i], _reward(verdict.test_score, verdict.tests_passed))
    return {"spec": sum(best_spec) / len(problems), "tests": sum(best_tests) / len(problems)}


def split_leakage(problems: list[dict[str, Any]]) -> list[str]:
    """Entry points that appear on both sides of the split (same task, different wording)."""
    names = {split: {p["entry_point"] for p in problems if p["split"] == split} for split in ("train", "test")}
    return sorted(names["train"] & names["test"])


def thin_test_accepts(problems: list[dict[str, Any]], reports: list[Path], ks: tuple[int, ...] = (1, 2, 3)) -> dict[str, Any]:
    by_id = {p["id"]: p for p in problems}
    records = [r for path in reports for r in json.loads(path.read_text())["records"]]
    wrong = [r for r in records if not (r["spec_passed"] and r["tests_passed"])]
    result: dict[str, Any] = {
        "completions": len(records),
        "wrong": len(wrong),
        "accepted_by_full_tests": sum(r["tests_passed"] for r in wrong) / len(wrong),
        "accepted_by_spec": sum(r["spec_passed"] for r in wrong) / len(wrong),
    }
    for k in ks:
        jobs = [
            {"code": extract_code(r["completion"], by_id[r["id"]]["entry_point"]), "entry_point": by_id[r["id"]]["entry_point"],
             "unit_tests": first_tests(by_id[r["id"]]["unit_tests"], k)}
            for r in wrong
        ]
        result[f"accepted_by_first_{k}_tests"] = sum(v.tests_passed for v in verify_many(jobs)) / len(wrong)
    return result


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, dict):
        return {k: _rounded(v) for k, v in value.items()}
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--logs", nargs="*", default=[], help="reward=path to a --monitor training log (reward: spec or tests)")
    parser.add_argument("--reports", nargs="*", type=Path, default=[], help="evaluate reports with saved completions")
    args = parser.parse_args()

    problems = [json.loads(line) for line in args.problems.read_text().splitlines() if line.strip()]
    out: dict[str, Any] = {"training_signal": {}}
    for pair in args.logs:
        reward, path = pair.split("=", 1)
        out["training_signal"][reward] = training_signal(Path(path), reward)
    out["reward_floor_best_stub"] = reward_floor(problems)
    out["entry_points_in_both_splits"] = split_leakage(problems)
    if args.reports:
        out["thin_tests"] = thin_test_accepts(problems, args.reports)
    print(json.dumps(_rounded(out), indent=2))


if __name__ == "__main__":
    main()

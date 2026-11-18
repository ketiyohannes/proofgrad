"""Validate specs against our standards and assemble the training dataset.

For every candidate with a spec in ``--specs/<slug>.py`` a problem is accepted
only if:

1. the spec declares ``ENTRY_POINT`` matching the candidate and at least
   ``MIN_PROPERTIES`` independent properties (partial credit needs several);
2. the reference solution satisfies every property at a high example count
   (the spec is satisfiable and not buggy);
3. the reference solution passes the original unit tests;
4. the spec kills mutants of the reference about as well as the unit tests do
   (the spec is strong enough to reject wrong code). Properties that no mutant
   ever fails are reported so weak rubric items can be reviewed, and problems
   with too few mutants to measure strength are flagged ``weakly_validated``;
5. the spec writer did not set ``EXCLUDE_REASON`` (e.g. the reference
   contradicts the problem statement).

A spec may also set ``CLARIFICATIONS``: conventions the spec checks that the
question leaves implicit. They are appended to the student prompt, so the
student is never graded on behavior it could not know about.

Usage: python -m proofgrad.build --candidates data/candidates.jsonl --specs data/specs --out data/problems.jsonl
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from proofgrad.mutants import generate_mutants
from proofgrad.prompts import build_prompt
from proofgrad.verifier import DEFAULT_MAX_EXAMPLES, verify, verify_many

MIN_PROPERTIES = 2
VALIDATION_EXAMPLES = 500
MAX_MUTANTS = 30
# The spec may miss at most this fraction of the mutants the unit tests catch.
MAX_MISSED_FRACTION = 0.10
HELD_OUT_PERCENT = 20
# Below this many mutants the strength check says little; flag, don't reject.
MIN_MUTANTS_FOR_STRENGTH = 5


@dataclass
class MutationStats:
    mutants: int
    killed_by_spec: int
    killed_by_tests: int
    missed_by_spec: int  # killed by tests but not by the spec
    caught_only_by_spec: int  # "subtly wrong" code the tests let through
    properties_never_failing: list[str]


def slug(problem_id: str) -> str:
    return problem_id.replace("/", "__")


def split_for(problem_id: str) -> str:
    bucket = int(hashlib.sha256(problem_id.encode()).hexdigest(), 16) % 100
    return "test" if bucket < HELD_OUT_PERCENT else "train"


@dataclass
class SpecHeader:
    entry_point: str | None
    n_properties: int
    clarifications: list[str]
    exclude_reason: str | None


def _spec_header(spec: str) -> SpecHeader:
    """Read the spec's module-level metadata statically (literals only)."""
    tree = ast.parse(spec)
    constants: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and node.value is not None:
                    try:
                        constants[target.id] = ast.literal_eval(node.value)
                    except ValueError:
                        pass
    n_props = sum(
        1
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        for dec in node.decorator_list
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "prop"
    )
    clarifications = constants.get("CLARIFICATIONS") or []
    if not (isinstance(clarifications, (list, tuple)) and all(isinstance(c, str) for c in clarifications)):
        raise ValueError("CLARIFICATIONS must be a list of strings")
    return SpecHeader(constants.get("ENTRY_POINT"), n_props, list(clarifications), constants.get("EXCLUDE_REASON") or None)


def mutation_stats(candidate: dict[str, Any], spec: str) -> MutationStats:
    mutants = generate_mutants(candidate["reference_solution"], limit=MAX_MUTANTS)
    common = {"entry_point": candidate["entry_point"]}
    spec_verdicts = verify_many({"code": m, "spec": spec, "max_examples": DEFAULT_MAX_EXAMPLES, **common} for m in mutants)
    test_verdicts = verify_many({"code": m, "unit_tests": candidate["unit_tests"], **common} for m in mutants)
    spec_kills = [not v.spec_passed for v in spec_verdicts]
    test_kills = [not v.tests_passed for v in test_verdicts]

    failing_props = {p.name for v in spec_verdicts for p in v.properties if not p.passed}
    all_props = [p.name for v in spec_verdicts for p in v.properties]
    never_failing = sorted(set(all_props) - failing_props)
    return MutationStats(
        mutants=len(mutants),
        killed_by_spec=sum(spec_kills),
        killed_by_tests=sum(test_kills),
        missed_by_spec=sum(t and not s for s, t in zip(spec_kills, test_kills)),
        caught_only_by_spec=sum(s and not t for s, t in zip(spec_kills, test_kills)),
        properties_never_failing=never_failing,
    )


def validate(candidate: dict[str, Any], spec: str) -> tuple[dict[str, Any] | None, str]:
    """Return (problem, "ok") or (None, rejection reason)."""
    try:
        header = _spec_header(spec)
    except (SyntaxError, ValueError) as exc:
        return None, f"spec header error: {exc}"
    entry_point, n_props = header.entry_point, header.n_properties
    if header.exclude_reason:
        return None, f"excluded by spec writer: {header.exclude_reason}"
    if entry_point != candidate["entry_point"]:
        return None, f"spec ENTRY_POINT {entry_point!r} != {candidate['entry_point']!r}"
    if n_props < MIN_PROPERTIES:
        return None, f"spec has {n_props} properties, need >= {MIN_PROPERTIES}"

    ref = candidate["reference_solution"]
    verdict = verify(ref, entry_point, spec=spec, max_examples=VALIDATION_EXAMPLES, property_timeout=20.0)
    if not verdict.spec_passed:
        failures = "; ".join(f"{c.name}: {c.detail}" for c in verdict.failures()) or verdict.error
        return None, f"reference fails spec: {failures}"
    verdict = verify(ref, entry_point, unit_tests=candidate["unit_tests"])
    if not verdict.tests_passed:
        failures = "; ".join(f"{c.name}: {c.detail}" for c in verdict.failures()) or verdict.error
        return None, f"reference fails unit tests: {failures}"

    stats = mutation_stats(candidate, spec)
    allowed_missed = int(MAX_MISSED_FRACTION * stats.killed_by_tests)
    if stats.missed_by_spec > allowed_missed:
        return None, f"spec too weak: missed {stats.missed_by_spec} of {stats.killed_by_tests} mutants the tests catch"

    problem = {
        "id": candidate["id"],
        "split": split_for(candidate["id"]),
        "prompt": build_prompt(candidate["question"], candidate["signature"], header.clarifications),
        "question": candidate["question"],
        "entry_point": entry_point,
        "signature": candidate["signature"],
        "spec": spec,
        "reference_solution": ref,
        "unit_tests": candidate["unit_tests"],
        "meta": {
            "source": candidate["source"],
            "subset": candidate["subset"],
            "difficulty": candidate["difficulty"],
            "gpt_pass_percentage": candidate["gpt_pass_percentage"],
            "benchmark_similarity": candidate["benchmark_similarity"],
            "n_properties": n_props,
            "clarifications": header.clarifications,
            "weakly_validated": stats.mutants < MIN_MUTANTS_FOR_STRENGTH,
            "mutation": asdict(stats),
        },
    }
    return problem, "ok"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ids", help="comma-separated candidate ids to validate (default: all)")
    args = parser.parse_args()

    candidates = [json.loads(line) for line in args.candidates.read_text().splitlines() if line.strip()]
    if args.ids:
        wanted = set(args.ids.split(","))
        candidates = [c for c in candidates if c["id"] in wanted]
    accepted, rejected, missing = [], [], 0
    for candidate in candidates:
        spec_path = args.specs / f"{slug(candidate['id'])}.py"
        if not spec_path.exists():
            missing += 1
            continue
        problem, reason = validate(candidate, spec_path.read_text())
        if problem is None:
            rejected.append({"id": candidate["id"], "reason": reason})
            print(f"REJECT {candidate['id']}: {reason}")
            continue
        accepted.append(problem)
        m = problem["meta"]["mutation"]
        print(
            f"ACCEPT {candidate['id']} [{problem['split']}] props={problem['meta']['n_properties']} "
            f"mutants={m['mutants']} spec_kills={m['killed_by_spec']} test_kills={m['killed_by_tests']} "
            f"only_spec={m['caught_only_by_spec']} missed={m['missed_by_spec']}"
            + (f" never_failing={m['properties_never_failing']}" if m["properties_never_failing"] else "")
            + (" WEAKLY_VALIDATED" if problem["meta"]["weakly_validated"] else "")
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(p) + "\n" for p in accepted))
    args.out.with_name(args.out.stem + ".rejected.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rejected))

    splits = {s: sum(p["split"] == s for p in accepted) for s in ("train", "test")}
    print(f"\naccepted {len(accepted)} {splits}, rejected {len(rejected)}, no spec yet {missing}")
    if accepted:
        tot = {k: sum(p["meta"]["mutation"][k] for p in accepted) for k in ("mutants", "killed_by_spec", "killed_by_tests", "caught_only_by_spec")}
        print(f"mutation totals: {tot}")


if __name__ == "__main__":
    main()

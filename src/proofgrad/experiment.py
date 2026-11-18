"""Gated experiment from the revised hypothesis (docs/handoff.md): analysis and problem selection.

Works on ``proofgrad.evaluate`` reports made with ``--samples N`` on problems
prepared by ``proofgrad.judge`` (records carry spec, thin-test, full-test and
judge verdicts).

    # H1: how often does each checker accept answers the judge rejects?
    python -m proofgrad.experiment h1 --report runs/small/samples_base_candidates.json
    # choose train / unseen problems the student can sometimes solve
    python -m proofgrad.experiment select --report ... --problems runs/small/candidates.jsonl --out runs/small/problems.jsonl
    # H2: compare arms after training
    python -m proofgrad.experiment h2 --problems runs/small/problems.jsonl \
        --reports base=... spec=... thin=...
    # H3: warmup problems and spec-first prompts, then what the answers state before the code
    python -m proofgrad.experiment h3-data --all data/problems_full.jsonl --eval runs/small/problems.jsonl --out-dir runs/h3
    python -m proofgrad.experiment h3 --report runs/h3/samples_sft_props.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from proofgrad.prompts import spec_first_prompt, stated_properties

DEFAULT_PAIRS = (("spec", "thin"), ("spec", "base"), ("thin", "base"))
CHECKERS = {"thin": "thin_passed", "tests": "tests_passed", "spec": "spec_passed"}
Record = dict[str, Any]


def by_problem(records: list[Record]) -> dict[str, list[Record]]:
    grouped: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        grouped[record["id"]].append(record)
    return dict(grouped)


def bootstrap(groups: list[Any], statistic: Callable[[list[Any]], float | None], draws: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% interval of ``statistic`` when resampling whole problems (answers to one problem are not independent)."""
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        value = statistic([rng.choice(groups) for _ in groups])
        if value is not None:
            values.append(value)
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def _rate(records: list[Record], hit: Callable[[Record], bool], among: Callable[[Record], bool] = lambda r: True) -> float | None:
    pool = [r for r in records if among(r)]
    return sum(hit(r) for r in pool) / len(pool) if pool else None


def _flat(groups: list[list[Record]]) -> list[Record]:
    return [r for group in groups for r in group]


def h1(records: list[Record]) -> dict[str, Any]:
    """False accepts (wrong answers a checker passes) and false rejects, against the judge."""
    groups = list(by_problem(records).values())
    wrong = lambda r: not r["judge_passed"]  # noqa: E731
    out: dict[str, Any] = {
        "problems": len(groups), "answers": len(records), "wrong_answers": sum(wrong(r) for r in records), "checkers": {},
    }
    for name, key in CHECKERS.items():
        accepts = lambda r, key=key: r[key]  # noqa: E731
        out["checkers"][name] = {
            "false_accept_rate": _rate(records, accepts, wrong),
            "false_accept_ci": bootstrap(groups, lambda gs, accepts=accepts: _rate(_flat(gs), accepts, wrong)),
            "false_reject_rate": _rate(records, lambda r: not accepts(r), lambda r: r["judge_passed"]),
            "accepted_answers_that_are_wrong": _rate(records, wrong, accepts),
            "problems_with_a_false_accept": sum(any(accepts(r) and wrong(r) for r in g) for g in groups),
        }

    def gap(gs: list[list[Record]]) -> float | None:
        thin, spec = _rate(_flat(gs), lambda r: r["thin_passed"], wrong), _rate(_flat(gs), lambda r: r["spec_passed"], wrong)
        return None if thin is None or spec is None else thin - spec

    out["thin_minus_spec"] = gap(groups)
    out["thin_minus_spec_ci"] = bootstrap(groups, gap)
    thin, spec = out["checkers"]["thin"]["false_accept_rate"], out["checkers"]["spec"]["false_accept_rate"]
    # Pre-registered in docs/handoff.md: thin >= 15%, spec <= 5%, gap >= 10 points and its interval above 0.
    out["gate_passed"] = bool(thin >= 0.15 and spec <= 0.05 and out["thin_minus_spec"] >= 0.10 and out["thin_minus_spec_ci"][0] > 0)
    # Answers the spec and the full tests accept but the reference comparison rejects: either a real
    # gap in both, or a task with several correct outputs (where differential testing is unfair).
    out["passes_spec_and_tests_but_not_judge"] = {
        pid: n for pid, g in by_problem(records).items() if (n := sum(r["spec_passed"] and r["tests_passed"] and not r["judge_passed"] for r in g))
    }
    return out


def select(
    records: list[Record], problems: list[dict[str, Any]], size: int, exclude: set[str], band: tuple[float, float] = (1 / 8, 6 / 8),
    together: list[list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Pick up to ``2 * size`` problems the student sometimes solves and split them into train and unseen halves.

    Eligible: base-model judge pass rate inside ``band``. Problems where the
    thin tests were fooled at least once come first (that is where the two
    rewards differ), and the two halves get alternating picks so they are
    comparable. With too few eligible problems the train half is filled first.
    Problems sharing an entry point never land on both sides; ``together``
    lists further entry points that are the same task under different names.
    """
    family = {name: group[0] for group in together or [] for name in group}
    stats = {}
    for pid, group in by_problem(records).items():
        passes = sum(r["judge_passed"] for r in group)
        fooled = sum(r["thin_passed"] and not r["judge_passed"] for r in group)
        if pid not in exclude and band[0] <= passes / len(group) <= band[1]:
            stats[pid] = (fooled, passes, len(group))
    ranked = sorted(stats, key=lambda pid: (-stats[pid][0], pid))
    by_id = {p["id"]: p for p in problems}
    halves: dict[str, list[str]] = {"train": [], "test": []}
    caps = {"train": size, "test": min(size, max(0, len(ranked) - size))}
    names: dict[str, set[str]] = {"train": set(), "test": set()}
    for pid in ranked:
        name = family.get(by_id[pid]["entry_point"], by_id[pid]["entry_point"])
        order = sorted(halves, key=lambda half: len(halves[half]))  # fill the shorter half first
        for half in order:
            other = "test" if half == "train" else "train"
            if len(halves[half]) < caps[half] and name not in names[other]:
                halves[half].append(pid)
                names[half].add(name)
                break
    chosen = []
    for half, ids in halves.items():
        for pid in ids:
            fooled, passes, n = stats[pid]
            chosen.append({**by_id[pid], "split": half, "base": {"judge_passes": passes, "thin_fooled": fooled, "samples": n}})
    return chosen


def h2(
    reports: dict[str, list[Record]], problems: list[dict[str, Any]], pairs: tuple[tuple[str, str], ...] = DEFAULT_PAIRS,
) -> dict[str, Any]:
    """Per arm and split: judge pass rate and how much accepted-but-wrong code the model writes."""
    split_of = {p["id"]: p["split"] for p in problems}
    metrics: dict[str, Callable[[list[Record]], float | None]] = {
        "judge_pass_rate": lambda rs: _rate(rs, lambda r: r["judge_passed"]),
        "thin_pass_rate": lambda rs: _rate(rs, lambda r: r["thin_passed"]),
        "subtly_wrong_rate": lambda rs: _rate(rs, lambda r: r["thin_passed"] and not r["judge_passed"]),
        "thin_accepted_that_are_wrong": lambda rs: _rate(rs, lambda r: not r["judge_passed"], lambda r: r["thin_passed"]),
    }
    out: dict[str, Any] = {}
    for split in ("train", "test", "all"):
        inside = lambda r, split=split: r["id"] in split_of and split in ("all", split_of[r["id"]])  # noqa: E731
        per_arm = {arm: by_problem([r for r in records if inside(r)]) for arm, records in reports.items()}
        ids = sorted(set.intersection(*(set(groups) for groups in per_arm.values())))
        section: dict[str, Any] = {"problems": len(ids), "arms": {}, "differences": {}}
        for arm, groups in per_arm.items():
            answers = _flat([groups[pid] for pid in ids])
            section["arms"][arm] = {"answers": len(answers), **{name: metric(answers) for name, metric in metrics.items()}}
        for a, b in [(a, b) for a, b in pairs if a in per_arm and b in per_arm]:
            for name in ("judge_pass_rate", "subtly_wrong_rate"):
                metric = metrics[name]

                def difference(chosen: list[str], a: str = a, b: str = b, metric: Callable[[list[Record]], float | None] = metric) -> float | None:
                    x = metric(_flat([per_arm[a][pid] for pid in chosen]))
                    y = metric(_flat([per_arm[b][pid] for pid in chosen]))
                    return None if x is None or y is None else x - y

                section["differences"][f"{a}_minus_{b}:{name}"] = {"value": difference(ids), "ci": bootstrap(ids, difference)}
        out[split] = section
    return out


def h3_data(
    all_problems: list[dict[str, Any]], eval_problems: list[dict[str, Any]], exclude: set[str] = frozenset(),
) -> dict[str, list[dict[str, Any]]]:
    """Warmup problems (never evaluated, no entry point shared with the evaluated ones or listed in
    ``exclude``) and the evaluated problems with the plain and the spec-first prompt."""
    taken_ids = {p["id"] for p in eval_problems}
    taken_names = {p["entry_point"] for p in eval_problems} | set(exclude)
    warmup = [p for p in all_problems if p["id"] not in taken_ids and p["entry_point"] not in taken_names]
    return {
        "warmup": warmup,
        "problems_plain": eval_problems,
        "problems_props": [{**p, "prompt": spec_first_prompt(p["prompt"])} for p in eval_problems],
    }


def h3(records: list[Record]) -> dict[str, Any]:
    """What spec-first answers state before the code, and whether it goes with passing the judge."""
    stated = [stated_properties(r["completion"]) for r in records]
    with_props = [r for r, props in zip(records, stated) if props]
    without = [r for r, props in zip(records, stated) if not props]
    # A line used in answers to three or more different problems is boilerplate, not a property of the task.
    problems_using: dict[str, set[str]] = defaultdict(set)
    for r, props in zip(records, stated):
        for line in props:
            problems_using[line.strip().lower()].add(r["id"])
    lines = [line.strip().lower() for props in stated for line in props]
    passing = [len(props) for r, props in zip(records, stated) if r["judge_passed"]]
    failing = [len(props) for r, props in zip(records, stated) if not r["judge_passed"]]
    # Within a problem: do answers with more stated properties pass more often than those with fewer?
    more, fewer = [], []
    for group in by_problem(records).values():
        counts = [len(stated_properties(r["completion"])) for r in group]
        median = sorted(counts)[len(counts) // 2]
        more += [r["judge_passed"] for r, n in zip(group, counts) if n > median]
        fewer += [r["judge_passed"] for r, n in zip(group, counts) if n < median]
    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    return {
        "answers": len(records),
        "state_properties": len(with_props) / len(records),
        "mean_properties_per_answer": mean([len(props) for props in stated]),
        "judge_pass_rate_with_properties": mean([r["judge_passed"] for r in with_props]),
        "judge_pass_rate_without_properties": mean([r["judge_passed"] for r in without]),
        "mean_properties_passing_answers": mean(passing),
        "mean_properties_failing_answers": mean(failing),
        "pass_rate_above_problem_median_count": mean(more),
        "pass_rate_below_problem_median_count": mean(fewer),
        "boilerplate_line_share": mean([len(problems_using[line]) >= 3 for line in lines]),
    }


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, dict):
        return {k: _rounded(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_rounded(v) for v in value]
    return value


def _records(path: str | Path) -> list[Record]:
    return json.loads(Path(path).read_text())["records"]


def _problems(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    p_h1 = commands.add_parser("h1")
    p_h1.add_argument("--report", type=Path, required=True)
    p_select = commands.add_parser("select")
    p_select.add_argument("--report", type=Path, required=True)
    p_select.add_argument("--problems", type=Path, required=True)
    p_select.add_argument("--size", type=int, default=20, help="problems per half (train, unseen)")
    p_select.add_argument("--exclude", nargs="*", default=[], help="problem ids to leave out (e.g. several correct outputs)")
    p_select.add_argument("--together", nargs="*", default=[], metavar="A,B", help="entry points that are the same task: keep on one side")
    p_select.add_argument("--band", type=float, nargs=2, default=(1 / 8, 6 / 8), metavar=("LOW", "HIGH"), help="eligible base judge pass rate")
    p_select.add_argument("--out", type=Path, required=True)
    p_h2 = commands.add_parser("h2")
    p_h2.add_argument("--problems", type=Path, required=True)
    p_h2.add_argument("--reports", nargs="+", required=True, help="arm=path, e.g. base=... spec=... thin=...")
    p_h2.add_argument("--pairs", nargs="*", metavar="A:B", help="differences to report (default: spec:thin spec:base thin:base)")
    p_data = commands.add_parser("h3-data")
    p_data.add_argument("--all", type=Path, required=True, help="every problem with a spec")
    p_data.add_argument("--eval", type=Path, required=True, help="the problems of the gated experiment (train + unseen)")
    p_data.add_argument("--exclude", nargs="*", default=[], help="entry points to keep out of the warmup (same task as an evaluated one)")
    p_data.add_argument("--out-dir", type=Path, required=True)
    p_h3 = commands.add_parser("h3")
    p_h3.add_argument("--report", type=Path, required=True, help="samples from an arm that answers spec-first")
    for sub in (p_h1, p_h2, p_h3):
        sub.add_argument("--out", type=Path, help="also write the result as JSON")
    args = parser.parse_args()

    if args.command == "select":
        together = [group.split(",") for group in args.together]
        chosen = select(_records(args.report), _problems(args.problems), args.size, set(args.exclude), tuple(args.band), together)
        args.out.write_text("".join(json.dumps(p) + "\n" for p in chosen))
        for half in ("train", "test"):
            part = [p for p in chosen if p["split"] == half]
            fooled = sum(p["base"]["thin_fooled"] > 0 for p in part)
            rate = sum(p["base"]["judge_passes"] for p in part) / sum(p["base"]["samples"] for p in part)
            print(f"{half}: {len(part)} problems, base judge pass rate {rate:.0%}, thin tests fooled at least once on {fooled}")
        return
    if args.command == "h3-data":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for name, rows in h3_data(_problems(args.all), _problems(args.eval), set(args.exclude)).items():
            (args.out_dir / f"{name}.jsonl").write_text("".join(json.dumps(p) + "\n" for p in rows))
            print(f"{name}: {len(rows)} problems")
        return
    if args.command == "h1":
        result = h1(_records(args.report))
    elif args.command == "h3":
        result = h3(_records(args.report))
    else:
        pairs = tuple(tuple(pair.split(":", 1)) for pair in args.pairs) if args.pairs else DEFAULT_PAIRS
        result = h2({arm: _records(path) for arm, path in (pair.split("=", 1) for pair in args.reports)}, _problems(args.problems), pairs)
    result = _rounded(result)
    if args.out:
        args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

"""Standard-benchmark evaluation with EvalPlus (HumanEval+ and MBPP+).

Prompting follows EvalPlus's own instruct protocol (instruction prefix plus a
pre-filled assistant reply that opens a ```python block), decoding is greedy,
code is cleaned with ``evalplus.sanitize`` and scored by ``evalplus.evaluate``,
so numbers are comparable across models and with published EvalPlus results
(modulo prompt/template differences of each model family).

Reports pass@1 on the original tests ("base") and on the extended tests
("plus"). ``base - plus`` is the share of solutions that pass the original tests
but break on harder inputs: the benchmark analogue of our "subtly wrong" rate.

Setup (EvalPlus's scoring code only; its API-provider extras are not needed):
    uv pip install --no-deps evalplus==0.3.1 wget tempdir multipledispatch appdirs termcolor fire \
        stop-sequencer tree-sitter tree-sitter-python

    uv run --no-sync python -m proofgrad.benchmark --model models/Qwen3.5-0.8B --out-dir runs/bench/base
    uv run --no-sync python -m proofgrad.benchmark --model models/Qwen3.5-0.8B \
        --adapter runs/long/grpo/final --out-dir runs/bench/grpo
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from proofgrad.evaluate import generate_from_texts, load_model

INSTRUCTION_PREFIX = "Please provide a self-contained Python script that solves the following problem in a markdown code block:"
# EvalPlus caps memory with RLIMIT_AS, which macOS rejects ("current limit exceeds
# maximum limit"), failing every task. -1 disables only the memory cap; its time
# limits and other guards still apply.
if sys.platform == "darwin":
    os.environ.setdefault("EVALPLUS_MAX_MEMORY_BYTES", "-1")

RESPONSE_PREFIX = "Below is a Python script with a self-contained function that solves the problem and passes corresponding tests:"


def load_tasks(dataset: str) -> dict[str, dict[str, Any]]:
    from evalplus.data import get_human_eval_plus, get_mbpp_plus

    return {"humaneval": get_human_eval_plus, "mbpp": get_mbpp_plus}[dataset]()


def chat_texts(tokenizer: Any, tasks: list[dict[str, Any]]) -> list[str]:
    from evalplus.provider.utility import make_raw_chat_prompt

    return [make_raw_chat_prompt(t["prompt"], INSTRUCTION_PREFIX, RESPONSE_PREFIX, tokenizer) for t in tasks]


def summarize(results_path: Path) -> dict[str, Any]:
    """pass@1 (greedy, one sample per task) from EvalPlus's results file."""
    results = json.loads(results_path.read_text())["eval"]
    rows = [samples[0] for samples in results.values()]
    n = len(rows)
    base = sum(r["base_status"] == "pass" for r in rows)
    plus = sum(r["base_status"] == "pass" and r["plus_status"] == "pass" for r in rows)
    return {
        "tasks": n,
        "base_pass@1": base / n,
        "plus_pass@1": plus / n,
        "base_only_rate": (base - plus) / n,
    }


def score(dataset: str, samples_path: Path) -> dict[str, Any]:
    from evalplus.evaluate import evaluate

    results_path = samples_path.with_name(samples_path.stem + "_eval_results.json")
    results_path.unlink(missing_ok=True)
    evaluate(dataset=dataset, samples=str(samples_path), i_just_wanna_run=True)
    return summarize(results_path)


def run(model: Any, tokenizer: Any, dataset: str, out_dir: Path, max_new_tokens: int, batch_size: int, limit: int) -> dict[str, Any]:
    from evalplus.sanitize import sanitize

    tasks = load_tasks(dataset)
    task_ids = list(tasks)[:limit] if limit else list(tasks)
    texts = chat_texts(tokenizer, [tasks[t] for t in task_ids])
    started = time.time()
    outputs = generate_from_texts(model, tokenizer, texts, 1, max_new_tokens, batch_size, stop_strings=["```"])

    samples_path = out_dir / f"{dataset}_samples.jsonl"
    with samples_path.open("w") as fh:
        for task_id, (raw,) in zip(task_ids, outputs):
            code = raw.split("```")[0]
            solution = sanitize(code, tasks[task_id]["entry_point"])
            fh.write(json.dumps({"task_id": task_id, "solution": solution, "raw": raw}) + "\n")
    gen_seconds = time.time() - started

    if limit:
        raise SystemExit(f"--limit is for smoke tests only; samples written to {samples_path}, not scored")
    return {**score(dataset, samples_path), "generation_seconds": round(gen_seconds, 1)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--datasets", nargs="+", default=["humaneval", "mbpp"], choices=["humaneval", "mbpp"])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=768)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--limit", type=int, default=0, help="generate only the first N tasks (smoke test, not scored)")
    parser.add_argument("--score-only", action="store_true", help="rescore samples already in --out-dir")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    # Merge into an existing summary so datasets can be run separately.
    summary_path = args.out_dir / "summary.json"
    summary: dict[str, Any] = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    summary |= {"model": args.model, "adapter": args.adapter}
    model = tokenizer = None
    if not args.score_only:
        model, tokenizer = load_model(args.model, args.adapter)
    for dataset in args.datasets:
        if args.score_only:
            summary[dataset] = score(dataset, args.out_dir / f"{dataset}_samples.jsonl")
        else:
            summary[dataset] = run(model, tokenizer, dataset, args.out_dir, args.max_new_tokens, args.batch_size, args.limit)
        print(json.dumps({dataset: summary[dataset]}), flush=True)
    summary_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

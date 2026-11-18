"""Score a model on our spec problems at zero hints.

Reports, per model:
- spec pass rate: completions satisfying every spec property (headline metric);
- test pass rate: completions passing the original unit tests;
- mean property score: average fraction of rubric properties satisfied;
- subtly wrong: completions that pass the unit tests but violate the spec.

    python -m proofgrad.evaluate --model Qwen/Qwen2.5-Coder-0.5B-Instruct --problems data/problems.jsonl \
        --split test --out runs/base_eval.json [--adapter runs/grpo/final]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from proofgrad.prompts import extract_code
from proofgrad.verifier import verify_many


def pick_device() -> tuple[str, Any]:
    import torch

    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    if torch.backends.mps.is_available():
        return "mps", torch.bfloat16
    return "cpu", torch.float32


def load_problems(path: Path, split: str | None) -> list[dict[str, Any]]:
    problems = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [p for p in problems if split in (None, "all") or p["split"] == split]


def chat_prompt(tokenizer: Any, prompt: str, thinking: bool = False) -> str:
    # enable_thinking toggles Qwen3-style reasoning; other templates ignore it.
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True, enable_thinking=thinking
    )


# Qwen's suggested wording for ending reasoning early under a thinking budget.
FORCE_STOP = "\n\nConsidering the limited time, I have to give the solution based on the thinking directly now.\n"


def split_thinking(completion: str, thinking: bool) -> tuple[str, str]:
    """(reasoning, answer). In thinking mode an answer exists only after </think>;
    a trace cut off by the token limit has no answer."""
    if not thinking:
        return "", completion
    reasoning, closed, answer = completion.partition("</think>")
    return reasoning.removeprefix("<think>").strip(), answer if closed else ""


def load_model(model_name: str, adapter: str | None) -> tuple[Any, Any]:
    """Return (model, tokenizer) on the best device, with the LoRA adapter applied if given."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device, dtype = pick_device()
    tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype).to(device)
    if adapter:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return model, tokenizer


def generate(
    model_name: str, adapter: str | None, prompts: list[str], samples: int, max_new_tokens: int, batch_size: int,
    thinking: bool = False, temperature: float = 0.0, thinking_budget: int = 0,
) -> list[list[str]]:
    model, tokenizer = load_model(model_name, adapter)
    texts = [chat_prompt(tokenizer, p, thinking) for p in prompts]
    if thinking_budget:
        return generate_with_budget(model, tokenizer, texts, samples, thinking_budget, max_new_tokens, batch_size, temperature)
    return generate_from_texts(model, tokenizer, texts, samples, max_new_tokens, batch_size, temperature=temperature)


def generate_with_budget(
    model: Any, tokenizer: Any, texts: list[str], samples: int, budget: int, answer_tokens: int, batch_size: int, temperature: float
) -> list[list[str]]:
    """Thinking with a token budget: reason until </think> or ``budget`` tokens;
    traces still open are closed with FORCE_STOP, then the answer is generated
    (up to ``answer_tokens``). Returns ``<reasoning></think>\n\n<answer>``."""
    thoughts = generate_from_texts(model, tokenizer, texts, samples, budget, batch_size, ["</think>"], temperature)
    traces, prefixes = [], []
    for text, group in zip(texts, thoughts):
        for thought in group:
            closed = "</think>" in thought
            trace = thought.split("</think>")[0].rstrip() + ("" if closed else FORCE_STOP) + "</think>\n\n"
            traces.append(trace)
            prefixes.append(text + trace)
    answers = generate_from_texts(model, tokenizer, prefixes, 1, answer_tokens, batch_size, temperature=temperature)
    flat = [trace + answer for trace, (answer,) in zip(traces, answers)]
    return [flat[i : i + samples] for i in range(0, len(flat), samples)]


def generate_from_texts(
    model: Any, tokenizer: Any, texts: list[str], samples: int, max_new_tokens: int, batch_size: int,
    stop_strings: list[str] | None = None, temperature: float = 0.0,
) -> list[list[str]]:
    """Generate continuations of already chat-templated ``texts``.

    Greedy for a single sample at temperature 0; otherwise sampled (default 0.7)."""
    import torch

    if samples > 1 or temperature > 0:
        sampling = {"do_sample": True, "temperature": temperature or 0.7, "top_p": 0.95, "top_k": 20}
    else:
        sampling = {"do_sample": False}
    if stop_strings:
        sampling |= {"stop_strings": stop_strings, "tokenizer": tokenizer}
    def run(chunk: list[str]) -> list[str]:
        batch = tokenizer(chunk, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **batch, max_new_tokens=max_new_tokens, num_return_sequences=samples, pad_token_id=tokenizer.pad_token_id, **sampling
            )
        return tokenizer.batch_decode(generated[:, batch["input_ids"].shape[1] :], skip_special_tokens=True)

    outputs: list[list[str]] = []
    for start in range(0, len(texts), batch_size):
        chunk = texts[start : start + batch_size]
        try:
            decoded = run(chunk)
        except RuntimeError as err:  # torch.AcceleratorError subclasses RuntimeError
            # bf16 on MPS can yield NaN probabilities in heavily left-padded
            # batches; retry each prompt alone, i.e. without padding.
            if "probability tensor" not in str(err) or len(chunk) == 1:
                raise
            print(f"NaN probabilities in batch at {start}; retrying unpadded", flush=True)
            decoded = [d for text in chunk for d in run([text])]
        outputs.extend(decoded[i : i + samples] for i in range(0, len(decoded), samples))
        print(f"generated {min(start + batch_size, len(texts))}/{len(texts)}", flush=True)
    return outputs


def score(problems: list[dict[str, Any]], completions: list[list[str]], thinking: bool = False) -> dict[str, Any]:
    jobs, owners = [], []
    for problem, samples in zip(problems, completions):
        for completion in samples:
            jobs.append({
                "code": extract_code(split_thinking(completion, thinking)[1], problem["entry_point"]),
                "entry_point": problem["entry_point"],
                "spec": problem["spec"],
                "unit_tests": problem["unit_tests"],
            })
            owners.append(problem["id"])
    verdicts = verify_many(jobs)
    # Problems prepared by proofgrad.judge also carry a thin test suite and the independent judge.
    extra: dict[str, list[bool]] = {}
    for name, column in (("thin_passed", "thin_tests"), ("judge_passed", "judge_tests")):
        if problems and column in problems[0]:
            by_id = {p["id"]: p[column] for p in problems}
            checks = verify_many(
                {"code": job["code"], "entry_point": job["entry_point"], "unit_tests": by_id[owner]} for job, owner in zip(jobs, owners)
            )
            extra[name] = [v.tests_passed for v in checks]

    records = [
        {
            "id": owner,
            "spec_passed": v.spec_passed,
            "tests_passed": v.tests_passed,
            "property_score": v.property_score,
            "failed": [c.name for c in v.failures()],
            "error": v.error,
            "completion": completion,
            **{name: values[index] for name, values in extra.items()},
            **({
                "thinking": split_thinking(completion, True)[0].replace(FORCE_STOP.strip(), "").rstrip(),
                "answered": "</think>" in completion,
                "forced_stop": FORCE_STOP.strip() in completion,
            } if thinking else {}),
        }
        for index, (owner, v, completion) in enumerate(zip(owners, verdicts, (c for s in completions for c in s)))
    ]
    n = len(records) or 1
    return {
        "n_problems": len(problems),
        "n_completions": len(records),
        "spec_pass_rate": sum(r["spec_passed"] for r in records) / n,
        "test_pass_rate": sum(r["tests_passed"] for r in records) / n,
        "mean_property_score": sum(r["property_score"] for r in records) / n,
        "subtly_wrong_rate": sum(r["tests_passed"] and not r["spec_passed"] for r in records) / n,
        **{name.replace("_passed", "_pass_rate"): sum(values) / n for name, values in extra.items()},
        **({
            "unfinished_thinking_rate": sum(not r["answered"] for r in records) / n,
            "forced_stop_rate": sum(r["forced_stop"] for r in records) / n,
        } if thinking else {}),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter", help="LoRA adapter directory from training")
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--split", default="test", choices=["train", "test", "all"])
    parser.add_argument("--samples", type=int, default=1, help="1 = greedy decoding")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--thinking", action="store_true", help="enable the model's reasoning mode (Qwen3 <think>)")
    parser.add_argument("--thinking-budget", type=int, default=0,
                        help="with --thinking: cap reasoning at N tokens, then force the answer (--max-new-tokens applies to the answer)")
    parser.add_argument("--temperature", type=float, default=0.0, help="0 = greedy for a single sample")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    problems = load_problems(args.problems, args.split)
    problems = problems[: args.limit] if args.limit else problems
    started = time.time()
    from transformers import set_seed

    set_seed(args.seed)
    completions = generate(
        args.model, args.adapter, [p["prompt"] for p in problems], args.samples, args.max_new_tokens, args.batch_size,
        thinking=args.thinking, temperature=args.temperature, thinking_budget=args.thinking_budget if args.thinking else 0,
    )
    report = {
        "model": args.model, "adapter": args.adapter, "split": args.split, "thinking": args.thinking,
        "temperature": args.temperature, "max_new_tokens": args.max_new_tokens, "thinking_budget": args.thinking_budget, **score(problems, completions, args.thinking),
    }
    report["seconds"] = round(time.time() - started, 1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    summary = {k: v for k, v in report.items() if k != "records"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

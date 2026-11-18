"""Supervised warmup on reference answers (LoRA), in one of two answer formats.

- ``code``: the reference solution in a code block (control).
- ``props``: the spec's property descriptions under ``Properties:``, then the
  reference solution. Teaches the "spec-first" format for H3; the warmup
  problems are the only ones whose spec the student ever sees.

    python -m proofgrad.sft --model models/Qwen3.5-0.8B --problems runs/h3/warmup.jsonl \
        --format props --output-dir runs/h3/sft_props
"""

from __future__ import annotations

import argparse
import ast
import json
import random
from pathlib import Path
from typing import Any

from proofgrad.evaluate import chat_prompt, pick_device
from proofgrad.prompts import spec_first_answer, spec_first_prompt


def property_descriptions(spec: str) -> list[str]:
    """The description string of every ``@prop("...")`` in a spec module, in order."""
    found = []
    for node in ast.parse(spec).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call) and getattr(decorator.func, "id", None) == "prop" and decorator.args
                and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str)
            ):
                found.append(decorator.args[0].value)
    return found


def example(problem: dict[str, Any], fmt: str) -> tuple[str, str]:
    """(student prompt, target answer) for one warmup problem."""
    code = problem["reference_solution"].strip()
    if fmt == "props":
        return spec_first_prompt(problem["prompt"]), spec_first_answer(property_descriptions(problem["spec"]), code)
    return problem["prompt"], f"```python\n{code}\n```"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--format", choices=["code", "props"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=1024, help="longer examples are skipped")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    set_seed(args.seed)
    device, dtype = pick_device()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    problems = [json.loads(line) for line in args.problems.read_text().splitlines() if line.strip()]
    batches = []
    for problem in problems:
        prompt, target = example(problem, args.format)
        prefix = tokenizer(chat_prompt(tokenizer, prompt), add_special_tokens=False)["input_ids"]
        answer = tokenizer(target + tokenizer.eos_token, add_special_tokens=False)["input_ids"]
        if len(prefix) + len(answer) <= args.max_tokens:
            # Loss on the answer only: -100 masks the prompt.
            batches.append((prefix + answer, [-100] * len(prefix) + answer))
    print(f"{len(batches)} of {len(problems)} examples within {args.max_tokens} tokens", flush=True)

    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(device)
    # Without checkpointing a 1,000-token example does not fit next to the weights on a 16 GB Mac.
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(
        r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.0, target_modules="all-linear", task_type="CAUSAL_LM",
    ))
    model.train()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.0)
    rng = random.Random(args.seed)
    step = 0
    for epoch in range(args.epochs):
        rng.shuffle(batches)
        total = 0.0
        for index, (ids, labels) in enumerate(batches, start=1):
            out = model(input_ids=torch.tensor([ids], device=device), labels=torch.tensor([labels], device=device))
            (out.loss / args.grad_accum).backward()
            total += out.loss.item()
            del out
            if index % args.grad_accum == 0 or index == len(batches):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                step += 1
                if device == "mps":
                    # Every new sequence length allocates new buffers; MPS keeps them all cached
                    # until the machine swaps and training slows to a crawl.
                    torch.mps.empty_cache()
            if index % 20 == 0 or index == len(batches):
                held = f", GPU memory {torch.mps.driver_allocated_memory() / 2**30:.1f} GB" if device == "mps" else ""
                print(f"epoch {epoch + 1} example {index}/{len(batches)} mean loss {total / index:.4f}{held}", flush=True)

    final = args.output_dir / "final"
    model.save_pretrained(str(final))
    (args.output_dir / "run_args.json").write_text(json.dumps({k: str(v) for k, v in vars(args).items()} | {"examples": len(batches), "optimizer_steps": step}, indent=2))
    print(f"saved adapter to {final}")


if __name__ == "__main__":
    main()

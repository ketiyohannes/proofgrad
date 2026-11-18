"""GRPO fine-tuning of a small coding model with verifier rewards (TRL + PEFT LoRA).

The student sees only the prompt. Each of ``--num-generations`` completions per
prompt is scored by the verifier and GRPO compares them within the group, so no
reward model is needed.

    # spec-rubric run (the experiment)
    python -m proofgrad.train_grpo --model Qwen/Qwen2.5-Coder-1.5B-Instruct --problems data/problems.jsonl \
        --reward spec --output-dir runs/spec
    # control run: same everything, reward = original unit tests
    python -m proofgrad.train_grpo ... --reward tests --output-dir runs/tests

On the RTX 4070 add ``--load-in-4bit`` (QLoRA) and optionally ``--use-vllm``.
``--monitor`` also logs the other rewards (weight 0) so you can watch for code
that passes the training reward but is wrong, e.g. ``--reward thin --monitor
spec judge``. ``--partial-credit 0`` trains on plain pass/fail.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from proofgrad.evaluate import load_problems, pick_device
from proofgrad.rewards import REWARD_COLUMNS, REWARDS, set_partial_credit


def build_dataset(problems: list[dict[str, Any]]) -> Any:
    from datasets import Dataset

    return Dataset.from_list([
        {
            "prompt": [{"role": "user", "content": p["prompt"]}],
            "id": p["id"],
            "entry_point": p["entry_point"],
            **{column: p[column] for column in REWARD_COLUMNS.values() if column in p},
        }
        for p in problems
    ])


def load_model(name: str, load_in_4bit: bool) -> Any:
    from transformers import AutoModelForCausalLM

    device, dtype = pick_device()
    kwargs: dict[str, Any] = {"dtype": dtype}
    if load_in_4bit:
        if device != "cuda":
            raise SystemExit("--load-in-4bit needs CUDA (bitsandbytes)")
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=dtype, bnb_4bit_use_double_quant=True
        )
        kwargs["device_map"] = {"": 0}
    model = AutoModelForCausalLM.from_pretrained(name, **kwargs)
    if not load_in_4bit:
        model = model.to(device)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--reward", choices=sorted(set(REWARDS) - {"judge"}), default="spec")
    parser.add_argument("--monitor", nargs="*", choices=sorted(REWARDS), metavar="REWARD",
                        help="also log these rewards with weight 0 (no names: every other reward the data supports)")
    parser.add_argument("--partial-credit", type=float, default=0.5, help="weight of fraction-passed in the reward; 0 = pass/fail")
    parser.add_argument("--mask-truncated", action="store_true", help="leave answers cut off at the token limit out of the loss")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--num-generations", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8, help="completions per device step; multiple of --num-generations")
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=5e-6)
    parser.add_argument("--beta", type=float, default=0.0, help="KL penalty; 0 skips the reference model")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--max-completion-length", type=int, default=512)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--use-vllm", action="store_true")
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--report-to", default="none", help="none, wandb or tensorboard")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--resume", action="store_true", help="continue from the newest checkpoint in --output-dir, if any")
    parser.add_argument("--init-adapter", type=Path, help="start from this LoRA adapter (e.g. an SFT warmup) instead of a fresh one")
    args = parser.parse_args()

    from peft import LoraConfig
    from transformers import AutoTokenizer
    from trl import GRPOConfig, GRPOTrainer

    problems = load_problems(args.problems, "train")
    if not problems:
        raise SystemExit(f"no train-split problems in {args.problems}")
    dataset = build_dataset(problems)

    set_partial_credit(args.partial_credit)
    available = [name for name, column in REWARD_COLUMNS.items() if column in problems[0]]
    if args.reward not in available:
        raise SystemExit(f"--reward {args.reward} needs the {REWARD_COLUMNS[args.reward]!r} field (see proofgrad.judge)")
    monitors = [] if args.monitor is None else (args.monitor or available)
    names = [args.reward] + [name for name in monitors if name != args.reward and name in available]
    reward_funcs = [REWARDS[name] for name in names]
    reward_weights = [1.0] + [0.0] * (len(names) - 1)

    device, _ = pick_device()
    config = GRPOConfig(
        output_dir=str(args.output_dir),
        max_steps=args.max_steps,
        learning_rate=args.lr,
        lr_scheduler_type="constant_with_warmup",
        warmup_steps=min(10, args.max_steps // 10),
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_generations=args.num_generations,
        max_completion_length=args.max_completion_length,
        temperature=args.temperature,
        beta=args.beta,
        mask_truncated_completions=args.mask_truncated,
        reward_weights=reward_weights,
        chat_template_kwargs={"enable_thinking": False},
        bf16=device in ("cuda", "mps"),
        gradient_checkpointing=device != "cpu",
        use_vllm=args.use_vllm,
        vllm_mode="colocate",
        logging_steps=1,
        log_completions=True,
        save_steps=args.save_steps,
        save_total_limit=3,
        report_to=args.report_to,
        seed=args.seed,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = load_model(args.model, args.load_in_4bit)
    peft_config = LoraConfig(
        r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.0, target_modules="all-linear", task_type="CAUSAL_LM",
    )
    if args.init_adapter:
        from peft import PeftModel

        model, peft_config = PeftModel.from_pretrained(model, str(args.init_adapter), is_trainable=True), None
    trainer = GRPOTrainer(
        model=model,
        reward_funcs=reward_funcs,
        args=config,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    trainer.train(resume_from_checkpoint=args.resume and any(args.output_dir.glob("checkpoint-*")))

    final = args.output_dir / "final"
    trainer.save_model(str(final))
    (args.output_dir / "run_args.json").write_text(json.dumps({k: str(v) for k, v in vars(args).items()}, indent=2))
    print(f"saved adapter to {final}")


if __name__ == "__main__":
    main()

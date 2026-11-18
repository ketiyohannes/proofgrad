# Experiment A: Step-by-Step Guide

Goal: test whether a hidden, property-based spec makes a better GRPO reward than
a thin example-test suite for a small coding model. The claim is split into
three gated hypotheses (H1 checker quality, H2 training effect, H3 reasoning)
with pass and stop conditions: see "Hypothesis (revised 2026-11-10)" in
`docs/handoff.md`.

Background and reasoning live in `docs/handoff.md`. This guide records the decisions
made since then and the exact steps to run. Where the two disagree on model
choice, this guide wins.

## Decisions so far

| Item | Decision |
|---|---|
| Method | Experiment A: the student writes plain code; the reward comes from hidden Hypothesis properties |
| Control | Same setup, but the reward is the fraction of 3-5 example unit tests passed |
| Student | `Qwen2.5-Coder-0.5B-Instruct` (MLX bf16 on the Mac, HF bf16 on the 4070) |
| Fallback / later student | `Qwen3.5-0.8B` or `Qwen2.5-Coder-1.5B-Instruct` |
| Reference | Not downloaded yet. Use a same-family model such as `Qwen2.5-Coder-7B-Instruct` 4-bit before benchmarking |
| Training precision | bf16 LoRA. No 4-bit training at this size |
| Final evaluation | Always zero hints |

## Step 0: Local setup (done)

Requirements: macOS on Apple Silicon, `uv`, roughly 2 GB free disk.

```bash
# Python env with mlx-lm (pyproject.toml already exists)
uv sync

# Student model (0.99 GB) into the Hugging Face cache
uv run hf download mlx-community/Qwen2.5-Coder-0.5B-Instruct-bf16
```

If a download is interrupted, do not resume it. The partial
`blobs/*.incomplete` file can contain empty, unwritten regions, so resuming
from its reported size can corrupt the model. Delete the `.incomplete` file,
download again, and check the checksum. The blob file name is its SHA-256:

```bash
shasum -a 256 ~/.cache/huggingface/hub/models--mlx-community--Qwen2.5-Coder-0.5B-Instruct-bf16/blobs/b514850795f9d051c503e59063112a9b5e59957aeef106850139c6eb2b00a7f3
```

## Step 1: Serve the student locally (done)

```bash
HF_HUB_OFFLINE=1 uv run mlx_lm.server \
  --model mlx-community/Qwen2.5-Coder-0.5B-Instruct-bf16 \
  --host 127.0.0.1 --port 8080
```

This serves an OpenAI-compatible API at `http://127.0.0.1:8080/v1`.

Smoke test:

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"mlx-community/Qwen2.5-Coder-0.5B-Instruct-bf16",
       "messages":[{"role":"user","content":"Write a Python function add(a, b). Reply with one python code block."}],
       "max_tokens":200,"temperature":0}' | jq -r '.choices[0].message.content'
```

## Step 2: Hand-write 20 seed problems

Use small pure functions over lists, strings, and integer math. Each problem
contains:

| Field | Purpose |
|---|---|
| `prompt` | Task in natural language plus the function signature. This is the only thing the student sees |
| `entry_point` | Function name the verifier imports |
| `properties` | Named Hypothesis checks plus input strategies. Each is tagged `core` (correctness) or `edge` (empty input, duplicates, bounds). This is the hidden spec |
| `reference` | A correct solution |
| `mutants` | 3-5 deliberately buggy versions: off-by-one, wrong comparison, missing empty case |
| `examples` | 3-5 plain example tests. Used only by the control run and the "subtly wrong" metric |

The seeds set the format and quality bar for generated problems.

## Step 3: Build the verifier

Input: a problem plus candidate code. Output: per-property pass/fail plus a
counterexample for each failure.

Requirements:
- Run candidate code in a separate subprocess with a hard timeout and no network.
- Check each property independently.
- Use fixed Hypothesis seeds and settings, so the same code always gets the same
  score.
- Treat parse errors, crashes, and timeouts as score 0. Never crash the caller.

Self-check that every problem must pass:
- `reference` passes every property.
- Every mutant fails at least one property.

## Step 4: Generate problems at scale

Use a frontier model via API, with the seeds as few-shot examples, to write about
1,500-3,000 candidate problems in the seed format. Expect 2-3x losses in
Steps 5-6. Re-estimate the loss rate from the seeds before paying for the full
batch.

## Step 5: Validate every problem

Keep a problem only if:
1. the reference passes all properties,
2. every mutant fails at least one property,
3. it is not a near-duplicate of another problem,
4. it does not overlap with HumanEval+ or MBPP+.

## Step 6: Baseline and difficulty filter

1. Sample 8 completions per problem from the base student (Step 1 server).
2. Score each completion with the verifier. A completion passes when it passes
   the full spec.
3. Training set: keep problems with a base pass rate of 20-60%. Problems outside
   that band give GRPO no learning signal.
4. Held-out set: use a wider band, 10-80%.
5. Split by problem family, so near-identical problems never appear on both sides.

Target sizes after filtering:

| Split | Problems | Why |
|---|---|---|
| Train | 300-1,000 | 300-500 for a first signal; about 1,000 guards against memorizing the set |
| Held-out | 200-300 | With 8 samples per problem, 200 problems detect about 5 pp and 300 detect about 4 pp (paired test, alpha 0.05, 80% power, simulated) |

## Step 7: Define the rewards

Spec reward (run A), starting definition:

```
if unparseable or crash or timeout: reward = 0
core = fraction of core properties passed
edge = fraction of edge properties passed
reward = 0.7 * core + 0.3 * edge * (core == 1)
```

Edge properties only count once all core properties pass. This blocks
degenerate answers such as `return []`, which satisfy edge properties without
being correct.

Control reward: fraction of the `examples` tests passed. Nothing else changes.

## Step 8: Train on the 4070 (WSL2 Ubuntu)

Desktop setup is described in `docs/handoff.md` under "Remote setup". Training uses
Unsloth Core or TRL `GRPOTrainer` with the verifier as a custom reward function.

Starting hyperparameters:

| Setting | Value |
|---|---|
| Model | `Qwen/Qwen2.5-Coder-0.5B-Instruct` (HF weights, not MLX) |
| Adapter | bf16 LoRA |
| Completions per prompt | 8 |
| Max new tokens | 512 |
| Temperature | 1.0 |
| KL beta | 0 or small |

Run order:
1. Run A with 3 seeds. Measure how much results vary between seeds.
2. If the between-seed spread is large (several pp), use 5 seeds per run.
3. Run the control with the same seed count, prompts, and compute.

## Step 9: Evaluate

Models: base, A (spec-trained), control (test-trained), and reference.

| Metric | Shows |
|---|---|
| Full-spec pass rate on held-out problems | Main correctness result |
| "Subtly wrong" rate: passes `examples` but fails the spec | Whether edge-case bugs went down |
| HumanEval+ and MBPP+ pass@1 | Transfer, and a check that nothing got worse |
| Gap closed = (trained - base) / (reference - base) | Progress toward the reference |

Use 8 samples per problem. Report mean and confidence interval across seeds.
Always evaluate with zero hints.

## Step 10: Decide

- **A beats the control** on held-out spec pass rate or subtly-wrong rate, by
  more than the seed variance, and does no worse on HumanEval+/MBPP+: the
  specs help. Next, run Experiment B (the student writes its own contracts and
  invariants), then scale the student up.
- **No difference:** use the mutant results to check whether the specs were
  actually stronger than the example tests, and whether the problems were too
  easy or too hard.
- **Tooling problems:** switch to the fallback student and rerun the same steps.

## Where each step runs

| Steps | Machine |
|---|---|
| 0-6 (setup, serving, problems, verifier, baseline) | Mac |
| 7-8 (rewards, GRPO training) | 4070 desktop, WSL2 |
| 9 (evaluation) | Mac or desktop |

## Status (2026-11-10)

Steps 2-10 were run once on the Mac with these deviations from this guide.
Results and the audit are in `docs/handoff.md`.

| Step | Planned | Done |
|---|---|---|
| 0-1 | `Qwen2.5-Coder-0.5B-Instruct` | `Qwen3.5-0.8B` (not a coder model) |
| 2, 4 | hand-written seeds, generated problems | KodCode-V1 problems with specs added: 190 accepted |
| 6 | keep train problems at 20-60% base pass rate; split by family | skipped: about 20% of training groups were in that band; split by id hash |
| 7 | spec reward with edge properties gated on core; control = 3-5 example tests | ungated `0.5 * fraction + 0.5 * all_passed`; control = full KodCode tests |
| 8 | 4070, 3 seeds | Mac, 1 seed, 240 updates |
| 9 | 200-300 held-out problems, 8 samples | 33 held-out problems, 1 greedy answer |

The next round follows the plan in this guide again, with the control changed
to 1-2 example tests and the gates from `docs/handoff.md` added before any training.

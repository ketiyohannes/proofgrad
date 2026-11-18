# proofgrad

Can a small coding model learn to write more correct code when it is trained
against a strict, hidden checker?

This repo trains Qwen3.5-0.8B with reinforcement learning (GRPO), using
property-based specs as the reward. The model never sees the spec: it gets a
task, writes plain Python, and is scored by whether the code obeys the spec.
The longer-term question is whether proof checkers (Dafny, Bend 2) can play
the same role.

Inspired by [Bend 2](https://github.com/HigherOrderCO/Bend), where every
change must come with a proof. Here the checker is training scaffolding only;
nothing is checked when the model is used.

## Status

Pilot results, one training run per model. Treat every gap as provisional
until it is repeated with more seeds.

**Are specs better checkers?** Share of wrong answers each checker accepts
(253 wrong answers from the untrained model):

| Checker | Wrong answers accepted |
|---|---|
| One example test | 20.6% |
| Full unit tests | 1.6% |
| Spec | 0.4% |

**Does training on the strict checker help?** Correct answers on 18 unseen
problems, judged by an independent referee:

| Model | Correct |
|---|---|
| Untrained | 41.0% |
| Trained on one example test | 56.2% |
| Trained on the spec | 72.2% |

The spec model leads the one-test model by 16.0 points (95% interval 6.2 to
26.4).

**Does stating the rules before the code help?** The model lists the rules in
every answer, but passing and failing answers list the same rules, so the
list does not act as reasoning.

**Open problem.** Two runs of nearly the same recipe scored 72% and 47% on
the same unseen problems. Seed variance has not been measured yet.

Start with [docs/explainer.md](docs/explainer.md) for the full story in plain
language.

## Layout

| Path | Contents |
|---|---|
| `src/proofgrad/` | Dataset building, verifier, rewards, training, evaluation, analysis |
| `scripts/` | Drivers for each experiment |
| `tests/` | Pipeline tests |
| `data/` | Problems with specs (`problems_full.jsonl`) and the spec sources (`specs/`) |
| `runs/` | Results of every experiment: samples, scores, reports |
| `docs/explainer.md` | Plain-language account of the whole project |
| `docs/handoff.md` | Full technical record: design, environment notes, results |
| `docs/guide.md` | Step-by-step guide for the first experiment |
| `docs/experiment-design.md` | Design for the next experiment: proof-based training against SFT and RLHF |

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run hf download Qwen/Qwen3.5-0.8B --local-dir models/Qwen3.5-0.8B
uv run pytest
```

The HumanEval+ and MBPP+ benchmark needs EvalPlus, installed outside the lock
file (see the docstring of `src/proofgrad/benchmark.py`). Because of that, run
project commands with `uv run --no-sync`; a plain `uv sync` removes EvalPlus.

## Reproducing the experiments

Everything so far ran on a 16 GB Apple M4. On macOS, keep the display awake
during training, or GPU jobs stall while it sleeps.

```bash
# Step 2: spec reward against a one-test reward
caffeinate -d -i bash scripts/small_experiment.sh

# Step 3: rules stated before the code
caffeinate -d -i bash scripts/h3_experiment.sh
```

Each script skips stages whose output already exists. Step 1, which selects
the problems, is run by hand; the commands are at the top of
`scripts/small_experiment.sh`.

## Trained adapters

The LoRA adapters, training logs and sampled training answers are on Hugging
Face: [ketiyohannes/proofgrad-qwen3.5-0.8b-lora](https://huggingface.co/ketiyohannes/proofgrad-qwen3.5-0.8b-lora).
The layout there mirrors `runs/`, so this restores them in place:

```bash
uv run hf download ketiyohannes/proofgrad-qwen3.5-0.8b-lora --local-dir runs
```

## Data and licences

- Problems, reference solutions and unit tests come from
  [KodCode-V1](https://huggingface.co/datasets/KodCode/KodCode-V1), licensed
  CC BY-NC 4.0. The files under `data/` and the problem sets under `runs/`
  are derived from it and carry the same licence.
- The specs in `data/specs/` were written for this project with an LLM and
  checked against each reference solution.
- The base model, [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B),
  is licensed Apache 2.0.

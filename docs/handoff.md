# Proof Fine-Tuning: Handoff

Status (2026-11-11): the first full experiment (190 problems, spec reward vs
full-unit-test control) showed no advantage, and an audit showed it could not
have. The hypothesis was rewritten (next section) and tested on a small scale:
H1 passed, and in a 20-problem H2 pilot the spec-reward arm beat the
one-example-test arm by 16 points of judge pass rate on 18 unseen problems
(one seed). An H3 pilot (properties stated before the code) gave a mixed
result and showed that single runs differ by 25 points on unseen problems, so
seeds come first. See "Small gated experiment", "H3 pilot" and "Next steps".

## The idea in one paragraph

Use formal specs (laws/proofs) as a hidden rubric to train a small coding model.
A strong model (or a strong human) writes a prompt plus a formal spec. The small
student model only sees the prompt and writes ordinary code. A verifier checks
the code against the spec, and the result becomes the reward for RL (plus an
optional SFT warmup). Proofs are training scaffolding only: the end goal is a
model that writes more correct code WITHOUT needing proofs at inference time
(unlike Bend 2, which requires a proof for every change).

Inspiration: Bend 2 (https://github.com/bendlang/bend), "a fast language that
blocks AI mistakes via proof". Human writes LAWS.bend, AI writes code + PROOF.bend,
`bend PROOF.bend` is the gate.

## Hypothesis (revised 2026-11-10)

The first version was "a spec reward makes a small model a better general
coder than a unit-test reward, visible on HumanEval+/MBPP+". It was not
testable as run: the control's tests were as strong as the specs, the outcome
(benchmark transfer) was far from the mechanism, and it stated no effect size
or failure condition. It also mixed two claims: specs are better checkers, and
per-property partial credit is a better learning signal. The audit found
evidence against the second (partial credit mostly ranked wrong answers).

Replacement: three claims, tested in order, each with a stop condition.
"Judge" means full KodCode tests plus differential testing against the
reference solution on generated inputs. The judge is never used as a reward,
so no arm grades itself.

- **H1, checker quality (no training).** On answers sampled from the base
  model, a thin test suite (1-2 example tests, the normal case outside curated
  datasets) accepts many answers the judge rejects; the spec accepts few.
  Pass: thin-test false accepts >= 15% of wrong answers and spec false accepts
  <= 5%, with a by-problem bootstrap interval that excludes equality.
  Stop: the spec is not at least 10 points better than thin tests.
  First look (198 saved completions, 33 problems, spec is half of that judge,
  so directional only): first 1 / 2 / 3 tests accept 25% / 8% / 5% of wrong
  answers, full tests 2.6%, spec 0%.
- **H2, training effect.** GRPO on a reward that accepts wrong answers teaches
  the model to write them. Arms: spec reward vs thin-test reward, same prompts
  and compute. Primary metric: judge pass rate on held-out problems, from
  sampled answers. Secondary: subtly-wrong rate (passes thin tests, fails the
  judge). Pass: spec arm beats the thin-test arm by >= 5 points, interval
  excludes 0 and the gap exceeds the spread between seeds. Stop: gap under 2
  points or inside the seed spread, which would mean false accepts do not
  matter at this scale.
- **H3, reasoning (deferred).** A model trained with thinking on, after an SFT
  warmup on spec-then-code traces, states properties before coding and that
  correlates with passing. Only after H2 passes, on a model that finishes its
  thinking (0.8B does not: 73-79% of traces hit the token budget).

No longer part of the hypothesis: HumanEval+/MBPP+ gains. They stay as a
guard (no arm may lose more than 3 points against base).

Conditions every H2 run must meet (each one failed in the full run):

| Condition | Full run | Requirement |
|---|---|---|
| Control weaker than the spec | full suites, median 6 tests | 1-2 example tests |
| Problems the student can sometimes solve | 20% of groups in the 20-60% band | train only on that band |
| Signal from right-vs-wrong, not wrong-vs-wrong | 55-61% of advantage from groups with no correct answer | gate or shrink partial credit, no per-group std scaling |
| Answers not cut off | 20% hit 512 tokens, scored ~0 | 1,024 tokens or mask truncated answers |
| Enough updates | 240 updates of 1 problem each | >= 1,000 updates of >= 4 problems |
| Held-out split independent | 5 task names in both splits | split by task family |
| Measurement power | 33 problems x 1 greedy answer, 1 seed | >= 100 problems x 8 samples, 3 seeds |

## Experiment design

### Data
- Each example: `prompt` (natural language task), `spec` (formal properties),
  `reference_solution` (teacher code that provably/verifiably passes the spec).
- The reference solution is there to prove the spec is satisfiable and not buggy.
- Target size for a first signal: a few hundred to ~1,000 problems.
- Spec writer: a frontier model via API (e.g. Fable 5.1). This is the only
  part that costs money.

### Spec as a rubric
- Split each spec into independent properties, e.g. "output is sorted",
  "output is a permutation of the input", "doesn't crash on empty input".
- Each property is checked separately, which gives partial credit instead of
  a flat pass/fail (fixes the sparse reward problem).

### Training loop
1. Optional SFT warmup on some teacher-verified solutions.
2. RL with GRPO: student generates several attempts per prompt, verifier
   scores each rubric property, scores become rewards. GRPO compares attempts
   against each other, so no separate reward model is needed.

### Hint ladder (proof steps revealed gradually)
- Break each proof into steps (e.g. Dafny loop invariants, intermediate
  asserts, helper lemmas; Bend `%` rewrite lines).
- As an EVALUATION: reveal steps one at a time until the model succeeds.
  "Hints needed" is a richer score than pass/fail. Plot accuracy vs. hints
  revealed for base student, fine-tuned student, and the reference model.
- As TRAINING: reverse curriculum. Start with most of the proof shown, hide
  more as the model improves, end at zero hints. Reward success with fewer
  hints more highly.
- Watch out: hints can leak the solution (loop invariants often describe the
  algorithm). Hints should give direction, not answers.
- Final evaluation is ALWAYS at zero hints.

### Evaluation (benchmark twice + reference)
- Run the same benchmarks on: (1) original student, (2) fine-tuned student,
  (3) a stronger reference model.
- Headline metric, gap closed:
  `(finetuned - base) / (reference - base)`
  e.g. base 30%, reference 70%, fine-tuned 50% -> closed half the gap.
- Use benchmarks the model never trained on: HumanEval+, MBPP+, LiveCodeBench,
  plus a held-out slice of our own spec problems.
- Control run: same student, same prompts and compute, but reward = ordinary
  unit tests only. If spec-trained beats test-trained, the specs did something.
- Extra metric: how often code passes visible tests but violates the spec on
  edge cases ("subtly wrong"). Reducing this is the most interesting possible
  result.
- Open question: should the reference model be the same model that wrote the
  specs, or a different one? Different avoids the student just learning the
  spec writer's style.

## Verifier options (cheapest first)

1. **Python + Hypothesis** (property-based testing). Not a proof, but fast,
   free, and gives concrete counterexamples. START HERE.
2. **CrossHair**: checks Python contracts with an SMT solver. Stronger than
   random testing, still not a full proof.
3. **Dafny**: real formal verification with an SMT solver; natural hint steps
   (invariants, asserts, lemmas).
4. **Bend 2**: real proofs, but no tactics or proof search, so proofs are
   long and manual. Models have seen very little Bend 2 in pretraining.
   Try only after the pipeline works.

## Models

| Role | Pick | Notes |
|---|---|---|
| Student (recommended) | Qwen2.5-Coder-1.5B-Instruct | Well-studied, lots of headroom, fits 4070 for QLoRA + GRPO |
| Student (modern) | Qwen3.5-2B | Base versions available |
| Student (cheapest, for pipeline testing) | Qwen3.5-0.8B | |
| Reference | Qwen2.5-Coder-7B or Qwen3.5-9B (4-bit) | Same family as student keeps comparison fair; benchmark only, no training |
| Spec writer | Frontier model via API | |
| Avoid as student | VibeThinker | Already heavily RL-trained on verifiable rewards, little headroom |

Use the 4-bit reference consistently in all comparisons.

Rough VRAM (estimates; depends on context length, batch size, GRPO samples):
- 1.5B: ~1.5 GB run (4-bit), ~6-10 GB train (QLoRA + GRPO)
- 2B: ~2 GB run, ~8-11 GB train
- 3B: ~2.5 GB run, ~10-14 GB train (tight on 12 GB)
- 7B: ~5 GB run (4-bit), ~24 GB train
- 9B: ~6-7 GB run (4-bit), 24-40 GB train

## Hardware and setup

- **Desktop (Windows) with RTX 4070, 12 GB**: does the GRPO training. Run
  everything inside WSL2 Ubuntu (Unsloth, bitsandbytes, vLLM, Bend all want
  Linux).
- **GTX 1650, 4 GB**: quick 4-bit inference tests of tiny models only, no
  training.
- **M4 MacBook Pro, 16 GB**: control center. Write specs and code, run the
  verifier (CPU), quick MLX inference/benchmarks and small SFT experiments
  with `mlx-lm`. GRPO on Mac is immature and slower (lower memory bandwidth).

### Remote setup (control the desktop from the Mac)
1. `wsl --install -d Ubuntu` (admin PowerShell). NVIDIA driver on Windows
   only; check `nvidia-smi` inside WSL.
2. Enable systemd in `/etc/wsl.conf`:
   ```
   [boot]
   systemd=true
   ```
   then `wsl --shutdown` and reopen.
3. Inside Ubuntu: `sudo apt install openssh-server`,
   `sudo systemctl enable --now ssh`, install Tailscale and `sudo tailscale up`.
   Install Tailscale on the Mac too. `ssh-copy-id` for key login.
4. Connect with VS Code / Cursor Remote-SSH.
5. Run training inside `tmux`. Monitor with Weights & Biases or TensorBoard.
6. Gotchas: Windows power plan must never sleep; WSL doesn't auto-start after
   reboot (Task Scheduler task running `wsl.exe -d Ubuntu` at startup).

### Unsloth
- Studio (web UI) inside WSL:
  `curl -fsSL https://unsloth.ai/install.sh | sh`
  then `unsloth studio -H 0.0.0.0 -p 8888`, open via Tailscale address from
  the Mac. Never expose the port publicly.
- Good for SFT warmups and quick model tests.
- GRPO with a custom verifier reward most likely needs Unsloth Core (Python +
  TRL): `uv pip install unsloth vllm --torch-backend=auto`. Verify current
  Studio support for custom reward functions before relying on it.

### Bend 2
- Install: `curl -fsSL https://bend-lang.com/install.sh | sh`
- `bend guide` prints the full language guide.
- No Windows; WSL and macOS work.

## Reference examples

### Python + Hypothesis rubric
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers(), min_size=1))
def test_max(xs):
    m = my_max(xs)
    assert all(x <= m for x in xs)  # rubric item 1
    assert m in xs                  # rubric item 2
```

### Dafny (spec + code + proof steps)
```dafny
method Max(a: array<int>) returns (m: int)
  requires a.Length > 0
  ensures forall i :: 0 <= i < a.Length ==> a[i] <= m
  ensures exists i :: 0 <= i < a.Length && a[i] == m
{
  m := a[0];
  var j := 1;
  while j < a.Length
    invariant 1 <= j <= a.Length
    invariant forall i :: 0 <= i < j ==> a[i] <= m
    invariant exists i :: 0 <= i < j && a[i] == m
  {
    if a[j] > m { m := a[j]; }
    j := j + 1;
  }
}
```
The three invariants are the "proof steps" for the hint ladder.

### Bend 2 (law + proof, from the official README)
```python
law add_zero:
  for x: Nat
  {Nat.add(x, 0n) == x : Nat}

def add_zero(x):
  match x:
    case 0n:
      {==}
    case 1n+xp:
      %add_zero(xp) : {1n+Nat.add(xp, 0n) == 1n+_ : Nat}
      {==}
```

## What is built (2026-11-08)

Code lives in `src/proofgrad/`; run everything with `uv run` from the repo root.

| Module | Role |
|---|---|
| `kodcode.py` | Selects spec-friendly problems from KodCode-V1 (pure single function, stdlib only, easy/medium, benchmark similarity < 0.8). |
| `spec_runtime.py` | `@prop(description, **strategies)`: the spec format. One property = one rubric item. |
| `verifier.py`, `_runner.py` | Runs candidate code in a subprocess (timeouts, rlimits, stripped env) against spec properties and/or unit tests; per-item pass/fail. Not a security sandbox. |
| `mutants.py` | AST mutants of the reference, to measure whether a spec actually rejects wrong code. |
| `build.py` | Our dataset standard (see below); writes `data/problems.jsonl` + `.rejected.jsonl`. |
| `spec_writer.py` | Drafts specs with Claude via the Message Batches API (`submit`, `collect`, `submit --repair`). Needs `ANTHROPIC_API_KEY`. Default model `claude-opus-5-5`; `--model claude-fable-5-1` to match the original plan. |
| `rewards.py` | GRPO rewards: `0.5 * fraction_passed + 0.5 * all_passed`, for spec rubric (`spec`) and unit-test control (`tests`). Cached per completion. |
| `train_grpo.py` | TRL GRPO + LoRA. `--reward spec|tests`, `--monitor` logs the other reward at weight 0, `--load-in-4bit` / `--use-vllm` for the 4070. |
| `evaluate.py` | Zero-hint eval: spec pass rate, test pass rate, mean property score, subtly-wrong rate. Accepts `--adapter`. |
| `benchmark.py` | EvalPlus HumanEval+/MBPP+ (instruct prompt, greedy pass@1, `--score-only` to rescore). |
| `report.py` | Self-contained HTML chart: benchmark and held-out columns per model, training reward/length lines from TRL logs. |
| `traces.py` | Side-by-side HTML viewer and marker statistics for thinking-mode reasoning traces. |
| `audit.py` | Post-run checks from artifacts on disk: training signal per group, reward earned by junk stubs, split leakage, thin-test false accepts. |
| `judge.py` | Adds to each problem the thin tests (first k test functions) and the judge (full tests + differential test against the reference on inputs recorded from the spec's generators). |
| `experiment.py` | Gated experiment: `h1` (false accepts per checker), `select` (train/unseen problems in a base pass-rate band, task families kept on one side), `h2` (arms compared with by-problem bootstrap intervals). |
| `scripts/small_experiment.sh` | Step 2 driver: trains the spec and thin arms, samples base/spec/thin, runs `h2`. Resumable. |
| `sft.py` | Supervised LoRA warmup on reference answers, format `code` or `props` (the spec's property descriptions, then the code). |
| `scripts/h3_experiment.sh` | H3 pilot driver: warmup x2, spec GRPO from each warmup (`train_grpo --init-adapter`), sampling, `h2` + `h3`. Resumable. |

### Dataset: KodCode-V1 fixed to our standard
Source: https://huggingface.co/datasets/KodCode/KodCode-V1 (CC-BY-NC-4.0, fine
for personal research). It already has question, verified reference, pytest
unit tests (these become the control-run reward). A problem enters
`data/problems.jsonl` only if:
1. the spec has >= 2 independent properties and the right `ENTRY_POINT`;
2. the reference passes every property at 500 examples and all unit tests;
3. the spec misses <= 10% of the mutants the unit tests kill (problems with
   < 5 mutants are flagged `weakly_validated`);
4. the spec writer did not set `EXCLUDE_REASON` (reference contradicts the
   statement);
5. any convention the spec checks but the question leaves implicit is listed in
   the spec's `CLARIFICATIONS`, which are appended to the student prompt, so
   the student is never graded on behavior it could not know about.
Held-out split: 20% by hash of id.

### Smoke-test results (Mac, M4 16 GB)
- Shard 0 of KodCode (32k rows) yields 14,289 eligible problems; 200 sampled
  into `data/candidates.jsonl`.
- 25 specs written (by Claude subagents following `spec_writer.SYSTEM_PROMPT`;
  the prompt was revised from their feedback). 24 accepted, 1 excluded (wrong
  reference). Specs kill 436/479 mutants vs. 415 for unit tests, 0 missed, 21
  caught only by specs.
- Base Qwen3.5-0.8B (greedy, 512 tokens, all 24): spec pass 16.7%, mean
  property score 0.40. Partial credit is much denser than pass/fail.
- GRPO, 3 steps (4 generations, LoRA r=16): ~20 s/step on MPS, adapter saved
  and evaluated (20.8% / 0.445; three steps on mostly-train problems, so this
  is noise, not a result). In step 1 every completion failed all unit tests but
  the spec rubric still gave a non-zero advantage: the dense-reward argument,
  observed.
- Lessons: max completion length 256 truncates most answers (zero signal);
  use >= 512. On MPS, keep per-device batch at 2 with gradient checkpointing
  (batch 4 hit the 18 GB MPS limit). Qwen3.5 uses fallback kernels without
  `flash-linear-attention` (install it on the 4070).

### Longer run + HumanEval+ benchmark (Mac)
- GRPO, 60 steps on the 21 train problems (8 generations, 512 tokens, LoRA
  r=16, lr 1e-5, spec reward): 65 min on MPS. Adapter: `runs/long/grpo/final`.
- HumanEval+ via EvalPlus (`proofgrad.benchmark`, EvalPlus instruct prompt,
  greedy, 512 tokens), Qwen3.5-0.8B:

  | | HumanEval | HumanEval+ | MBPP | MBPP+ |
  |---|---|---|---|---|
  | base | 32.9% | 29.9% (49/164) | 28.0% | 24.3% (92/378) |
  | + spec-GRPO adapter | 38.4% | 34.1% (56/164) | 30.2% | 25.9% (98/378) |

  Paired: HumanEval+ 18 gained / 11 lost (p = 0.27), MBPP+ 21 / 15 (p = 0.41),
  combined 39 / 26 (exact McNemar p = 0.14): consistent direction, not
  statistically significant. No formatting failures in either run;
  fine-tuned answers are ~15% shorter. Not yet compared against a unit-test
  control run, so the gain cannot be attributed to specs specifically.
- EvalPlus is installed with `--no-deps` (see `benchmark.py` docstring); on
  macOS its memory rlimit must be disabled (`benchmark.py` does this).

### Full run: spec reward vs unit-test control (2026-11-09, Mac)
- Dataset `data/problems_full.jsonl`: 200 KodCode candidates, specs by Claude
  subagents, 190 accepted (157 train / 33 test, 19 weakly validated). Mutants
  3,463: specs kill 3,231, unit tests 3,104, specs miss 0 that tests kill, 127
  caught only by specs.
- Two LoRA runs on Qwen3.5-0.8B, identical except `--reward spec` vs
  `--reward tests` (240 steps = ~1.5 passes over the 157 train problems, 8
  generations, batch 2 x grad-accum 4, lr 1e-5, 512 tokens, both `--monitor`).
  ~4 h (spec) and ~3.5 h (tests) on MPS. Driver: `scripts/full_run.sh`
  (resumable); outputs in `runs/full/`, `runs/bench/full_{spec,tests}/`.
- Chart: `runs/report_full.html` (`bash scripts/render_full_report.sh`).

  EvalPlus, greedy pass@1:

  | | HumanEval | HumanEval+ | MBPP | MBPP+ | HE+ & MBPP+ combined |
  |---|---|---|---|---|---|
  | base | 32.9% | 29.9% | 28.0% | 24.3% | 26.0% |
  | spec GRPO | 33.5% | 30.5% | 29.6% | 24.6% | 26.4% |
  | unit-test GRPO (control) | 29.9% | 26.2% | 33.9% | 29.6% | 28.6% |
  | (PoC, 60 steps, spec) | 38.4% | 34.1% | 30.2% | 25.9% | 28.4% |

  Exact McNemar on the + metrics: spec vs base p = 1.00 (HE+), 1.00 (MBPP+);
  control vs base p = 0.41 (HE+, down), 0.013 (MBPP+, up 40 / 20); spec vs
  control on MBPP+ p = 0.020 (control better); combined spec vs control
  p = 0.26.

  Held-out split (33 problems, greedy):

  | | all spec props | unit tests | mean property score | subtly wrong |
  |---|---|---|---|---|
  | base | 6/33 | 7/33 | 0.357 | 1 |
  | spec GRPO | 8/33 | 8/33 | 0.457 | 0 |
  | unit-test GRPO | 6/33 | 7/33 | 0.447 | 1 |

  No held-out difference is significant (smallest p = 0.50).
- Reading:
  1. The two rewards barely differ on this data: per completion they
     correlate at 0.94 and are exactly equal on ~49% of completions. KodCode's
     unit tests are already strong (specs add only 127 of 3,463 mutant kills,
     3.7%), so the experiment has little room to separate them.
  2. Neither run gives a reliable benchmark gain. The PoC's +2.4 pts did not
     reproduce with more data and steps, so treat +-2-3 pts as noise.
  3. The control learned to be terse (mean completion 300 -> 92 tokens, fewer
     docstrings); the spec run did not (~270-300 tokens). The control's MBPP+
     gain coincides with that shift; truncation at 512 tokens explains only 3
     of its 40 gains, so the cause is not settled. Its HumanEval dropped.
  4. Training reward did not clearly rise for either run beyond problem
     difficulty; the second pass (step 158+) is higher for both, which is
     memorization of seen problems, not generalization.

### Thinking-mode eval (2026-11-09, Mac)
- Same three models on the 33 held-out problems with thinking on (budget
  2,048 tokens, then a forced answer; temperature 0.6). Driver:
  `scripts/thinking_eval.sh`; viewer: `runs/thinking/traces.html`.
- Spec pass base / spec / tests: 6 / 8 / 8 with thinking, 6 / 8 / 6 without.
  Thinking does not help at this size.
- 73-79% of traces hit the budget (looping "Wait, I made an error"). Traces
  that finish pass about half the time, forced ones about 11%.
- Traces are not spec-like for any model: about 2 property-style phrases per
  trace in all three. Training with thinking off did not change how the model
  reasons.

### Audit: why the full run could not show an effect (2026-11-10)
Reproduce with `python -m proofgrad.audit` (usage in its docstring). All
numbers come from artifacts already on disk.

1. **The problems were too hard for the student.** In 63% (spec run) and 55%
   (control) of training groups none of the 8 answers was correct. Only about
   20% of groups were in the 20-60% band where GRPO can compare right with
   wrong. GUIDE step 6 (difficulty filter) was skipped. Of problems visited
   twice, 38 of 63 (spec) and 30 of 63 (control) were never solved either time.
2. **More than half of the gradient ranked wrong answers against each other.**
   Groups with no correct answer still produced 61% (spec) and 55% (control)
   of the total advantage, because TRL's default `scale_rewards="group"`
   divides by the group's standard deviation: a 0.05 difference in partial
   credit becomes a full-size advantage.
3. **Partial credit pays for junk.** The best trivial stub per problem
   (`return []`, `return False`, ...) earns 0.18 mean spec reward and 0.15
   test reward. Wrong answers in training averaged 0.08-0.11. GUIDE step 7
   gated edge properties on core ones to prevent this; `rewards.py` does not.
4. **Truncation rewarded brevity, not correctness.** 20% of early answers hit
   the 512-token limit and scored about 0 (`mask_truncated_completions` is
   off by default). The control escaped by getting short: length 306 -> 106
   tokens, entropy 0.61 -> 0.19. That is a collapse in diversity, and it
   coincides with its MBPP+ change.
5. **Capability did not move.** The share of groups with no correct answer
   was the same in the second pass as in the first (63% vs 64% spec, 57% vs
   55% control). 240 updates of one problem each at lr 1e-5 is too little.
6. **Held-out leakage.** The split is by id hash, and 5 task names (`trap`,
   `maxProfit`, `num_islands`, `is_palindrome`,
   `length_of_longest_substring`) appear in both splits: at least 5 of the 33
   held-out problems have a near-duplicate in train.
7. **The control was not the planned control.** GUIDE specifies 3-5 example
   tests; the run used the full KodCode suites, which are as strong as the
   specs. On 3,840 training answers, 8.5% of test-passing answers fail the
   spec and 1.8% of spec-passing answers fail the tests.
8. **Some "spec-only" failures are conventions, not bugs.** 177 of 190
   problems carry clarifications taken from the reference's behavior. One
   problem (`isPerfect`, "0" does not count as a square) gives 19 of the 59
   tests-pass/spec-fail answers. Count these separately from real errors.
9. **Verifier is sound.** All 190 references pass spec and tests at
   reward-time settings (100 examples, 5 s), twice in a row.

### Small gated experiment (2026-11-10/11, Mac)

Everything is in `runs/small/`. Rewards were pass/fail (`--partial-credit 0`),
answers of 768 tokens, cut-off answers masked, 8 samples per problem.

**H1 (checker quality, no training): passed.** 51 problems the base model
sometimes solves, 408 answers, 253 wrong by the judge.

| Checker | Wrong answers accepted | 95% interval |
|---|---|---|
| First example test | 20.6% | 13.9-28.4% |
| Full unit tests | 1.6% | 0.4-3.1% |
| Spec | 0.4% | 0-1.3% |

Thin minus spec: 20.2 points (13.5-28.0). The spec rejected 2 of 155 correct
answers, both on `Leetcode_5219_I` (`too_large_k_raises`). No answer passed
spec and full tests but failed the judge.

**H2 pilot (training): passed on one seed.** 20 train + 18 unseen problems
(base pass rate 1/8-7/8, no shared entry points or task families), 120 updates
per arm (6 passes), one problem per update, lr 2e-5. Judge pass rate, 8
samples per problem at temperature 1.0, fresh seed:

| Split | Base | Thin-test reward | Spec reward | Spec minus thin (95% interval) |
|---|---|---|---|---|
| 18 unseen problems | 41.0% | 56.2% | 72.2% | +16.0 (6.2 to 26.4) |
| 20 training problems | 40.6% | 58.8% | 79.4% | +20.6 (8.1 to 34.4) |

- Unseen problems: spec arm better on 12, thin arm better on 2, tie on 4.
- Scored with the full unit tests alone (no spec generators involved), spec
  minus thin on unseen problems is +15.3 (4.9 to 25.7).
- Answers that pass the example test but are wrong, unseen problems: base
  15.3%, thin 11.8%, spec 6.2%. Spec minus thin is -5.6 (-13.9 to 2.8), not
  yet separable from zero.
- During training the judge pass rate on training problems rose from 21% to
  69% (spec arm) and 18% to 49% (thin arm), first 20 vs last 20 updates.
- Spec-arm answers grew longer: 24% hit 768 tokens in the last 20 updates.

Limits: one seed per arm, 18 unseen problems from the same source as the
training problems, problems chosen as ones the base model sometimes solves,
HumanEval+/MBPP+ guard not run. The seed-spread condition of H2 is untested.

### H3 pilot: properties stated before the code (2026-11-11, Mac)

Everything is in `runs/h3/`. Native thinking is unusable at 0.8B, so the
"spec-first" format is plain text with thinking off: the prompt asks for a
`Properties:` list, then the code (`prompts.spec_first_prompt`). Only the code
is graded. 2 x 2: answer format (code only | properties first) x training
(SFT warmup | warmup + spec GRPO, 120 updates, same settings as the H2 pilot).
Warmup: 141 problems outside the 38 evaluated ones, 3 epochs, lr 1e-4; targets
are the reference solution, preceded in the `props` format by the spec's
property descriptions. Judge pass rate, 8 samples per problem:

| Arm | 18 unseen | 20 GRPO-train |
|---|---|---|
| Base (from the H2 pilot) | 41.0% | 40.6% |
| Spec GRPO, no warmup (H2 pilot) | 72.2% | 79.4% |
| Warmup, code only | 49.3% | 43.8% |
| Warmup, properties first | 46.5% | 31.9% |
| Warmup + spec GRPO, code only | 47.2% | 80.0% |
| Warmup + spec GRPO, properties first | 68.8% | 73.8% |

- After warmup only, properties-first is not better: -7.6 points over all 38
  problems (-15.5 to +1.3); code-only better on 23 problems, worse on 9.
- After spec GRPO, properties-first beats code-only on unseen problems by
  21.5 points (7.6 to 35.4; better on 11, worse on 3, tie 4), and is level on
  the training problems (-6.2, -21.3 to +10.6).
- The code-only arm learned its training problems (43.8% to 80.0%) and gained
  nothing on unseen ones (49.3% to 47.2%). The H2-pilot spec arm, also code
  only but without a warmup, reached 72.2% on the same unseen problems. So two
  code-only spec-reward runs differ by 25 points on unseen problems; whether
  the warmup or run-to-run variance causes it is unknown. This is the size of
  effect the H2 pilot's "+16 over thin tests" must be compared with.
- The stated properties: every answer has them; 5.2 per answer after warmup,
  3.5 after GRPO (they are not rewarded). Task-specific (1-2% of lines recur
  across 3+ problems). Not tied to passing: passing and failing answers state
  the same number, and word overlap with the hidden spec is the same for both
  (0.31 vs 0.30 after GRPO, 0.37 vs 0.35 after warmup). Read by hand, passing
  answers contain false properties (e.g. "the result has exactly as many
  elements as the input" for a prime filter).
- Checked and ruled out: the H2-pilot spec arm sometimes writes a second,
  revised code block (15% of answers), but the first block passes almost as
  often (7 vs 9 of 22), so revision does not explain its gain.

Reading: H3 as stated (properties that correlate with passing) is not
supported; the model imitates the form of a spec. The arm-level gain under
GRPO may be real (extra text before the code could act as scratch space) or
a seed effect. Needs seeds before any follow-up.

### Mac environment notes
- SFT on MPS: each new sequence length allocates buffers that MPS keeps
  cached (20 GB after 100 examples, then swap). `sft.py` calls
  `torch.mps.empty_cache()` after every optimizer step and uses gradient
  checkpointing.
- With the displays asleep, MPS jobs froze in a GPU wait for minutes at a time
  and resumed when the display woke. Run long jobs under `caffeinate -d -i`.
- PyPI is throttled per connection on the home network (~40 KB/s); torch for
  macOS comes from download.pytorch.org (`[tool.uv.sources]` in
  pyproject.toml). Linux keeps PyPI's CUDA torch.
- Qwen3.5-0.8B weights are in `models/Qwen3.5-0.8B` (downloaded with parallel
  range requests; HF's xet transfer stalled).

## Next steps

H1, a one-seed H2 pilot and a one-seed H3 pilot are done. Next, in order:
1. Seeds. Repeat the H2 pilot arms (spec, thin) and the two H3 GRPO arms with
   2 more seeds each (`--seed`; about 1.5-2.5 h per run plus 30 min sampling).
   The H3 pilot showed a 25-point difference between two code-only spec runs
   on unseen problems, so no single-run gap is trustworthy yet.
2. Spec GRPO from the code-only warmup vs from no warmup, same seed, to
   separate "warmup hurts transfer" from run-to-run variance.
3. HumanEval+/MBPP+ guard on the adapters, then scale as in step 3 below.
The original plan follows.

Test the revised hypothesis in order. Stop at the first failed gate.

1. **H1, about half a day on the Mac, no training.** Sample 8 answers per
   problem from the base model on all 190 problems (1,024 tokens). Build the
   judge (full tests + differential testing against the reference). Score
   thin tests (first 1 and 2 tests), full tests and the spec for false accepts
   and false rejects. The same samples give each problem's base pass rate,
   which is the difficulty filter for step 3.
2. **Selection check, about an hour, same samples.** Pick 1 of 8 answers by
   random / thin tests / spec and compare judge pass rates. This is the
   inference-time use of specs and needs no training.
3. **H2, only if H1 passes.** Changes needed first:
   - `rewards.py`: a thin-test reward; partial credit gated or shrunk
     (for example `all_passed + 0.2 * fraction`).
   - `train_grpo.py`: `scale_rewards="batch"` or `"none"`,
     `mask_truncated_completions=True` or 1,024 tokens, several problems per
     update.
   - `build.py`: split by task family; keep train problems with a base pass
     rate of 20-60%.
   - `evaluate.py`: judge pass rate from 8 samples per problem.
   - Data: 500-1,000 accepted problems (`ANTHROPIC_API_KEY` +
     `spec_writer submit` -> `collect` -> `build`), 100+ held-out.
   - Hardware: the 4070 with vLLM and `flash-linear-attention`; 3 seeds per
     arm. A Mac night per arm is too slow for this.
4. **H3 and later:** thinking-on training with an SFT warmup on a model of
   1.5B or more; then the hint ladder, Dafny, Bend 2.

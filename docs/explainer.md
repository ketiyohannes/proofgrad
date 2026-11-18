# The spec-reward experiment, from the start

A plain-language account of what was tried, what failed and what the results
are as of 2026-11-11. The full technical record is in `docs/handoff.md`.

## The idea

Train a small coding model to write more correct code by grading it with a
strict checker. The checker is a **spec**: a set of rules the code must obey,
tested on many generated inputs. The model never sees the spec. It only sees
the task, writes ordinary code, and gets a score. The hope is that the habit
of writing correct code sticks after training, when no spec is around.

## The building blocks

- **Model:** Qwen3.5-0.8B, a small open model, trained on a 16 GB Mac.
- **Data:** 190 Python problems from the KodCode dataset, each with a
  reference solution and unit tests. We wrote a spec for each one.
- **Spec:** rules written with Hypothesis, a property-based testing library.
  Instead of "input X gives output Y", a rule says something that must hold
  for any input:

  ```python
  @prop("Reordering the input does not change the result.", case=cases())
  def order_invariant(f, case): ...
  ```

- **Verifier:** runs the model's code against the spec in a separate process
  and reports which rules passed.
- **LoRA:** we don't retrain the whole model. We train a small add-on (about
  40 MB) that adjusts its behaviour.
- **GRPO, the training algorithm:**
  1. Give the model one problem and sample 8 different answers.
  2. Score each answer with the checker.
  3. Compare each score to the group's average.
  4. Nudge the model toward the answers that beat the average and away from
     those below it.
  5. Repeat with the next problem.

  No "correct answer" is ever shown. The model learns only from which of its
  own attempts scored better.

## Attempt 1: the full run (no result)

We trained two copies for 240 updates each: one scored by the spec, one scored
by the problem's unit tests (the control). Scores gave partial credit: half
for the fraction of rules passed, half for passing everything. We then tested
both on public benchmarks (HumanEval+, MBPP+) and 33 held-out problems.

There was no measurable difference. On the held-out problems the spec model
solved 8 of 33 and the control 6, which is noise.

We also turned on the model's "thinking" mode to see whether the spec-trained
model reasoned differently. It didn't, and 73-79% of its reasoning traces ran
out of budget in loops.

## Why it failed: the audit

Going back through the logs showed the setup could not have detected an
effect:

- **The control was too strong.** Full unit tests rejected wrong code almost
  as well as the specs, so the two rewards were nearly the same.
- **Most problems were too hard.** In 55-63% of training rounds, none of the 8
  answers was correct.
- **Partial credit taught the wrong thing.** About 60% of the learning signal
  came from ranking wrong answers against each other.
- **Answers were cut off.** 20% hit the 512-token limit and scored about zero.
- **The measurement was too coarse.** 33 problems with one answer each can't
  show a difference of a few points, and 5 tasks appeared in both training
  and test sets.

## The redesign

We split the question into three steps, each with a pass/fail bar set in
advance.

| Change | Before | After |
|---|---|---|
| Control | Full unit tests | One example test (a weak checker) |
| Reward | Partial credit | Pass or fail |
| Problems | All of them | Only ones the model solves sometimes (1 to 7 of 8 tries) |
| Answer length | 512 tokens | 768, with cut-off answers ignored |
| Grading | The spec itself | An independent referee |
| Measurement | 1 answer per problem | 8 answers per problem, with a 95% interval |

The **referee** is never used for training. It runs the full unit tests and
also compares the model's output with the reference solution on up to 300
generated inputs.

## Step 1: are specs better checkers? (yes)

No training. We sampled 408 answers from the untrained model on 51 problems;
253 were wrong. We then counted how many wrong answers each checker let
through.

| Checker | Wrong answers accepted |
|---|---|
| One example test | 20.6% |
| Full unit tests | 1.6% |
| Spec | 0.4% |

## Step 2: does training on the strict checker help? (yes, on one run)

Two copies were trained on the same 20 problems for 120 updates each, one
rewarded by the spec and one by the single example test. Both were then tested
on 18 problems neither had seen.

| Model | Correct on unseen problems |
|---|---|
| Untrained | 41% |
| Trained on one test | 56% |
| Trained on the spec | 72% |

The spec model's lead is 16 points, with an interval of 6 to 26.

## Step 3: can the model "think in specs"? (not really)

Built-in thinking doesn't work at this size, so we taught the model to write a
`Properties:` list before its code. A supervised warmup on 141 other problems
showed it examples in that format; a control warmup showed code only. Both
then got the spec-reward training.

| Model | Unseen | Training problems |
|---|---|---|
| Warmup, code only | 49% | 44% |
| Warmup, rules first | 47% | 32% |
| Warmup + spec reward, code only | 47% | 80% |
| Warmup + spec reward, rules first | 69% | 74% |

- **The rules are decoration.** Every answer lists them, but passing and
  failing answers list the same kind and number, and passing answers include
  false rules.
- **Rules-first still did better after spec-reward training,** by 21.5 points
  on unseen problems. The code-only model memorized its training problems and
  gained nothing on new ones.

## Where this stands

The strict-checker idea looks promising, but there is one open problem. The
step 2 spec model and step 3's code-only model follow nearly the same recipe,
and they score 72% and 47% on the same unseen problems. Either the warmup
hurt, or two runs of the same recipe can differ by 25 points. Every result
above comes from a single run, so the next step is to repeat each one with
different random seeds before trusting any gap.

## Where things are

| What | Where |
|---|---|
| Full technical record and next steps | `docs/handoff.md` |
| Step 1 and 2 results | `runs/small/` (`h1.json`, `h2.json`) |
| Step 3 results | `runs/h3/` (`h2.json`, `h3_*.json`) |
| Drivers | `scripts/small_experiment.sh`, `scripts/h3_experiment.sh` |
| Code | `src/proofgrad/` |

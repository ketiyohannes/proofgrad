# Experiment design: does proof-based training make a better coding model?

Design only, written 2026-11-17. Nothing here has been run. Background and
earlier results are in `docs/explainer.md` and `docs/handoff.md`.

## The claim under test

> A model trained to write code that a proof checker accepts writes more
> correct ordinary code than a model trained, on the same problems and the
> same budget, by SFT or by RLHF.

"Ordinary code" means plain Python, with no proof checker available when the
model is used. That is the project's original goal: proofs as training
scaffolding, not as a gate at inference (which is what Bend 2 does).

### One comparison the claim needs but does not mention

Beating SFT and RLHF is not enough. Current coding models are also trained
with RL against executed unit tests. If the proof arm beats SFT and RLHF but
only matches test-based RL, the finding is "an executed reward beats
imitation and learned preferences", which is already known. So test-based RL
is a required arm, and it is the comparison that decides the claim.

## Hypotheses

| | Statement | Decided by |
|---|---|---|
| H1 | The proof arm beats SFT, preference RL and test RL on Python correctness on unseen problems | Proof arm against each of arms 1 to 3 |
| H2 | The gain comes from proving, not from learning a second language | Proof arm against the Dafny-without-proofs arm |
| H3 | The proof-trained model reasons in checkable claims that matter for its answer | Contract analysis (see "Mechanism") |

H1 is the main result. H2 and H3 are only worth running if H1 holds.

## Setup

- **Proof language: Dafny.** Off-the-shelf models succeed on 82% of Dafny
  verification tasks against 27% for Lean, a solver fills in most proof
  steps so the model writes only invariants and assertions, and Dafny
  compiles to Python. Bend 2 has no proof search and almost no pretraining
  data; it is a follow-up, not the first test.
- **Base model: a 1.5B-class open code model.** The 0.8B model used so far
  is unlikely to verify anything. Published work gets valid Dafny from 0.5B
  models after SFT, so 1.5B is a cautious choice that keeps about 18 runs
  affordable. The final step repeats the top two arms on a 7B model.
- **Hardware: a rented GPU with 24 GB or more.** The 16 GB Mac cannot fit
  this.
- **Adapter and RL algorithm:** LoRA and GRPO with pass/fail reward, as in
  `src/proofgrad/train_grpo.py`.

## Data

Every problem needs five parts, so that all arms train on the same problems:

1. A natural-language task.
2. A Python reference solution.
3. Python unit tests.
4. A Dafny spec: the method signature with `requires` and `ensures`.
5. A Dafny reference solution whose proof verifies.

Candidate sources, to be confirmed in step 0:

- ATLAS: 2.7K verified Dafny programs built from Python problems with unit
  tests. I could not confirm that the dataset is public.
- The vericoding benchmark: 3,029 Dafny specs.
- DafnyBench: 782 verified programs, 164 of them translated from MBPP.

Splits, by problem, with no problem family in two splits:

| Split | Size | Use |
|---|---|---|
| Warmup | about 1,000 | SFT |
| RL | about 300 | Reward training |
| Dev | 100 | Tuning and checkpoint choice |
| Test | at least 150 | Reported numbers, touched once |

Problems derived from MBPP or HumanEval are excluded from training, because
those benchmarks are used as outside checks.

## Arms

All arms start from the same base model, train on the same problems and stop
at the same GPU-hour cap. Each arm gets the same small tuning grid (learning
rate and number of updates), with the checkpoint chosen on the dev split.

| # | Arm | Warmup (SFT) | Second phase | Role |
|---|---|---|---|---|
| 0 | Untrained | none | none | Baseline |
| 1 | SFT | Python references | More SFT on the RL split | The SFT comparison |
| 2 | Test RL | Python references | GRPO, reward: all unit tests pass | The decisive control |
| 3 | Preference RL | Python references | GRPO, reward: a learned preference model | The RLHF comparison |
| 4 | Proof | Python and Dafny references | GRPO in Dafny, reward: verifier accepts code and proof | The treatment |
| 5 | Dafny without proofs | Python and Dafny references | GRPO in Dafny, reward: compiled code passes the tests | Separates proving from language exposure |

Arm 5 runs only if arm 4 beats arm 2.

### Arm 3: the RLHF stand-in

Real RLHF needs thousands of human rankings, which is out of reach. The
stand-in keeps what defines RLHF: the reward is a learned model of a rater
who reads answers and cannot run them.

- A stronger model compares pairs of candidate answers by reading only.
- A reward model is trained on 10,000 to 20,000 such pairs.
- The policy is trained with GRPO against that reward model.
- Its quality is reported the same way as the other checkers: the share of
  wrong answers it scores above the correct ones.

The paper should call this "learned-preference RL" and state that no human
labels were used.

### Arm 4: what counts as a verified answer

The model receives the task and the Dafny spec, and returns the method body
with its invariants and assertions. The reward is 1 only if all of these
hold:

- Dafny verifies the file within a fixed time limit.
- The signature, `requires` and `ensures` are byte-identical to the given
  spec.
- The answer contains none of `assume`, `{:axiom}`, `{:verify false}`,
  `decreases *`, or an `expect` that replaces a proof.

During the Dafny phase, a fixed share of Python SFT examples is mixed in for
arms 4 and 5 so that they do not forget Python.

## Measurement

**Primary outcome:** share of Python answers on the test split that pass the
referee in `src/proofgrad/judge.py` (full unit tests plus a differential test
against the reference on recorded inputs). Eight sampled answers per problem
at temperature 1.0, plus one greedy answer.

**Secondary outcomes:**

- Subtly wrong rate: answers that pass the visible example and fail the
  referee.
- HumanEval+ and LiveCodeBench, as a check that no arm got worse at general
  coding.
- Dafny verified rate on unseen specs, for arms 4 and 5.
- Tokens per correct answer.

**Seeds:** three per arm, five if the spread between seeds exceeds 5 points.

**Statistics:** bootstrap over problems and seeds together, 95% interval,
Holm correction over the three H1 comparisons.

**Bar for H1, fixed now:** the proof arm beats the best of arms 1 to 3 by at
least 5 points, with an interval that excludes zero.

**Why these sizes:** with 18 test problems the interval on a difference was
about ±10 points. That scales with the square root of the problem count, so
150 problems gives about ±3.5 points, enough to see a 5-point effect. This
is an estimate, to be rechecked on the pilot.

## Steps and pass bars

| Step | What | Pass bar | If it fails |
|---|---|---|---|
| 0 | Assemble paired data and the verifier harness | At least 1,500 problems with all five parts | Generate the missing Dafny side with a stronger model, or shrink the splits |
| 1 | Spec strength | Specs accept at most 1% of known-wrong programs | Drop or repair weak specs |
| 2 | Feasibility pilot, one seed | After warmup, at least 15% of answers verify, and at least 200 RL problems are solved 1 to 7 times out of 8 | Move to a larger model |
| 3 | Learning in Dafny, one seed | Verified rate on unseen specs rises by 10 points or more | Stop: nothing to transfer |
| 4 | Main comparison: arms 0 to 4, three seeds | The H1 bar | Report the null result |
| 5 | Attribution: arm 5 | Proof arm beats arm 5 | Gain is from Dafny exposure, not proving |
| 6 | Mechanism and a 7B repeat of the top two arms | See below | Report as is |

Step 1 uses wrong programs from two sources: mutated reference solutions,
and wrong answers sampled from the base model. Each verified reference is
also compiled to Python and run against the unit tests, to catch specs that
disagree with the tests.

## How to read the main result

| Pattern | Reading |
|---|---|
| Proof beats test RL, and beats Dafny without proofs | Claim supported |
| Proof beats test RL, ties Dafny without proofs | The gain is from the second language, not from proofs |
| Proof ties test RL, both beat SFT and preference RL | Executed rewards matter; proofs add nothing |
| Proof loses to test RL | Proof training costs Python ability at this budget |

## Mechanism (H3)

In the earlier pilot the model's written rules were decoration: nothing
checked them, and passing and failing answers listed the same rules. This
design makes the reasoning checkable in Python too.

- Prompt each arm in two formats: plain code, and code with preconditions,
  postconditions and loop invariants written as `assert` lines.
- Run the asserts on the referee's recorded inputs.
- Report three numbers per arm: the share of stated contracts that hold,
  whether holding contracts predict a correct answer, and how much
  correctness drops when the contract format is taken away.

H3 holds if the proof arm's contracts are true more often than the other
arms' and its correctness depends on them.

## Known weaknesses

- **The proof arm sees more data.** Its warmup includes Dafny references.
  Arm 5 controls for this, which is why H2 matters.
- **The preference arm is a stand-in.** A reader can object that real human
  feedback would do better or worse.
- **Small models may lack capacity.** A null result at 1.5B does not rule
  out an effect at 7B and above; the last step only partly covers this.
- **Specs are costly.** If the Dafny side must be generated, its quality
  limits everything; step 1 is the guard.
- **Pretraining overlap.** Source problems are public and may be in the base
  model's training data. This affects all arms equally.
- **Tuning effort.** Equal grids do not guarantee equal tuning; the dev
  split and the fixed cap are the mitigation.

## Cost

Rough estimates, to be replaced by measurements from step 2:

- 15 runs for the main comparison, plus 3 for arm 5 and 2 for the 7B repeat.
- 5 to 10 GPU-hours per RL run on a 1.5B model.
- 100 to 200 GPU-hours in total.
- Preference labels for arm 3 need a stronger model, through a paid API or
  a large local model.

## Decisions needed before starting

1. Whether to rent a GPU, and the spending limit.
2. Where the preference labels for arm 3 come from.
3. Whether to start at 1.5B or go straight to a larger model.

#!/usr/bin/env bash
# Small gated experiment (docs/handoff.md, "Hypothesis (revised)"): spec reward vs thin-test reward.
# Step 1 (H1) is run by hand first, because it chooses the problems:
#   python -m proofgrad.judge --problems data/problems_full.jsonl --ids runs/small/candidate_ids.json --out runs/small/candidates.jsonl
#   python -m proofgrad.evaluate ... --problems runs/small/candidates.jsonl --split all --samples 8 --out runs/small/samples_base_candidates.json
#   python -m proofgrad.experiment h1 --report runs/small/samples_base_candidates.json
#   python -m proofgrad.experiment select --report ... --problems runs/small/candidates.jsonl --out runs/small/problems.jsonl
# This script is step 2 (H2). Run from the repo root:  caffeinate -d -i bash scripts/small_experiment.sh
# Keep the display awake (-d): with the displays asleep, MPS jobs on this Mac froze in a GPU wait for
# minutes at a time (2026-11-11) and resumed as soon as the display woke.
# Each stage is skipped if its output already exists, so the script can be re-run after an interruption.
set -euo pipefail

MODEL=models/Qwen3.5-0.8B
OUT=runs/small
PROBLEMS=$OUT/problems.jsonl
STEPS=${STEPS:-120}
TOKENS=${TOKENS:-768}
log() { echo "[$(date '+%F %T')] $*" | tee -a "$OUT/progress.log"; }

train() {  # $1 = reward (spec|thin). Pass/fail reward; the other checkers and the judge are logged at weight 0.
  # One answer per backward pass: two 768-token answers in a batch run out of memory on a 16 GB Mac.
  local dir="$OUT/$1"
  if [[ -d "$dir/final" ]]; then log "train $1: already done"; return; fi
  log "train $1: start ($STEPS steps)"
  uv run --no-sync python -m proofgrad.train_grpo --model "$MODEL" --problems "$PROBLEMS" \
    --reward "$1" --monitor spec thin judge --partial-credit 0 --mask-truncated \
    --output-dir "$dir" --max-steps "$STEPS" --num-generations 8 --batch-size 1 --grad-accum 8 \
    --lr 2e-5 --max-completion-length "$TOKENS" --save-steps 20 --resume >> "$OUT/train_$1.log" 2>&1
  log "train $1: done"
}

sample() {  # $1 = name, $2 = adapter dir or empty. 8 sampled answers per problem, train and unseen halves.
  local out="$OUT/samples_$1.json"
  if [[ -f "$out" ]]; then log "sample $1: already done"; return; fi
  log "sample $1: start"
  local adapter_args=()
  [[ -n "$2" ]] && adapter_args=(--adapter "$2")
  uv run --no-sync python -m proofgrad.evaluate --model "$MODEL" ${adapter_args[@]+"${adapter_args[@]}"} --problems "$PROBLEMS" \
    --split all --samples 8 --temperature 1.0 --max-new-tokens "$TOKENS" --batch-size 1 --seed 1 \
    --out "$out" > "$OUT/samples_$1.log" 2>&1
  log "sample $1: done"
}

train spec
train thin
# The base model is sampled again with a fresh seed: the step-1 samples chose the problems, so they are biased.
sample base ""
sample spec "$OUT/spec/final"
sample thin "$OUT/thin/final"
uv run --no-sync python -m proofgrad.experiment h2 --problems "$PROBLEMS" \
  --reports base="$OUT/samples_base.json" spec="$OUT/samples_spec.json" thin="$OUT/samples_thin.json" \
  --out "$OUT/h2.json" > "$OUT/h2.log" 2>&1
log "all stages complete"

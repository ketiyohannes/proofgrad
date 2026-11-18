#!/usr/bin/env bash
# Full experiment: spec-reward GRPO vs unit-test control, then full evaluation.
# Run from the repo root:  caffeinate -i bash scripts/full_run.sh
# Each stage is skipped if its output already exists, so the script can be re-run after an interruption.
set -euo pipefail

MODEL=models/Qwen3.5-0.8B
PROBLEMS=data/problems_full.jsonl
OUT=runs/full
STEPS=${STEPS:-240}
mkdir -p "$OUT"
log() { echo "[$(date '+%F %T')] $*" | tee -a "$OUT/progress.log"; }

# The GPU is shared: wait for any running benchmark to finish first.
while pgrep -f "proofgrad.benchmark" >/dev/null; do sleep 30; done

train() {  # $1 = reward (spec|tests)
  local dir="$OUT/$1"
  if [[ -d "$dir/final" ]]; then log "train $1: already done"; return; fi
  log "train $1: start ($STEPS steps)"
  uv run --no-sync python -m proofgrad.train_grpo --model "$MODEL" --problems "$PROBLEMS" \
    --reward "$1" --monitor --output-dir "$dir" --max-steps "$STEPS" --num-generations 8 \
    --batch-size 2 --grad-accum 4 --lr 1e-5 --max-completion-length 512 --save-steps 40 \
    > "$OUT/train_$1.log" 2>&1
  log "train $1: done"
}

bench() {  # $1 = name, $2 = adapter dir
  local dir="runs/bench/$1"
  for ds in humaneval mbpp; do
    if [[ -f "$dir/summary.json" ]] && grep -q "\"$ds\"" "$dir/summary.json"; then log "bench $1 $ds: already done"; continue; fi
    log "bench $1 $ds: start"
    uv run --no-sync python -m proofgrad.benchmark --model "$MODEL" --adapter "$2" --datasets "$ds" \
      --max-new-tokens 512 --out-dir "$dir" > "$OUT/bench_$1_$ds.log" 2>&1
    log "bench $1 $ds: done"
  done
}

heldout() {  # $1 = name, $2 = adapter dir or empty
  local out="$OUT/heldout_$1.json"
  if [[ -f "$out" ]]; then log "held-out $1: already done"; return; fi
  log "held-out $1: start"
  local adapter_args=()
  [[ -n "$2" ]] && adapter_args=(--adapter "$2")
  uv run --no-sync python -m proofgrad.evaluate --model "$MODEL" ${adapter_args[@]+"${adapter_args[@]}"} --problems "$PROBLEMS" \
    --split test --max-new-tokens 512 --out "$out" > "$OUT/heldout_$1.log" 2>&1
  log "held-out $1: done"
}

train spec
train tests
bench full_spec "$OUT/spec/final"
bench full_tests "$OUT/tests/final"
heldout base ""
heldout spec "$OUT/spec/final"
heldout tests "$OUT/tests/final"
log "all stages complete"

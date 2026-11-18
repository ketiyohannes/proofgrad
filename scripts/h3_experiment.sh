#!/usr/bin/env bash
# H3 pilot (docs/handoff.md): does a model taught to state a problem's properties before the code write
# better code, and does spec-reward GRPO on top keep those statements meaningful?
# 2 x 2: answer format (code only | properties then code) x training (SFT warmup | warmup + spec GRPO).
# Uses the 20 train + 18 unseen problems of the small experiment; the warmup uses other problems.
# Run from the repo root:  caffeinate -d -i bash scripts/h3_experiment.sh
# (-d: with the displays asleep, MPS jobs on this Mac freeze in a GPU wait.)
# Each stage is skipped if its output exists, so the script can be re-run after an interruption.
set -euo pipefail

MODEL=models/Qwen3.5-0.8B
OUT=runs/h3
STEPS=${STEPS:-120}
TOKENS=${TOKENS:-768}
log() { echo "[$(date '+%F %T')] $*" | tee -a "$OUT/progress.log"; }
problems() { if [[ "$1" == props ]]; then echo "$OUT/problems_props.jsonl"; else echo "$OUT/problems_plain.jsonl"; fi; }

if [[ ! -f "$OUT/warmup.jsonl" ]]; then
  uv run --no-sync python -m proofgrad.experiment h3-data --all data/problems_full.jsonl --eval runs/small/problems.jsonl \
    --exclude findPrimes first_n_primes removeDuplicates group_and_sort_orders --out-dir "$OUT"
fi

warmup() {  # $1 = format (props|code): supervised warmup on reference answers in that format
  local dir="$OUT/sft_$1"
  if [[ -d "$dir/final" ]]; then log "warmup $1: already done"; return; fi
  log "warmup $1: start"
  uv run --no-sync python -m proofgrad.sft --model "$MODEL" --problems "$OUT/warmup.jsonl" --format "$1" \
    --output-dir "$dir" > "$OUT/sft_$1.log" 2>&1
  log "warmup $1: done"
}

grpo() {  # $1 = format: spec-reward GRPO on the 20 train problems, starting from the warmup adapter
  local dir="$OUT/grpo_$1"
  if [[ -d "$dir/final" ]]; then log "grpo $1: already done"; return; fi
  log "grpo $1: start ($STEPS steps)"
  uv run --no-sync python -m proofgrad.train_grpo --model "$MODEL" --problems "$(problems "$1")" \
    --init-adapter "$OUT/sft_$1/final" --reward spec --monitor spec thin judge --partial-credit 0 --mask-truncated \
    --output-dir "$dir" --max-steps "$STEPS" --num-generations 8 --batch-size 1 --grad-accum 8 \
    --lr 2e-5 --max-completion-length "$TOKENS" --save-steps 20 --resume >> "$OUT/train_grpo_$1.log" 2>&1
  log "grpo $1: done"
}

sample() {  # $1 = stage (sft|grpo), $2 = format. 8 sampled answers per problem, same settings as step 2.
  local out="$OUT/samples_$1_$2.json"
  if [[ -f "$out" ]]; then log "sample $1 $2: already done"; return; fi
  log "sample $1 $2: start"
  uv run --no-sync python -m proofgrad.evaluate --model "$MODEL" --adapter "$OUT/$1_$2/final" --problems "$(problems "$2")" \
    --split all --samples 8 --temperature 1.0 --max-new-tokens "$TOKENS" --batch-size 1 --seed 1 \
    --out "$out" > "$OUT/samples_$1_$2.log" 2>&1
  log "sample $1 $2: done"
}

warmup props; warmup code
sample sft props; sample sft code
grpo props; sample grpo props
grpo code; sample grpo code

uv run --no-sync python -m proofgrad.experiment h2 --problems "$OUT/problems_plain.jsonl" \
  --reports base=runs/small/samples_base.json spec=runs/small/samples_spec.json \
    sft_code="$OUT/samples_sft_code.json" sft_props="$OUT/samples_sft_props.json" \
    grpo_code="$OUT/samples_grpo_code.json" grpo_props="$OUT/samples_grpo_props.json" \
  --pairs sft_props:sft_code grpo_props:grpo_code grpo_props:sft_props grpo_code:sft_code sft_code:base grpo_code:spec \
  --out "$OUT/h2.json" > "$OUT/h2.log" 2>&1
for arm in sft_props grpo_props; do
  uv run --no-sync python -m proofgrad.experiment h3 --report "$OUT/samples_$arm.json" --out "$OUT/h3_$arm.json" > /dev/null
done
log "all stages complete"

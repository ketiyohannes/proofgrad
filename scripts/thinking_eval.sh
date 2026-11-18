#!/usr/bin/env bash
# Held-out eval with the model's reasoning mode on (2048-token thinking budget), base vs both adapters.
set -euo pipefail
OUT=runs/thinking
mkdir -p "$OUT"
for spec in "base:" "spec:runs/full/spec/final" "tests:runs/full/tests/final"; do
  name=${spec%%:*}; adapter=${spec#*:}
  [[ -f "$OUT/heldout_$name.json" ]] && continue
  args=(); [[ -n "$adapter" ]] && args=(--adapter "$adapter")
  echo "[$(date '+%T')] $name: start"
  uv run --no-sync python -m proofgrad.evaluate --model models/Qwen3.5-0.8B ${args[@]+"${args[@]}"} \
    --problems data/problems_full.jsonl --split test --thinking --thinking-budget 2048 --temperature 0.6 --seed 0 \
    --max-new-tokens 768 --batch-size "${BATCH:-11}" --out "$OUT/heldout_$name.json" > "$OUT/heldout_$name.log" 2>&1
  echo "[$(date '+%T')] $name: done"
done
echo "all done"

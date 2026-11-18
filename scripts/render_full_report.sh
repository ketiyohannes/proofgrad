#!/usr/bin/env bash
# Render the full-experiment report (base vs spec GRPO vs unit-test GRPO).
#   bash scripts/render_full_report.sh            -> runs/report_full.html
#   bash scripts/render_full_report.sh --embed    -> runs/report_full_embed.html (compact, for embedding)
set -euo pipefail
extra=(--train-stride 1); out=runs/report_full.html
if [[ "${1:-}" == "--embed" ]]; then extra=(--embed --train-stride 4); out=runs/report_full_embed.html; fi
uv run --no-sync python -m proofgrad.report --out "$out" "${extra[@]}" \
  --series "base=Base" "full_spec=Spec GRPO" "full_tests=Unit-test GRPO (control)" \
  --heldout base=runs/full/heldout_base.json full_spec=runs/full/heldout_spec.json full_tests=runs/full/heldout_tests.json \
  --train full_spec=runs/full/train_spec.log full_tests=runs/full/train_tests.log --epoch-steps 157 \
  --title "Spec reward vs unit-test reward: GRPO on Qwen3.5-0.8B" \
  --subtitle "Two LoRA runs, 240 GRPO steps each on 157 KodCode problems, identical except for the reward: hidden Hypothesis spec properties vs the original unit tests." \
  --bench-note "HumanEval 164 tasks, MBPP 378. Paired exact McNemar on the + metrics: spec vs base p=1.00 (HE+) and 1.00 (MBPP+); control vs base p=0.41 (HE+) and 0.013 (MBPP+); spec vs control on MBPP+ p=0.020 in the control's favor. Combined HE+ and MBPP+: base 26.0%, spec 26.4%, control 28.6% (spec vs control p=0.26)." \
  --heldout-note "33 held-out problems, greedy, one completion each, so one problem is 3 points. No difference is significant (smallest p=0.50)." \
  --train-note "The control run's answers shrink from about 300 to 90 tokens; the spec run's barely change."

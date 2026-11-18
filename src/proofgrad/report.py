"""Render experiment results as a self-contained HTML chart.

Reads benchmark summaries (``<bench-dir>/<name>/summary.json``), optional
held-out reports from ``proofgrad.evaluate`` and optional TRL training logs, and
writes one HTML file with:
- grouped columns: EvalPlus pass@1 per model and metric;
- grouped columns: held-out spec-problem metrics per model (if given);
- lines: hidden spec reward and completion length per training step, one line
  per run (rolling mean).

Series are ``name=Label`` pairs; their order fixes the colors (first = baseline).

    uv run --no-sync python -m proofgrad.report --out runs/report_full.html \
        --series base=Base full_spec="Spec GRPO" full_tests="Unit-test GRPO" \
        --heldout base=runs/full/heldout_base.json full_spec=runs/full/heldout_spec.json \
            full_tests=runs/full/heldout_tests.json \
        --train full_spec=runs/full/train_spec.log full_tests=runs/full/train_tests.log
"""

from __future__ import annotations

import ast
import argparse
import json
import re
from pathlib import Path
from typing import Any

METRICS = [
    ("humaneval", "base_pass@1", "HumanEval"),
    ("humaneval", "plus_pass@1", "HumanEval+"),
    ("mbpp", "base_pass@1", "MBPP"),
    ("mbpp", "plus_pass@1", "MBPP+"),
]
HELDOUT_METRICS = [
    ("spec_pass_rate", "All spec properties"),
    ("test_pass_rate", "Unit tests"),
    ("mean_property_score", "Mean property score"),
]
WINDOW = 20
# Embedded mode: the host page supplies background, text colors and padding.
EMBED_CSS = """
.viz-root { background: none !important; padding: 0 !important; color: var(--foreground);
  --text-primary: var(--foreground); --text-secondary: var(--muted-foreground); --text-muted: var(--muted-foreground);
  --grid: var(--border); --axis: var(--border); --surface-1: var(--background); }
.viz-root > h1 { display: none; }
.tip { background: var(--popover); color: var(--popover-foreground); border-color: var(--border); }
"""


def pairs(values: list[str]) -> dict[str, str]:
    """Parse ``name=value`` command-line pairs, keeping their order."""
    return dict(v.split("=", 1) for v in values)


def bench_rows(bench_dir: Path, names: list[str]) -> list[dict[str, Any]]:
    summaries = {name: json.loads((bench_dir / name / "summary.json").read_text()) for name in names}
    return [
        {"label": label, "tasks": summaries[names[0]][dataset]["tasks"], "values": {n: summaries[n][dataset][key] for n in names}}
        for dataset, key, label in METRICS
        if all(dataset in s for s in summaries.values())
    ]


def heldout_rows(reports: dict[str, Path]) -> list[dict[str, Any]]:
    loaded = {name: json.loads(path.read_text()) for name, path in reports.items()}
    first = next(iter(loaded.values()))
    return [
        {"label": label, "tasks": first["n_completions"], "values": {n: r[key] for n, r in loaded.items()}, "count": key != "mean_property_score"}
        for key, label in HELDOUT_METRICS
    ]


def rolling(values: list[float]) -> list[float]:
    return [round(sum(w) / len(w), 3) for w in (values[max(0, i - WINDOW + 1) : i + 1] for i in range(len(values)))]


def training_rows(log_path: Path, stride: int = 1) -> list[dict[str, float]]:
    """Rolling-mean metrics per step from the dicts TRL prints to the training log.

    ``stride`` keeps every Nth step (plus the last) to shrink the page."""
    text = log_path.read_text().replace("\r", "\n")
    logs = [ast.literal_eval(m) for m in re.findall(r"\{'loss'.*?\}", text)]
    logs = [d for d in logs if "rewards/spec_rubric_reward/mean" in d]
    reward = [float(d["rewards/spec_rubric_reward/mean"]) for d in logs]
    length = [float(d["completions/mean_length"]) for d in logs]
    rows = [
        {"step": i + 1, "reward_avg": ra, "length_avg": round(la)}
        for i, (ra, la) in enumerate(zip(rolling(reward), rolling(length)))
    ]
    return [r for i, r in enumerate(rows) if i % stride == 0 or i == len(rows) - 1]


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TITLE_TEXT</title>
<style>
.viz-root {
  color-scheme: light;
  --surface-1: #fcfcfb; --text-primary: #0b0b0b; --text-secondary: #52514e; --text-muted: #6f6e69;
  --grid: #e6e5e1; --axis: #b9b8b2;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .viz-root {
    color-scheme: dark;
    --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #9a998f;
    --grid: #2e2e2c; --axis: #55544f;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  }
}
:root[data-theme="dark"] .viz-root {
  color-scheme: dark;
  --surface-1: #1a1a19; --text-primary: #f0efec; --text-secondary: #c3c2b7; --text-muted: #9a998f;
  --grid: #2e2e2c; --axis: #55544f;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
}
body { margin: 0; }
.viz-root { background: var(--surface-1); color: var(--text-primary); font: 14px/1.45 system-ui, -apple-system, sans-serif; padding: 28px 32px 36px; }
h1 { font-size: 20px; margin: 0 0 4px; font-weight: 600; }
h2 { font-size: 15px; margin: 0 0 2px; font-weight: 600; }
.sub { color: var(--text-secondary); margin: 0 0 18px; max-width: 760px; }
.card { margin: 0 0 30px; }
.legend { display: flex; gap: 18px; margin: 8px 0 4px; color: var(--text-secondary); font-size: 13px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.swatch { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
svg text { fill: var(--text-secondary); font-size: 12px; }
svg .value { fill: var(--text-primary); font-size: 11px; font-weight: 600; }
svg .panel { fill: var(--text-primary); font-size: 12.5px; font-weight: 600; }
.note { color: var(--text-muted); font-size: 12.5px; max-width: 760px; margin-top: 6px; }
.tip { position: fixed; pointer-events: none; background: var(--surface-1); color: var(--text-primary); border: 1px solid var(--axis);
       border-radius: 6px; padding: 6px 9px; font-size: 12.5px; box-shadow: 0 2px 8px rgb(0 0 0 / .12); display: none; z-index: 2; }
details { margin-top: 10px; color: var(--text-secondary); font-size: 13px; }
table { border-collapse: collapse; margin-top: 6px; }
td, th { padding: 3px 12px 3px 0; text-align: left; font-variant-numeric: tabular-nums; }
th { color: var(--text-muted); font-weight: 500; }
</style>
</head>
<body>
<div class="viz-root">
  <h1>TITLE_TEXT</h1>
  <p class="sub">SUBTITLE_TEXT</p>

  <section class="card">
    <h2>EvalPlus pass@1 (greedy, never seen in training)</h2>
    <div class="legend" data-legend></div>
    <svg id="bench" role="img" aria-label="Grouped column chart of EvalPlus pass@1 per model"></svg>
    <p class="note">BENCH_NOTE</p>
    <details><summary>Table view</summary><table id="bench-table"></table></details>
  </section>

  <section class="card" id="heldout-card">
    <h2>Held-out spec problems</h2>
    <div class="legend" data-legend></div>
    <svg id="heldout" role="img" aria-label="Grouped column chart of held-out spec-problem metrics per model"></svg>
    <p class="note">HELDOUT_NOTE</p>
    <details><summary>Table view</summary><table id="heldout-table"></table></details>
  </section>

  <section class="card" id="train-card">
    <h2>Training dynamics</h2>
    <div class="legend" id="train-legend"></div>
    <svg id="train" role="img" aria-label="Line charts of hidden spec reward and completion length per training step"></svg>
    <p class="note">Lines: rolling mean over WINDOW_STEPS steps (one problem per step, so raw step values are mostly problem difficulty).
       Both runs log the spec reward; only the spec run is trained on it. TRAIN_NOTE</p>
  </section>
  <div class="tip" id="tip"></div>
</div>
<script>
const SERIES = SERIES_JSON;   // [[name, label], ...]; first is the baseline
const BENCH = BENCH_JSON;
const HELDOUT = HELDOUT_JSON;
const TRAIN = TRAIN_JSON;     // {name: [{step, reward_avg, length_avg}]}
const EPOCH = EPOCH_STEPS;
const NS = "http://www.w3.org/2000/svg";
const tip = document.getElementById("tip");
const color = name => `var(--series-${SERIES.findIndex(s => s[0] === name) + 1})`;
const label = name => SERIES.find(s => s[0] === name)[1];
const pct = v => (v * 100).toFixed(1) + "%";
function el(name, attrs, parent) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  parent.appendChild(node); return node;
}
function showTip(evt, html) { tip.innerHTML = html; tip.style.display = "block";
  tip.style.left = (evt.clientX + 14) + "px"; tip.style.top = (evt.clientY + 14) + "px"; }
function hideTip() { tip.style.display = "none"; }
// Column with a 4px rounded top, square at the zero baseline.
function columnPath(x, y, w, h) { const r = Math.min(4, h);
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`; }
function legend(node, names) {
  node.innerHTML = names.map(n => `<span><i class="swatch" style="background:${color(n)}"></i>${label(n)}</span>`).join("");
}
document.querySelectorAll("[data-legend]").forEach(n => legend(n, SERIES.map(s => s[0])));

function columns(svgId, tableId, rows) {
  const svg = document.getElementById(svgId), names = SERIES.map(s => s[0]);
  const W = 720, H = 280, m = {t: 22, r: 10, b: 26, l: 44};
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.style.width = "100%"; svg.style.maxWidth = W + "px";
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const ymax = Math.max(0.3, Math.ceil(Math.max(...rows.flatMap(d => names.map(n => d.values[n]))) * 10 + 0.5) / 10);
  const y = v => m.t + ih - (v / ymax) * ih;
  for (let v = 0; v <= ymax + 1e-9; v += 0.1) {
    el("line", {x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: v === 0 ? "var(--axis)" : "var(--grid)", "stroke-width": 1}, svg);
    el("text", {x: m.l - 8, y: y(v) + 4, "text-anchor": "end"}, svg).textContent = Math.round(v * 100) + "%";
  }
  const band = iw / rows.length, gap = 3, bw = Math.min(40, (band * 0.8 - gap * (names.length - 1)) / names.length);
  rows.forEach((d, i) => {
    const cx = m.l + band * i + band / 2, start = cx - (names.length * bw + (names.length - 1) * gap) / 2;
    names.forEach((name, j) => {
      const v = d.values[name], x = start + j * (bw + gap), top = y(v);
      const p = el("path", {d: columnPath(x, top, bw, y(0) - top), fill: color(name)}, svg);
      el("text", {x: x + bw / 2, y: top - 5, "text-anchor": "middle", class: "value"}, svg).textContent = pct(v);
      const hit = el("rect", {x: x - gap / 2, y: m.t, width: bw + gap, height: ih, fill: "transparent"}, svg);
      const delta = j ? `<br>${((v - d.values[names[0]]) * 100).toFixed(1)} pts vs ${label(names[0])}` : "";
      const count = d.count === false ? "" : ` (${Math.round(v * d.tasks)}/${d.tasks})`;
      const show = e => { p.style.opacity = 0.85; showTip(e, `<b>${d.label}</b><br>${label(name)}: ${pct(v)}${count}${delta}`); };
      hit.addEventListener("mousemove", show); hit.addEventListener("mouseleave", () => { p.style.opacity = 1; hideTip(); });
    });
    el("text", {x: cx, y: H - m.b + 18, "text-anchor": "middle"}, svg).textContent = d.label;
  });
  document.getElementById(tableId).innerHTML = `<tr><th>Metric</th><th>n</th>${names.map(n => `<th>${label(n)}</th>`).join("")}</tr>` +
    rows.map(d => `<tr><td>${d.label}</td><td>${d.tasks}</td>${names.map((n, j) => `<td>${pct(d.values[n])}` +
      (j ? ` (${((d.values[n] - d.values[names[0]]) * 100) >= 0 ? "+" : ""}${((d.values[n] - d.values[names[0]]) * 100).toFixed(1)})` : "") +
      "</td>").join("")}</tr>`).join("");
}
columns("bench", "bench-table", BENCH);
if (HELDOUT.length) columns("heldout", "heldout-table", HELDOUT); else document.getElementById("heldout-card").remove();

(function train() {
  const runs = Object.keys(TRAIN);
  if (!runs.length) { document.getElementById("train-card").remove(); return; }
  legend(document.getElementById("train-legend"), runs);
  const svg = document.getElementById("train");
  const W = 720, PH = 170, GAP = 44, m = {t: 26, r: 64, b: 30, l: 48}, H = m.t + 2 * PH + GAP + m.b;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.style.width = "100%"; svg.style.maxWidth = W + "px";
  const iw = W - m.l - m.r, n = Math.max(...runs.map(r => TRAIN[r].at(-1).step));
  const x = s => m.l + ((s - 1) / Math.max(1, n - 1)) * iw;
  const panels = [
    {key: "reward_avg", title: "Hidden spec reward", top: m.t, max: 0.5, step: 0.1, fmt: v => v.toFixed(2)},
    {key: "length_avg", title: "Completion length (tokens)", top: m.t + PH + GAP, max: 400, step: 100, fmt: v => v.toFixed(0)},
  ];
  panels.forEach(pn => {
    pn.y = v => pn.top + PH - (v / pn.max) * PH;
    el("text", {x: m.l, y: pn.top - 10, class: "panel"}, svg).textContent = pn.title;
    for (let v = 0; v <= pn.max + 1e-9; v += pn.step) {
      el("line", {x1: m.l, x2: W - m.r, y1: pn.y(v), y2: pn.y(v), stroke: v === 0 ? "var(--axis)" : "var(--grid)", "stroke-width": 1}, svg);
      el("text", {x: m.l - 8, y: pn.y(v) + 4, "text-anchor": "end"}, svg).textContent = pn.step < 1 ? v.toFixed(1) : v;
    }
    if (EPOCH && EPOCH < n) {
      el("line", {x1: x(EPOCH), x2: x(EPOCH), y1: pn.top, y2: pn.top + PH, stroke: "var(--axis)", "stroke-dasharray": "3 3"}, svg);
      if (pn === panels[0]) el("text", {x: x(EPOCH) + 5, y: pn.top + 12}, svg).textContent = "2nd pass over problems";
    }
    runs.forEach(r => {
      const rows = TRAIN[r];
      el("path", {d: rows.map((d, i) => `${i ? "L" : "M"}${x(d.step)},${pn.y(d[pn.key])}`).join(""), fill: "none",
        stroke: color(r), "stroke-width": 2, "stroke-linejoin": "round"}, svg);
    });
    // End labels, nudged apart when the two lines finish close together.
    const ends = runs.map(r => ({r, v: TRAIN[r].at(-1)[pn.key], ly: pn.y(TRAIN[r].at(-1)[pn.key])})).sort((a, b) => a.ly - b.ly);
    for (let i = 1; i < ends.length; i++) ends[i].ly = Math.max(ends[i].ly, ends[i - 1].ly + 13);
    ends.forEach(e => el("text", {x: x(TRAIN[e.r].at(-1).step) + 8, y: e.ly + 4, class: "value", style: `fill:${color(e.r)}`}, svg).textContent = pn.fmt(e.v));
  });
  for (let s = 40; s <= n; s += 40) el("text", {x: x(s), y: H - m.b + 18, "text-anchor": "middle"}, svg).textContent = "step " + s;
  const cross = el("line", {y1: m.t, y2: H - m.b, stroke: "var(--axis)", "stroke-width": 1, visibility: "hidden"}, svg);
  const hit = el("rect", {x: m.l, y: m.t, width: iw, height: H - m.t - m.b, fill: "transparent"}, svg);
  hit.addEventListener("mousemove", e => {
    const box = svg.getBoundingClientRect(), sx = (e.clientX - box.left) * (W / box.width);
    const step = Math.max(1, Math.min(n, Math.round(((sx - m.l) / iw) * (n - 1)) + 1));
    cross.setAttribute("x1", x(step)); cross.setAttribute("x2", x(step)); cross.setAttribute("visibility", "visible");
    // Nearest logged row (rows may be strided).
    const near = r => TRAIN[r].reduce((a, b) => Math.abs(b.step - step) < Math.abs(a.step - step) ? b : a);
    showTip(e, `<b>Step ${step}</b>` + runs.map(r => { const d = near(r); return d.step > TRAIN[r].at(-1).step ? "" :
      `<br>${label(r)}: reward ${d.reward_avg.toFixed(3)}, length ${d.length_avg.toFixed(0)}`; }).join(""));
  });
  hit.addEventListener("mouseleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
})();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bench-dir", type=Path, default=Path("runs/bench"))
    parser.add_argument("--series", nargs="+", default=["base=Base", "grpo=Fine-tuned (spec GRPO)"], help="name=Label, baseline first")
    parser.add_argument("--heldout", nargs="*", default=[], help="name=path to a proofgrad.evaluate report")
    parser.add_argument("--train", nargs="*", default=[], help="name=path to a TRL training log")
    parser.add_argument("--train-stride", type=int, default=1, help="plot every Nth training step")
    parser.add_argument("--epoch-steps", type=int, default=0, help="steps per pass over the training problems (draws a marker)")
    parser.add_argument("--title", default="Spec-reward GRPO on Qwen3.5-0.8B")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--bench-note", default="")
    parser.add_argument("--heldout-note", default="")
    parser.add_argument("--train-note", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--embed", action="store_true", help="no page background/padding/title (for embedding)")
    args = parser.parse_args()

    series = pairs(args.series)
    names = list(series)
    replacements = {
        "SERIES_JSON": json.dumps(list(series.items())),
        "BENCH_JSON": json.dumps(bench_rows(args.bench_dir, names)),
        "HELDOUT_JSON": json.dumps(heldout_rows({n: Path(p) for n, p in pairs(args.heldout).items()}) if args.heldout else []),
        "TRAIN_JSON": json.dumps({n: training_rows(Path(p), args.train_stride) for n, p in pairs(args.train).items()}),
        "EPOCH_STEPS": str(args.epoch_steps),
        "WINDOW_STEPS": str(WINDOW),
        "SUBTITLE_TEXT": args.subtitle,  # before TITLE_TEXT, which it contains
        "TITLE_TEXT": args.title,
        "BENCH_NOTE": args.bench_note,
        "HELDOUT_NOTE": args.heldout_note,
        "TRAIN_NOTE": args.train_note,
    }
    html = TEMPLATE
    for key, value in replacements.items():
        html = html.replace(key, value)
    if args.embed:
        html = html.replace("</style>", EMBED_CSS + "</style>", 1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

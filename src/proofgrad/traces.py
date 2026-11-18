"""Compare reasoning traces across models (thinking-mode eval reports).

Computes per-model trace statistics (length, self-corrections, repetition,
edge-case and property-style reasoning) and writes a side-by-side HTML viewer:
one row per problem, one column per model, with verdict, failed spec
properties, the full reasoning trace and the final answer.

    uv run --no-sync python -m proofgrad.traces --out runs/thinking/traces.html \
        --runs base=runs/thinking/heldout_base.json spec=runs/thinking/heldout_spec.json \
            tests=runs/thinking/heldout_tests.json \
        --no-thinking base=runs/full/heldout_base.json spec=runs/full/heldout_spec.json \
            tests=runs/full/heldout_tests.json
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

# Phrase families counted per trace (case-insensitive, whole-word where it matters).
MARKERS = {
    "self_corrections": r"\bwait\b|\bactually\b|\bi made an error\b|\blet me (?:re-?check|reconsider|trace again|re-?think)\b|\bhmm\b",
    "edge_cases": r"\bedge case|\bcorner case|\bempty\b|\bsingle element|\bnegative\b|\bzero\b|\bduplicate|\boverflow\b|\bboundary\b",
    "spec_style": r"\binvariant|\bproperty\b|\bproperties\b|\bmust (?:always|never)\b|\bfor (?:all|every|any)\b|\bguarantee|\bpostcondition|\bprecondition|\bconstraint",
    "example_tracing": r"\bexample\b|\blet me trace\b|\btrace through\b|\bstep by step\b|\binput:",
}


def trace_stats(trace: str) -> dict[str, float]:
    lines = [ln.strip() for ln in trace.splitlines() if ln.strip()]
    stats: dict[str, float] = {name: len(re.findall(rx, trace, re.IGNORECASE)) for name, rx in MARKERS.items()}
    stats["words"] = len(trace.split())
    # Share of non-empty lines that repeat an earlier line: a looping indicator.
    stats["repeated_lines"] = (len(lines) - len(set(lines))) / len(lines) if lines else 0.0
    stats["code_in_trace"] = float("```" in trace)
    return stats


def summarize(report: dict[str, Any]) -> dict[str, float]:
    records = report["records"]
    n = len(records) or 1
    per_trace = [trace_stats(r.get("thinking", "")) for r in records]
    summary = {
        "spec_pass": sum(r["spec_passed"] for r in records) / n,
        "tests_pass": sum(r["tests_passed"] for r in records) / n,
        "property_score": sum(r["property_score"] for r in records) / n,
        "forced_stop": sum(r.get("forced_stop", False) for r in records) / n,
    }
    for key in per_trace[0] if per_trace else []:
        summary[key] = sum(t[key] for t in per_trace) / n
    return summary


def _verdict(record: dict[str, Any] | None) -> str:
    if record is None:
        return '<span class="badge none">n/a</span>'
    if record["spec_passed"]:
        return '<span class="badge pass">spec pass</span>'
    if record["tests_passed"]:
        return '<span class="badge warn">tests only</span>'
    return f'<span class="badge fail">fail · {record["property_score"]:.2f}</span>'


def _answer(record: dict[str, Any]) -> str:
    return record["completion"].rsplit("</think>", 1)[-1].strip()


STAT_ROWS = [
    ("spec_pass", "Spec pass (all properties)", "pct"),
    ("tests_pass", "Unit tests pass", "pct"),
    ("property_score", "Mean property score", "num"),
    ("forced_stop", "Hit thinking budget", "pct"),
    ("words", "Trace length (words)", "int"),
    ("self_corrections", "Self-corrections per trace", "num"),
    ("repeated_lines", "Repeated lines (looping)", "pct"),
    ("edge_cases", "Edge-case mentions", "num"),
    ("spec_style", "Property-style mentions", "num"),
    ("example_tracing", "Example-tracing mentions", "num"),
    ("code_in_trace", "Drafts code while thinking", "pct"),
]

CSS = """
:root { color-scheme: light dark; --bg: #fcfcfb; --fg: #0b0b0b; --muted: #6f6e69; --line: #e6e5e1; --card: #f4f3f0;
  --pass: #1baf7a; --warn: #c98a00; --fail: #d1453b; }
@media (prefers-color-scheme: dark) { :root { --bg: #1a1a19; --fg: #f0efec; --muted: #9a998f; --line: #2e2e2c; --card: #232321;
  --pass: #199e70; --warn: #d9a521; --fail: #e0605a; } }
body { margin: 0; background: var(--bg); color: var(--fg); font: 14px/1.45 system-ui, -apple-system, sans-serif; }
main { padding: 24px 28px 48px; max-width: 1500px; }
h1 { font-size: 20px; margin: 0 0 4px; } h2 { font-size: 15px; margin: 28px 0 8px; }
.sub, .note { color: var(--muted); max-width: 900px; }
table.stats { border-collapse: collapse; font-variant-numeric: tabular-nums; }
table.stats td, table.stats th { padding: 4px 14px 4px 0; text-align: left; border-bottom: 1px solid var(--line); }
table.stats th { color: var(--muted); font-weight: 500; }
.problem { border-top: 1px solid var(--line); padding: 14px 0; }
.problem > summary { cursor: pointer; font-weight: 600; }
.prompt { white-space: pre-wrap; color: var(--muted); font-size: 13px; margin: 8px 0; max-height: 220px; overflow: auto; }
.cols { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 12px; margin-top: 8px; }
.col { background: var(--card); border-radius: 8px; padding: 10px 12px; min-width: 0; }
.col h3 { font-size: 13px; margin: 0 0 6px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.badge { font-size: 11.5px; font-weight: 600; padding: 1px 7px; border-radius: 10px; color: #fff; }
.pass { background: var(--pass); } .warn { background: var(--warn); } .fail { background: var(--fail); } .none { background: var(--muted); }
.meta { color: var(--muted); font-size: 12px; margin: 2px 0 6px; }
details.trace > summary { cursor: pointer; color: var(--muted); font-size: 12.5px; }
pre { white-space: pre-wrap; word-break: break-word; font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; margin: 6px 0 0;
  max-height: 520px; overflow: auto; }
.filters { margin: 10px 0; display: flex; gap: 14px; color: var(--muted); font-size: 13px; }
"""

SCRIPT = """
const boxes = document.querySelectorAll('.filters input');
function apply() {
  const only = [...boxes].filter(b => b.checked).map(b => b.value);
  document.querySelectorAll('.problem').forEach(p => {
    p.style.display = only.every(f => p.dataset[f] === '1') ? '' : 'none';
  });
}
boxes.forEach(b => b.addEventListener('change', apply));
"""


def render(runs: dict[str, dict[str, Any]], baseline: dict[str, dict[str, Any]], problems: dict[str, dict[str, Any]]) -> str:
    names = list(runs)
    summaries = {n: summarize(r) for n, r in runs.items()}
    base_summaries = {n: summarize(r) for n, r in baseline.items()}
    fmt = {"pct": lambda v: f"{v:.0%}", "num": lambda v: f"{v:.2f}", "int": lambda v: f"{v:.0f}"}

    head = "".join(f"<th>{html.escape(n)}</th>" for n in names)
    rows = "".join(
        f"<tr><td>{label}</td>" + "".join(f"<td>{fmt[kind](summaries[n][key])}</td>" for n in names) + "</tr>"
        for key, label, kind in STAT_ROWS
    )
    off_rows = ""
    if baseline:
        off_rows = "".join(
            f"<tr><td>{label} (thinking off)</td>"
            + "".join(f"<td>{fmt[kind](base_summaries[n][key]) if n in base_summaries else '–'}</td>" for n in names)
            + "</tr>"
            for key, label, kind in STAT_ROWS[:3]
        )

    by_id = {n: {r["id"]: r for r in rep["records"]} for n, rep in runs.items()}
    off_by_id = {n: {r["id"]: r for r in rep["records"]} for n, rep in baseline.items()}
    ids = list(by_id[names[0]])
    blocks = []
    for pid in ids:
        recs = {n: by_id[n].get(pid) for n in names}
        passes = [bool(r and r["spec_passed"]) for r in recs.values()]
        cols = []
        for n, r in recs.items():
            if r is None:
                cols.append(f'<div class="col"><h3>{html.escape(n)} {_verdict(None)}</h3></div>')
                continue
            st = trace_stats(r.get("thinking", ""))
            off = off_by_id.get(n, {}).get(pid)
            failed = ", ".join(r["failed"]) or "none"
            cols.append(
                f'<div class="col"><h3>{html.escape(n)} {_verdict(r)}'
                + (f'<span class="meta">thinking off: {_verdict(off)}</span>' if off else "")
                + "</h3>"
                f'<div class="meta">{st["words"]:.0f} words · {st["self_corrections"]:.0f} self-corrections · '
                f'{"hit budget" if r.get("forced_stop") else "finished"} · failed: {html.escape(failed)}</div>'
                f'<details class="trace"><summary>Reasoning trace</summary><pre>{html.escape(r.get("thinking", ""))}</pre></details>'
                f'<details class="trace" open><summary>Answer</summary><pre>{html.escape(_answer(r))}</pre></details></div>'
            )
        prompt = problems.get(pid, {}).get("prompt", "")
        blocks.append(
            f'<details class="problem" data-differ="{int(len(set(passes)) > 1)}" data-anypass="{int(any(passes))}">'
            f"<summary>{html.escape(pid)} · " + " / ".join("✓" if p else "✗" for p in passes) + "</summary>"
            f'<div class="prompt">{html.escape(prompt)}</div>'
            f'<div class="cols" style="--n:{len(names)}">{"".join(cols)}</div></details>'
        )

    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Reasoning traces</title><style>{CSS}</style></head><body><main>'
        "<h1>Reasoning traces: base vs spec-GRPO vs unit-test-GRPO</h1>"
        '<p class="sub">Held-out spec problems with the model\'s thinking mode on. Marker counts are regex heuristics over the trace '
        "text (see <code>proofgrad.traces.MARKERS</code>), useful for comparing models, not as exact measures.</p>"
        f'<h2>Summary</h2><table class="stats"><tr><th></th>{head}</tr>{rows}{off_rows}</table>'
        f"<h2>Per problem ({len(ids)})</h2>"
        "<p class=\"note\">Header marks: spec pass per model, in column order. Click a problem to open it.</p>"
        '<div class="filters"><label><input type="checkbox" value="differ"> only where models disagree</label>'
        '<label><input type="checkbox" value="anypass"> only where some model passes</label></div>'
        + "".join(blocks)
        + f"<script>{SCRIPT}</script></main></body></html>"
    )


def _load(pairs: list[str]) -> dict[str, dict[str, Any]]:
    return {name: json.loads(Path(path).read_text()) for name, path in (p.split("=", 1) for p in pairs)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", nargs="+", required=True, help="name=path to a thinking-mode evaluate report")
    parser.add_argument("--no-thinking", nargs="*", default=[], help="name=path to the same model's thinking-off report")
    parser.add_argument("--problems", type=Path, default=Path("data/problems_full.jsonl"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    problems = {p["id"]: p for p in (json.loads(ln) for ln in args.problems.read_text().splitlines() if ln.strip())}
    runs, baseline = _load(args.runs), _load(args.no_thinking)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(runs, baseline, problems))
    print(json.dumps({n: {k: round(v, 3) for k, v in summarize(r).items()} for n, r in runs.items()}, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

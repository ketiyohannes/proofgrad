"""Generate Hypothesis spec modules with Claude via the Message Batches API.

Batches cost 50% of standard pricing; the long shared instructions are cached.
Generated specs are only drafts: ``proofgrad.build`` decides whether they meet
our standards, and rejected specs can be sent back with the rejection reason.

    # draft specs for candidates that have none yet
    python -m proofgrad.spec_writer submit --candidates data/candidates.jsonl --specs data/specs
    # retry specs that build rejected, showing the model why
    python -m proofgrad.spec_writer submit --candidates data/candidates.jsonl --specs data/specs \
        --repair data/problems.rejected.jsonl
    # wait for the batch and write data/specs/<slug>.py
    python -m proofgrad.spec_writer collect --specs data/specs

Credentials come from ANTHROPIC_API_KEY (or any source the anthropic SDK resolves).
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

from proofgrad.build import slug

DEFAULT_MODEL = "claude-opus-5-5"
STATE_FILE = "batches.json"
_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)

SYSTEM_PROMPT = '''\
You write formal specifications, as executable Hypothesis properties, for small \
Python programming problems. The specs are a hidden grading rubric for \
reinforcement learning: a student model sees only the problem statement and the \
function signature, writes code, and earns partial credit for each property its \
code satisfies. You are given the problem, a verified reference solution and \
its unit tests.

Write one Python module in this exact format:

```python
"""Spec for <entry point>: <one-line summary of the contract>."""
from hypothesis import strategies as st
from proofgrad.spec_runtime import prop

ENTRY_POINT = "my_max"

nonempty_ints = st.lists(st.integers(min_value=-10**6, max_value=10**6), min_size=1, max_size=50)

@prop("The result is greater than or equal to every element.", xs=nonempty_ints)
def is_upper_bound(f, xs):
    m = f(xs)
    assert all(x <= m for x in xs)

@prop("The result is one of the input elements.", xs=nonempty_ints)
def is_member(f, xs):
    assert f(xs) in xs
```

How properties work:
- `@prop(description, **strategies)` declares one rubric item. Hypothesis draws \
each keyword argument from its strategy and calls `check(f, **drawn)`. A \
property fails if it raises (an assertion, or any exception from `f`).
- `f` is the student's function. It deep-copies its arguments on every call, so \
you may call it several times and compare against the inputs afterwards.
- Each property is scored independently, so make them independent: one \
property per distinct aspect of correctness, typically 3 to 6 per problem.

Optional module-level fields (plain literals):
- `CLARIFICATIONS = ["...", ...]`: the student sees only the problem statement, so any behavior your properties check that the statement leaves implicit must be stated here. These lines are appended to the student's prompt. Use them for tie-breaking and output order (e.g. "If several substrings are equally long, return the leftmost one."), the result for edge inputs the statement does not cover but the unit tests do (e.g. "Return 0 for an empty list."), and exact return types, and mismatches between the statement and the signature (e.g. the \
statement says "print" but the signature returns a value). Keep each one short \
and phrase it as part of the task. Never put hints about the algorithm here.
- `EXCLUDE_REASON = "..."`: set this, with a one-sentence reason, when the problem cannot be fairly graded: the reference solution contradicts the problem statement, or the statement is too broken to specify. The problem is then dropped from the dataset. Still write your best properties below it.

What makes a good spec:
- Describe WHAT a correct answer is, not HOW to compute it. Prefer relational properties (output is sorted; output is a permutation of the input; every returned index satisfies the condition; no shorter answer exists) and metamorphic properties (reversing the input does not change the answer; adding an element can only increase the count).
- When the answer is a number that cannot be checked by a relation alone, compare against a simple, obviously-correct brute-force oracle written inside the spec, on small inputs. Follow the definition directly; that is fine even when the reference happens to be just as naive. Do not reproduce a clever algorithm from the reference.
- One claim per property, so partial credit is meaningful. Put the empty or degenerate cases the unit tests check in their own property. Helper functions and `@st.composite` strategies shared by several properties are encouraged.
- Together the properties must pin down the full contract: an implementation satisfying all of them should be correct, even on problems so small that there is little to mutate. Think about off-by-one errors, boundary values, empty and single-element inputs, duplicates, negative numbers and ties, and make sure some property would catch each plausible bug.
- Check the return type the statement or signature implies (use `is True` / `is False` for booleans, `isinstance(result, list)` for lists).
- Input domain: generate only inputs the statement allows, plus edge inputs the unit tests exercise even if they fall outside the stated constraints. Where the statement is silent about a domain (negative numbers, empty input) and neither the tests nor a natural reading fix the answer, do not generate those inputs. Where the statement is ambiguous, follow the reference solution and unit tests, and add a CLARIFICATION. State domain assumptions in the module docstring.
- Bias generators toward the structures that expose bugs, not just small values: use `st.one_of` to mix in all-equal elements, few distinct values, minimum and maximum sizes, sorted and reverse-sorted inputs. For problems with \
thresholds (a sum or balance reaching exactly 0), also mix in tiny values such \
as 0..1, because wide value ranges make boundary cases rare. When you construct inputs that must have a particular answer (e.g. "definitely not an arithmetic progression"), make sure the construction cannot accidentally produce the other answer. `st.data()`, `st.permutations` and `st.composite` help with dependent inputs.
- Keep it fast: every property runs about 100 examples on student code and 500 on the reference within a few seconds, so bound sizes so that both your oracle AND a naive reference stay fast.
- Requirements that properties cannot observe (time or space complexity, "do it in place") are not checked; leave them out.
- Use only `hypothesis` and the standard library. Do not import the reference solution or the unit tests; the spec must stand alone.

Reply with the module in a single ```python code block and nothing else.'''


def _user_message(candidate: dict[str, Any], previous_spec: str | None, rejection: str | None) -> str:
    parts = [
        f"## Problem\n\n{candidate['question']}",
        f"## Signature\n\n```python\n{candidate['signature']}\n```\n\nENTRY_POINT = {candidate['entry_point']!r}",
        f"## Reference solution (verified)\n\n```python\n{candidate['reference_solution']}```",
        f"## Unit tests\n\n```python\n{candidate['unit_tests']}```",
    ]
    if previous_spec and rejection:
        parts.append(
            "## Your previous spec was rejected\n\n"
            f"```python\n{previous_spec}```\n\nReason: {rejection}\n\n"
            "Fix the problem. If the reference fails a property, the property is wrong. "
            "If the spec is too weak, add or strengthen properties so they catch the bugs the unit tests catch."
        )
    return "\n\n".join(parts)


def _request(candidate: dict[str, Any], model: str, previous_spec: str | None = None, rejection: str | None = None) -> Any:
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    return Request(
        custom_id=slug(candidate["id"]),
        params=MessageCreateParamsNonStreaming(
            model=model,
            max_tokens=16000,
            output_config={"effort": "high"},
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": _user_message(candidate, previous_spec, rejection)}],
        ),
    )


def submit(args: argparse.Namespace) -> None:
    import anthropic

    candidates = [json.loads(line) for line in args.candidates.read_text().splitlines() if line.strip()]
    args.specs.mkdir(parents=True, exist_ok=True)
    if args.repair:
        rejections = {r["id"]: r["reason"] for r in map(json.loads, args.repair.read_text().splitlines()) if r}
        requests = [
            _request(c, args.model, (args.specs / f"{slug(c['id'])}.py").read_text(), rejections[c["id"]])
            for c in candidates
            if c["id"] in rejections and (args.specs / f"{slug(c['id'])}.py").exists()
        ]
    else:
        requests = [_request(c, args.model) for c in candidates if not (args.specs / f"{slug(c['id'])}.py").exists()]
    requests = requests[: args.limit] if args.limit else requests
    if not requests:
        print("nothing to submit")
        return

    batch = anthropic.Anthropic().messages.batches.create(requests=requests)
    state_path = args.specs / STATE_FILE
    state = json.loads(state_path.read_text()) if state_path.exists() else []
    state.append({"batch_id": batch.id, "model": args.model, "requests": len(requests), "collected": False})
    state_path.write_text(json.dumps(state, indent=2))
    print(f"submitted batch {batch.id} with {len(requests)} requests (model {args.model})")


def collect(args: argparse.Namespace) -> None:
    import anthropic

    client = anthropic.Anthropic()
    state_path = args.specs / STATE_FILE
    state = json.loads(state_path.read_text())
    for entry in (e for e in state if not e["collected"]):
        while (batch := client.messages.batches.retrieve(entry["batch_id"])).processing_status != "ended":
            print(f"{batch.id}: {batch.processing_status}, {batch.request_counts.processing} processing")
            time.sleep(args.poll_seconds)

        written, problems = 0, []
        for result in client.messages.batches.results(entry["batch_id"]):
            outcome = result.result
            if outcome.type != "succeeded":
                problems.append(f"{result.custom_id}: {outcome.type}")
                continue
            message = outcome.message
            if message.stop_reason in ("refusal", "max_tokens"):
                problems.append(f"{result.custom_id}: stop_reason={message.stop_reason}")
                continue
            text = "".join(block.text for block in message.content if block.type == "text")
            blocks = _FENCE.findall(text)
            if not blocks:
                problems.append(f"{result.custom_id}: no python code block in reply")
                continue
            (args.specs / f"{result.custom_id}.py").write_text(blocks[-1])
            written += 1

        entry["collected"] = True
        state_path.write_text(json.dumps(state, indent=2))
        print(f"{entry['batch_id']}: wrote {written} specs, {len(problems)} problems")
        for line in problems:
            print(f"  {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_submit = sub.add_parser("submit")
    p_submit.add_argument("--candidates", type=Path, required=True)
    p_submit.add_argument("--specs", type=Path, required=True)
    p_submit.add_argument("--model", default=DEFAULT_MODEL)
    p_submit.add_argument("--limit", type=int, default=0)
    p_submit.add_argument("--repair", type=Path, help="rejected.jsonl from proofgrad.build")
    p_collect = sub.add_parser("collect")
    p_collect.add_argument("--specs", type=Path, required=True)
    p_collect.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    {"submit": submit, "collect": collect}[args.command](args)


if __name__ == "__main__":
    main()

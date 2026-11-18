"""Student-facing prompt format and code extraction from completions.

The student never sees the spec: only the task and the function signature.
"""

from __future__ import annotations

import re

_FENCE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.+?)\s*$")

# Added to the prompt in the "spec-first" answer format (H3): the student writes
# the properties of a correct solution, then the code. Only the code is graded.
SPEC_FIRST = (
    "\n\nBefore the code, write a `Properties:` heading and list, one per line, "
    "the properties every correct solution must satisfy."
)


def spec_first_prompt(prompt: str) -> str:
    return prompt.rstrip() + SPEC_FIRST


def spec_first_answer(properties: list[str], code: str) -> str:
    """The answer format the spec-first prompt asks for (used to build SFT targets)."""
    bullets = "".join(f"- {text.strip()}\n" for text in properties)
    return f"Properties:\n{bullets}\n```python\n{code.strip()}\n```"


def stated_properties(completion: str) -> list[str]:
    """Properties a spec-first answer lists before its first code block."""
    head = completion.split("```", 1)[0]
    _, heading, body = head.partition("Properties:")
    if not heading:
        return []
    return [m.group(1) for line in body.splitlines() if (m := _BULLET.match(line))]


def build_prompt(question: str, signature: str, clarifications: list[str] | None = None) -> str:
    """Student prompt. ``clarifications`` state conventions the spec checks that
    the original question leaves implicit (tie-breaking, edge cases), so the
    student is never graded on behavior it could not know about."""
    notes = "".join(f"- {c.strip()}\n" for c in clarifications or [])
    return (
        f"{question.strip()}\n\n"
        + (f"Clarifications:\n{notes}\n" if notes else "")
        + f"Implement this as a Python function with the signature `{signature}`. "
        "Use only the standard library. "
        "Reply with the complete function in a single ```python code block."
    )


def extract_code(completion: str, entry_point: str | None = None) -> str:
    """Return the code to verify from a model completion.

    Prefers the last fenced block defining ``entry_point`` (models often add a
    usage example after the solution); otherwise all blocks joined; otherwise
    the raw text.
    """
    text = _THINK.sub("", completion)
    # In thinking mode the chat template opens <think> in the prompt, so the
    # completion holds only the closing tag: drop the reasoning before it.
    text = text.rsplit("</think>", 1)[-1]
    blocks = _FENCE.findall(text)
    if entry_point is not None:
        defining = [b for b in blocks if re.search(rf"\bdef\s+{re.escape(entry_point)}\s*\(", b)]
        if defining:
            return defining[-1]
    if blocks:
        return "\n\n".join(blocks)
    # An unterminated fence (generation hit the token limit) still yields code.
    start = re.search(r"```(?:python|py)?[ \t]*\n", text)
    return text[start.end():] if start else text

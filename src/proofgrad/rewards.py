"""GRPO reward functions backed by the verifier.

All rewards have the same shape so runs differ only in the rubric:
``w * fraction_passed + (1 - w) * all_passed`` with ``w = PARTIAL_CREDIT``.
The fraction gives dense partial credit; the bonus keeps full correctness the
clear goal. ``w = 0`` is plain pass/fail, which stops GRPO from ranking wrong
answers against each other (see the audit in docs/handoff.md).

Rubrics: ``spec`` (hidden properties), ``tests`` (full unit tests), ``thin``
(the first one or two unit tests) and ``judge`` (full tests plus differential
testing, for monitoring only: see ``proofgrad.judge``).

Signatures follow TRL's convention: ``reward(prompts, completions, **columns)``
where extra dataset columns (``entry_point``, ``spec``, ``unit_tests``, ...)
arrive as lists aligned with ``completions``.
"""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Any

from proofgrad.prompts import extract_code
from proofgrad.verifier import Verdict, verify_many

_CACHE_SIZE = 4096
PARTIAL_CREDIT = 0.5
_cache: OrderedDict[str, Verdict] = OrderedDict()
_lock = threading.Lock()


def completion_text(completion: Any) -> str:
    """TRL passes plain strings for text datasets and message lists for chat datasets."""
    if isinstance(completion, str):
        return completion
    return "".join(message["content"] for message in completion if message.get("role") == "assistant")


def _key(job: dict[str, Any]) -> str:
    raw = "\x00".join(str(job.get(k)) for k in ("code", "entry_point", "spec", "unit_tests"))
    return hashlib.sha256(raw.encode()).hexdigest()


def cached_verify(jobs: list[dict[str, Any]]) -> list[Verdict]:
    """verify_many with an LRU cache: GRPO groups often contain identical completions."""
    keys = [_key(job) for job in jobs]
    with _lock:
        known = {k: _cache[k] for k in keys if k in _cache}
    todo = {k: job for k, job in zip(keys, jobs) if k not in known}
    fresh = dict(zip(todo, verify_many(todo.values()))) if todo else {}
    with _lock:
        for k, verdict in fresh.items():
            _cache[k] = verdict
            _cache.move_to_end(k)
        while len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return [known.get(k) or fresh[k] for k in keys]


def set_partial_credit(weight: float) -> None:
    """Weight of the fraction-passed term for every reward (0 = pass/fail only)."""
    global PARTIAL_CREDIT
    if not 0.0 <= weight <= 1.0:
        raise ValueError("partial credit weight must be in [0, 1]")
    PARTIAL_CREDIT = weight


def _score(fraction: float, all_passed: bool) -> float:
    return PARTIAL_CREDIT * fraction + (1.0 - PARTIAL_CREDIT) * float(all_passed)


def _test_scores(completions: list[Any], entry_point: list[str], tests: list[str]) -> list[float]:
    jobs = [
        {"code": extract_code(completion_text(c), ep), "entry_point": ep, "unit_tests": ut}
        for c, ep, ut in zip(completions, entry_point, tests)
    ]
    return [_score(v.test_score, v.tests_passed) for v in cached_verify(jobs)]


def spec_rubric_reward(prompts: list[Any], completions: list[Any], entry_point: list[str], spec: list[str], **_: Any) -> list[float]:
    jobs = [
        {"code": extract_code(completion_text(c), ep), "entry_point": ep, "spec": sp}
        for c, ep, sp in zip(completions, entry_point, spec)
    ]
    return [_score(v.property_score, v.spec_passed) for v in cached_verify(jobs)]


def unit_test_reward(prompts: list[Any], completions: list[Any], entry_point: list[str], unit_tests: list[str], **_: Any) -> list[float]:
    return _test_scores(completions, entry_point, unit_tests)


def thin_test_reward(prompts: list[Any], completions: list[Any], entry_point: list[str], thin_tests: list[str], **_: Any) -> list[float]:
    return _test_scores(completions, entry_point, thin_tests)


def judge_reward(prompts: list[Any], completions: list[Any], entry_point: list[str], judge_tests: list[str], **_: Any) -> list[float]:
    """Pass/fail by the independent judge. Log it at weight 0; never train on it."""
    jobs = [
        {"code": extract_code(completion_text(c), ep), "entry_point": ep, "unit_tests": ut}
        for c, ep, ut in zip(completions, entry_point, judge_tests)
    ]
    return [float(v.tests_passed) for v in cached_verify(jobs)]


REWARDS = {"spec": spec_rubric_reward, "tests": unit_test_reward, "thin": thin_test_reward, "judge": judge_reward}
# Dataset column each reward needs, besides ``entry_point``.
REWARD_COLUMNS = {"spec": "spec", "tests": "unit_tests", "thin": "thin_tests", "judge": "judge_tests"}

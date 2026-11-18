"""Check candidate code against a spec rubric and/or unit tests in a subprocess.

Candidate code is untrusted model output. Each check runs in a fresh Python
process with its own temp directory, a stripped environment, CPU/file-size
limits and a wall-clock timeout. This contains accidents (infinite loops,
runaway output, crashes); it is not a security boundary against hostile code.
Run training on a machine or container you are willing to lose.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_MAX_EXAMPLES = 100
DEFAULT_PROPERTY_TIMEOUT = 5.0
DEFAULT_TESTS_TIMEOUT = 20.0


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str | None = None


@dataclass(frozen=True)
class Verdict:
    compiled: bool
    error: str | None = None
    properties: list[CheckResult] = field(default_factory=list)
    tests: list[CheckResult] = field(default_factory=list)

    @property
    def property_score(self) -> float:
        """Fraction of rubric properties satisfied (0.0 if nothing ran)."""
        return _fraction(self.properties) if self.compiled and self.error is None else 0.0

    @property
    def test_score(self) -> float:
        """Fraction of unit tests passed (0.0 if nothing ran)."""
        return _fraction(self.tests) if self.compiled and self.error is None else 0.0

    @property
    def spec_passed(self) -> bool:
        return self.compiled and self.error is None and bool(self.properties) and all(p.passed for p in self.properties)

    @property
    def tests_passed(self) -> bool:
        return self.compiled and self.error is None and bool(self.tests) and all(t.passed for t in self.tests)

    def failures(self) -> list[CheckResult]:
        return [c for c in (*self.properties, *self.tests) if not c.passed]


def _fraction(checks: list[CheckResult]) -> float:
    return sum(c.passed for c in checks) / len(checks) if checks else 0.0


def verify(
    code: str,
    entry_point: str,
    *,
    spec: str | None = None,
    unit_tests: str | None = None,
    max_examples: int = DEFAULT_MAX_EXAMPLES,
    property_timeout: float = DEFAULT_PROPERTY_TIMEOUT,
    tests_timeout: float = DEFAULT_TESTS_TIMEOUT,
) -> Verdict:
    """Run ``code`` against ``spec`` properties and/or ``unit_tests``."""
    if spec is None and unit_tests is None:
        raise ValueError("pass a spec, unit tests, or both")
    n_props = spec.count("@prop(") if spec else 0
    wall_timeout = 10.0 + n_props * property_timeout + (tests_timeout if unit_tests else 0.0)
    job = {
        "entry_point": entry_point,
        "spec": spec,
        "unit_tests": unit_tests,
        "max_examples": max_examples,
        "property_timeout": property_timeout,
        "tests_timeout": tests_timeout,
        "cpu_seconds": int(wall_timeout) + 1,
    }

    with tempfile.TemporaryDirectory(prefix="proofgrad_") as tmp:
        workdir = Path(tmp)
        (workdir / "solution.py").write_text(code)
        (workdir / "job.json").write_text(json.dumps(job))
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
        proc = subprocess.Popen(
            [sys.executable, "-m", "proofgrad._runner", tmp],
            cwd=tmp,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            proc.wait(timeout=wall_timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            return Verdict(compiled=False, error="timed out")
        finally:
            _kill_stragglers(proc.pid)

        result_path = workdir / "result.json"
        if not result_path.exists():
            return Verdict(compiled=False, error=f"runner crashed (exit code {proc.returncode})")
        raw: dict[str, Any] = json.loads(result_path.read_text())

    return Verdict(
        compiled=raw["compiled"],
        error=raw["error"],
        properties=[CheckResult(p["name"], p["passed"], p["detail"]) for p in raw["properties"]],
        tests=[CheckResult(t["name"], t["passed"], t["detail"]) for t in raw["tests"]],
    )


def _kill_stragglers(pgid: int) -> None:
    """Kill anything the candidate forked into the runner's process group."""
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def verify_many(jobs: Iterable[dict[str, Any]], workers: int | None = None) -> list[Verdict]:
    """Run ``verify(**job)`` for each job in parallel, preserving order."""
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda job: verify(**job), jobs))

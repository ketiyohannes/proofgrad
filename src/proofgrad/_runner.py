"""Subprocess entry point that checks one candidate. Not imported by the parent.

Usage: python -m proofgrad._runner WORKDIR

WORKDIR contains ``job.json`` and ``solution.py`` (the candidate). Results are
written to ``WORKDIR/result.json`` rather than stdout, so prints from the
candidate cannot corrupt them.
"""

from __future__ import annotations

import copy
import functools
import importlib.util
import inspect
import json
import resource
import signal
import sys
import traceback
from pathlib import Path
from typing import Any

MAX_DETAIL = 400
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_MEMORY_BYTES = 2 * 1024**3


class PropertyTimeout(Exception):
    pass


def _on_alarm(signum: int, frame: Any) -> None:
    raise PropertyTimeout("property exceeded its time budget")


def _limit_self(cpu_seconds: int) -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))
    if sys.platform.startswith("linux"):  # macOS does not enforce RLIMIT_AS
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))


def _short(text: str) -> str:
    return text if len(text) <= MAX_DETAIL else text[:MAX_DETAIL] + "..."


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _copying(func: Any) -> Any:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*copy.deepcopy(args), **copy.deepcopy(kwargs))

    return wrapper


def _bind(prop: Any, f: Any) -> Any:
    """Turn ``check(f, **inputs)`` into a named test taking only ``**inputs``, as @given expects."""

    def test(**inputs: Any) -> None:
        prop.check(f, **inputs)

    test.__name__ = test.__qualname__ = prop.name
    test.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        [inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY) for name in prop.strategies]
    )
    return test


def _run_properties(job: dict[str, Any], workdir: Path, candidate: Any) -> list[dict[str, Any]]:
    from hypothesis import HealthCheck, Phase, given, settings

    from proofgrad.spec_runtime import collect

    (workdir / "spec_module.py").write_text(job["spec"])
    spec_module = _load_module("spec_module", workdir / "spec_module.py")
    f = _copying(candidate)
    budget = float(job["property_timeout"])
    # Skip the shrink phase: we only need pass/fail plus some counterexample,
    # and shrinking a slow candidate can eat the whole time budget.
    profile = settings(
        max_examples=int(job["max_examples"]),
        deadline=None,
        derandomize=True,
        database=None,
        phases=[Phase.explicit, Phase.generate, Phase.target],
        suppress_health_check=list(HealthCheck),
    )

    results = []
    for prop in collect(spec_module):
        checker = profile(given(**prop.strategies)(_bind(prop, f)))
        signal.setitimer(signal.ITIMER_REAL, budget)
        try:
            checker()
            results.append({"name": prop.name, "description": prop.description, "passed": True, "detail": None})
        except BaseException as exc:  # noqa: BLE001 - any failure of the candidate is a rubric miss
            if isinstance(exc, KeyboardInterrupt):
                raise
            detail = f"{type(exc).__name__}: {exc}"
            results.append({"name": prop.name, "description": prop.description, "passed": False, "detail": _short(detail)})
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    return results


def _run_unit_tests(job: dict[str, Any], workdir: Path) -> list[dict[str, Any]]:
    import pytest

    (workdir / "test_solution.py").write_text(job["unit_tests"])
    outcomes: dict[str, dict[str, Any]] = {}

    class Collector:
        def pytest_runtest_logreport(self, report: Any) -> None:
            entry = outcomes.setdefault(report.nodeid, {"name": report.nodeid.split("::", 1)[-1], "passed": True, "detail": None})
            if report.failed:
                entry["passed"] = False
                entry["detail"] = _short(str(report.longrepr).strip().splitlines()[-1] if report.longrepr else "failed")

        def pytest_collectreport(self, report: Any) -> None:
            if report.failed:
                outcomes["<collection>"] = {"name": "<collection>", "passed": False, "detail": _short(str(report.longrepr))}

    signal.setitimer(signal.ITIMER_REAL, float(job["tests_timeout"]))
    try:
        args = [str(workdir / "test_solution.py"), "-q", "--no-header", "-p", "no:cacheprovider"]
        if job.get("fail_fast"):
            args.append("-x")
        pytest.main(args, plugins=[Collector()])
    except PropertyTimeout:
        outcomes["<timeout>"] = {"name": "<timeout>", "passed": False, "detail": "unit tests exceeded their time budget"}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    return list(outcomes.values())


def main() -> None:
    workdir = Path(sys.argv[1])
    job = json.loads((workdir / "job.json").read_text())
    _limit_self(int(job["cpu_seconds"]))
    result: dict[str, Any] = {"compiled": False, "error": None, "properties": [], "tests": []}
    signal.signal(signal.SIGALRM, _on_alarm)
    sys.path.insert(0, str(workdir))
    sys.setrecursionlimit(10_000)

    try:
        signal.setitimer(signal.ITIMER_REAL, float(job["property_timeout"]))
        try:
            solution = _load_module("solution", workdir / "solution.py")
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        candidate = getattr(solution, job["entry_point"], None)
        if not callable(candidate):
            raise LookupError(f"solution does not define a callable named {job['entry_point']!r}")
        result["compiled"] = True
        if job.get("spec"):
            result["properties"] = _run_properties(job, workdir, candidate)
        if job.get("unit_tests"):
            result["tests"] = _run_unit_tests(job, workdir)
    except BaseException as exc:  # noqa: BLE001 - report everything to the parent
        result["error"] = _short("".join(traceback.format_exception_only(type(exc), exc)).strip())

    (workdir / "result.json").write_text(json.dumps(result))


if __name__ == "__main__":
    main()

"""Runtime imported by spec modules.

A spec is a Python module that defines ``ENTRY_POINT`` (the function name the
student must implement) and one or more rubric properties declared with
``@prop``. Each property is checked independently, which gives partial credit:

    from hypothesis import strategies as st
    from proofgrad.spec_runtime import prop

    ENTRY_POINT = "my_max"

    @prop("The result is >= every element.", xs=st.lists(st.integers(), min_size=1))
    def is_upper_bound(f, xs):
        m = f(xs)
        assert all(x <= m for x in xs)

The ``f`` passed to a property deep-copies its arguments on every call, so a
candidate that mutates its input cannot corrupt the values the property
compares against afterwards.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from hypothesis import strategies as st

_MARKER = "__spec_property__"


@dataclass(frozen=True)
class Property:
    name: str
    description: str
    strategies: dict[str, st.SearchStrategy[Any]]
    check: Callable[..., None]


def prop(description: str, **strategies: st.SearchStrategy[Any]) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """Mark ``check(f, **inputs)`` as one rubric property drawn from ``strategies``."""
    if not strategies:
        raise ValueError("a property needs at least one input strategy")

    def decorator(check: Callable[..., None]) -> Callable[..., None]:
        setattr(check, _MARKER, Property(check.__name__, description, strategies, check))
        return check

    return decorator


def collect(module: ModuleType) -> list[Property]:
    """Return the properties declared in ``module``, in definition order."""
    found = [getattr(value, _MARKER) for value in vars(module).values() if hasattr(value, _MARKER)]
    if not found:
        raise ValueError(f"spec module {module.__name__} declares no @prop properties")
    return found

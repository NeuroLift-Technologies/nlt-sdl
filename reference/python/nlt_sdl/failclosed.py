"""
Fail-closed boundary (NLT-SPEC-SDL-1.0.0 R20-R24).

The boundary's job is simple and load-bearing: run an underlying detector, and
if it raises, times out, or returns a value that violates its contract, do NOT
let that turn pass silently. Instead surface a failure the assembler turns into
an escalating ``failClosed`` result. Abstention is always *upward*.

This is the SDL's core value-add over the raw canonical detectors: the canon
produces scores; the boundary guarantees that an *absence* of a usable score
escalates rather than defaulting to safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class GuardOutcome:
    """Result of running one detector behind the fail-closed boundary."""

    value: Optional[dict[str, Any]]
    failed: bool
    note: Optional[str]


def guarded(
    name: str,
    fn: Callable[[dict[str, Any]], dict[str, Any]],
    inp: dict[str, Any],
    validator: Optional[Callable[[Any], None]] = None,
) -> GuardOutcome:
    """Run ``fn(inp)`` behind the boundary.

    On success (and passing ``validator``), returns the value. On *any*
    exception — including injected faults, import failures, timeouts, and
    contract violations raised by the validator — returns a failed outcome
    carrying a PII-free note (R4: only the failing detector name + exception
    type, never message content).
    """
    try:
        value = fn(inp)
        if validator is not None:
            validator(value)
        return GuardOutcome(value=value, failed=False, note=None)
    except Exception as exc:  # noqa: BLE001 - the boundary must catch everything
        return GuardOutcome(
            value=None,
            failed=True,
            note=f"{name}_failclosed:{type(exc).__name__}",
        )


def validate_rrta_raw(value: Any) -> None:
    """Reject malformed RRTA detector output (R20).

    A conformant RRTA raw output is a dict with a finite ``aggregate`` in
    [0,1], a boolean ``self_harm``, and a list ``fields``. Anything else is a
    contract violation that MUST fail closed rather than be coerced.
    """
    if not isinstance(value, dict):
        raise ValueError("rrta raw output is not a dict")
    agg = value.get("aggregate")
    if not isinstance(agg, (int, float)) or isinstance(agg, bool):
        raise ValueError("rrta aggregate is not a number")
    if agg != agg:  # NaN
        raise ValueError("rrta aggregate is NaN")
    if not (0.0 <= float(agg) <= 1.0):
        raise ValueError("rrta aggregate out of range")
    if not isinstance(value.get("self_harm"), bool):
        raise ValueError("rrta self_harm is not a bool")
    if not isinstance(value.get("fields"), list):
        raise ValueError("rrta fields is not a list")


def validate_sleepwalker_raw(value: Any) -> None:
    """Reject malformed Sleepwalker detector output (R20)."""
    if not isinstance(value, dict):
        raise ValueError("sleepwalker raw output is not a dict")
    for key in ("vulnerable", "crisis"):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"sleepwalker {key} is not a bool")
    for key in ("events", "signals"):
        if not isinstance(value.get(key), list):
            raise ValueError(f"sleepwalker {key} is not a list")

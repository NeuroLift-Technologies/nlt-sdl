"""
NLT-SDL Python reference implementation (NLT-SPEC-SDL-1.0.0).

One conformant implementation of the State Detection Layer. It wraps the
canonical rrt-advocate and sleepwalker detectors behind the SDL contract and
guards them with the fail-closed boundary.

Conformance entrypoint: ``run_vector(input) -> dict`` returns a schema-valid
``DetectionResult`` for a single observed turn.
"""

from __future__ import annotations

from typing import Any

from .adapters import detect_rrta, detect_sleepwalker, tier_ranges
from .contract import SCHEMA_VERSION, assemble
from .failclosed import guarded, validate_rrta_raw, validate_sleepwalker_raw

__all__ = ["run_vector", "observe", "SCHEMA_VERSION"]


def run_vector(inp: dict[str, Any]) -> dict[str, Any]:
    """Run one turn through the SDL and return a schema-valid result dict.

    Each shape detector runs behind the fail-closed boundary. If either fails,
    the result is marked ``meta.failClosed`` and escalates (abstain upward).
    Routing-critical guarantees hold even when a detector is down:
      * an explicit RRTA signal still escalates even if Sleepwalker fails (R22)
      * a total outage still escalates via emergency_human_routing (R22/R23)
    """
    rrta_outcome = guarded("rrta", detect_rrta, inp, validator=validate_rrta_raw)
    sw_outcome = guarded(
        "sleepwalker", detect_sleepwalker, inp, validator=validate_sleepwalker_raw
    )

    notes: list[str] = []
    for outcome in (rrta_outcome, sw_outcome):
        if outcome.note:
            notes.append(outcome.note)

    fail_closed = rrta_outcome.failed or sw_outcome.failed

    result = assemble(
        rrta_raw=rrta_outcome.value,
        sw_raw=sw_outcome.value,
        fail_closed=fail_closed,
        notes=notes,
        ranges=tier_ranges(),
    )
    return result.to_dict()


# Convenience alias mirroring the host-facing verb used in the repo README.
def observe(**kwargs: Any) -> dict[str, Any]:
    """Host-friendly wrapper: ``observe(message=..., model=..., ...)``."""
    return run_vector(dict(kwargs))

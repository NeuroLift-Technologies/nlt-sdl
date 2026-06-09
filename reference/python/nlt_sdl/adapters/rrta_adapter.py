"""
RRTA adapter — wraps rrt-advocate's canonical 3-layer CrisisDetector.

It does NOT reimplement detection. It calls the canonical detector, reads its
``CrisisIndicators``, and returns the coarse raw shape the contract assembler
consumes. Tier ranges are loaded from the canonical
``config/crisis_thresholds.yaml`` so the SDL never invents thresholds.

Fault injection (``input.inject``) lets the conformance suite exercise the
fail-closed boundary without modifying canonical source.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

from .. import _canon
from ..contract import CANONICAL_TIER_RANGES

_TIER_NAMES = ("green", "yellow", "orange", "red", "black")


def load_tier_ranges() -> list[tuple[str, float, float]]:
    """Load canonical tier ranges from crisis_thresholds.yaml.

    Falls back to the documented constants only if the YAML cannot be read; the
    SDL consumes canon, it does not own these numbers.
    """
    try:
        import yaml  # local import: optional at contract level

        yaml_path = os.path.join(
            os.path.dirname(_canon.rrta_src()), "config", "crisis_thresholds.yaml"
        )
        with open(yaml_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        levels = data["crisis_levels"]
        ranges: list[tuple[str, float, float]] = []
        for name in _TIER_NAMES:
            lo, hi = levels[name]["threshold_range"]
            ranges.append((name, float(lo), float(hi)))
        return ranges
    except Exception:
        return CANONICAL_TIER_RANGES


def detect_rrta(inp: dict[str, Any]) -> dict[str, Any]:
    """Return the coarse RRTA raw shape for the contract assembler.

    Output: ``{"aggregate": float, "self_harm": bool, "fields": list[str]}``.
    Raises on injected faults or any real import/execution failure so the
    boundary can fail closed.
    """
    inject = inp.get("inject") or {}
    if inject.get("rrtaError"):
        raise RuntimeError("injected rrta error")
    if inject.get("rrtaTimeout"):
        raise TimeoutError("injected rrta timeout")
    if inject.get("malformedRrta"):
        # Simulate a detector that returned an unusable value. The boundary's
        # validator must reject this (R20) rather than coerce it.
        return {"aggregate": float("nan"), "self_harm": "no", "fields": "oops"}

    _canon.ensure_rrta()
    from crisis.detectors.crisis_detector import CrisisDetector  # type: ignore

    detector = CrisisDetector()
    message = inp.get("message") or ""
    indicators = asyncio.run(detector.detect_crisis_indicators(message))

    return {
        "aggregate": float(indicators.aggregate_confidence),
        "self_harm": bool(indicators.self_harm_risk),
        "fields": list(indicators.detected_semantic_fields),
    }


# Cached ranges so the YAML is read once per process.
_RANGES_CACHE: Optional[list[tuple[str, float, float]]] = None


def tier_ranges() -> list[tuple[str, float, float]]:
    global _RANGES_CACHE
    if _RANGES_CACHE is None:
        _RANGES_CACHE = load_tier_ranges()
    return _RANGES_CACHE

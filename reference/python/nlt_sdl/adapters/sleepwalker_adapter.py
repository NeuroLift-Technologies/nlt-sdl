"""
Sleepwalker adapter — wraps the canonical sleepwalker StateDetector and derives
deterministic continuity events from host facts.

Two sources feed the Sleepwalker shape:
  * Protective-state detection (dissociation / numbing / avoidance / detachment)
    and crisis indicators come from the canonical ``StateDetector`` (wrapped).
  * Deterministic continuity events (model/version change, handoff, memory gap,
    tone shift, new session) are derived here by diffing the turn's host facts
    against the prior turn's facts. These are facts, not guesses, and bypass any
    confidence floor (R14).
"""

from __future__ import annotations

from typing import Any

from .. import _canon
from ..contract import RUPTURE_EVENTS

# A memory gap longer than this (seconds) is treated as a continuity rupture.
MEMORY_GAP_SECONDS = 7 * 24 * 60 * 60  # 7 days


def compute_events(inp: dict[str, Any]) -> list[str]:
    """Derive deterministic continuity events from host facts (R14)."""
    events: list[str] = []
    prior = inp.get("prior") or {}

    if inp.get("newSession"):
        events.append("new_session")
    if prior.get("model") and inp.get("model") and prior["model"] != inp["model"]:
        events.append("model_change")
    if prior.get("version") and inp.get("version") and prior["version"] != inp["version"]:
        events.append("version_change")
    if inp.get("handoff"):
        events.append("handoff")
    if prior.get("tone") and inp.get("tone") and prior["tone"] != inp["tone"]:
        events.append("tone_shift")
    gap = inp.get("gapSeconds")
    if isinstance(gap, (int, float)) and not isinstance(gap, bool) and gap > MEMORY_GAP_SECONDS:
        events.append("memory_gap")
    return events


def detect_sleepwalker(inp: dict[str, Any]) -> dict[str, Any]:
    """Return the coarse Sleepwalker raw shape for the contract assembler.

    Output: ``{"vulnerable": bool, "events": list[str], "signals": list[str],
    "crisis": bool}``. Raises on injected faults or real failures so the
    boundary can fail closed.
    """
    inject = inp.get("inject") or {}
    if inject.get("sleepwalkerError"):
        raise RuntimeError("injected sleepwalker error")

    events = compute_events(inp)
    rupture = bool(set(events) & RUPTURE_EVENTS)

    _canon.ensure_sleepwalker()
    from sleepwalker_protocol.state_detection import StateDetector  # type: ignore

    detector = StateDetector()
    message = inp.get("message") or ""
    state = detector.detect(message)

    signals: list[str] = []
    if state.protective and state.state_type and state.state_type != "neutral":
        signals.append(state.state_type)

    crisis = bool(
        state.explicit_suicidal_ideation
        or state.self_harm_indicators
        or state.inability_to_ensure_safety
    )

    return {
        "vulnerable": bool(state.protective) or rupture,
        "events": events,
        "signals": signals,
        "crisis": crisis,
    }

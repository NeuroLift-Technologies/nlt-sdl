"""
NLT-SDL contract types and routing policy (NLT-SPEC-SDL-1.0.0).

This module is the *policy brain* of the State Detection Layer. It is pure and
host-agnostic: it knows nothing about how the underlying RRTA / Sleepwalker
detectors work. It takes their coarse outputs and assembles a schema-valid
``DetectionResult``, enforcing the spec's safety invariants:

  * R2  — tier is always derived from confidence via the canonical ranges
  * R11 — soft signals alone never reach red/black (confidence clamped below red)
  * R12 — an explicit hard-distress signal forces tier=black + escalate
  * R16 — a Sleepwalker crisis indicator escalates
  * R17/R18 — Enabler is reserved (risk=none) in 1.0.0
  * R19 — uncertainty yields a gentle posture (preserve_choice + slow pacing)
  * R21/R22 — fail-closed escalates and never downgrades (abstain upward)

It deliberately does NOT redefine tiers, weights, or lexicons. Those live in
rrt-advocate canon and are consumed by the adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

SCHEMA_VERSION = "1.0.0"

# Canonical green->black ordering.
TIER_ORDER = ["green", "yellow", "orange", "red", "black"]

# Canonical tier ranges. These MIRROR rrt-advocate config/crisis_thresholds.yaml
# and MUST NOT be reinvented. The rrta_adapter loads the authoritative values
# from canon when available and passes them in; these are the documented
# fallback used only when canon's YAML cannot be read.
CANONICAL_TIER_RANGES: list[tuple[str, float, float]] = [
    ("green", 0.0, 0.2),
    ("yellow", 0.2, 0.4),
    ("orange", 0.4, 0.7),
    ("red", 0.7, 0.9),
    ("black", 0.9, 1.0),
]

# Crisis tier (red/black) requires an explicit signal (README safety invariant
# #2). Non-explicit confidence is clamped just below this so it can never derive
# a red/black tier.
RED_THRESHOLD = 0.7

# Sleepwalker events that indicate a continuity rupture (vs routine new_session).
RUPTURE_EVENTS = frozenset(
    {"model_change", "version_change", "handoff", "memory_gap", "tone_shift"}
)

CONSTRAINTS_BY_MODE: dict[str, list[str]] = {
    "standard": [],
    "rrta_soft_scaffold": [
        "reduce_to_one_next_step",
        "no_large_lists",
        "preserve_choice",
        "avoid_shame_language",
        "slow_pace",
    ],
    "rrta_stabilize": [
        "reduce_to_one_next_step",
        "preserve_choice",
        "slow_pace",
        "offer_human_support",
    ],
    "rrta_crisis_human_routing": [
        "offer_human_support",
        "surface_crisis_resources",
        "preserve_choice",
        "slow_pace",
    ],
    "emergency_human_routing": [
        "offer_human_support",
        "surface_crisis_resources",
        "preserve_choice",
        "slow_pace",
    ],
    "sleepwalker_reorient": ["confirm_continuity", "preserve_choice", "slow_pace"],
    "sleepwalker_reconsent": ["reaffirm_consent", "preserve_choice"],
    "enabler_agency_support": ["encourage_self_direction", "preserve_choice"],
}


def tier_index(tier: str) -> int:
    return TIER_ORDER.index(tier)


def derive_tier(
    confidence: float,
    ranges: list[tuple[str, float, float]] = CANONICAL_TIER_RANGES,
) -> str:
    """Map a confidence in [0,1] to a canonical tier (R2).

    Ranges are half-open ``[lo, hi)`` except the top tier, which is inclusive of
    1.0 so a forced 1.0 (self-harm) always lands on black.
    """
    c = max(0.0, min(1.0, float(confidence)))
    last = len(ranges) - 1
    for i, (name, lo, hi) in enumerate(ranges):
        if c >= lo and (c < hi or i == last):
            return name
    return ranges[last][0]


@dataclass
class RrtaResult:
    tier: str
    confidence: float
    signals: list[str]
    explicit_signal: bool


@dataclass
class SleepwalkerResult:
    vulnerable: bool
    events: list[str]
    signals: list[str]


@dataclass
class EnablerResult:
    """Reserved in 1.0.0 (R17/R18): contract-normative, no implementation ships."""

    risk: str = "none"
    confidence: float = 0.0
    agency_trend: float = 0.0
    signals: list[str] = field(default_factory=list)


@dataclass
class Meta:
    fail_closed: bool
    notes: list[str]
    schema_version: str = SCHEMA_VERSION


@dataclass
class DetectionResult:
    rrta: RrtaResult
    sleepwalker: SleepwalkerResult
    enabler: EnablerResult
    recommended_mode: str
    response_constraints: list[str]
    escalate_to_human: bool
    meta: Meta
    suggested_persona: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "rrta": {
                "tier": self.rrta.tier,
                "confidence": round(float(self.rrta.confidence), 4),
                "signals": list(self.rrta.signals),
                "explicitSignal": bool(self.rrta.explicit_signal),
            },
            "sleepwalker": {
                "vulnerable": bool(self.sleepwalker.vulnerable),
                "events": list(self.sleepwalker.events),
                "signals": list(self.sleepwalker.signals),
            },
            "enabler": {
                "risk": self.enabler.risk,
                "confidence": round(float(self.enabler.confidence), 4),
                "agencyTrend": round(float(self.enabler.agency_trend), 4),
                "signals": list(self.enabler.signals),
            },
            "recommendedMode": self.recommended_mode,
            "responseConstraints": list(self.response_constraints),
            "escalateToHuman": bool(self.escalate_to_human),
            "meta": {
                "failClosed": bool(self.meta.fail_closed),
                "schemaVersion": self.meta.schema_version,
                "notes": list(self.meta.notes),
            },
        }
        if self.suggested_persona is not None:
            out["suggestedPersona"] = self.suggested_persona
        return out


def assemble(
    rrta_raw: Optional[dict[str, Any]],
    sw_raw: Optional[dict[str, Any]],
    fail_closed: bool,
    notes: Optional[list[str]] = None,
    ranges: list[tuple[str, float, float]] = CANONICAL_TIER_RANGES,
) -> DetectionResult:
    """Assemble the final DetectionResult from coarse shape outputs.

    ``rrta_raw``  : {"aggregate": float, "self_harm": bool, "fields": list[str]}
                    or None if the RRTA detector was unusable.
    ``sw_raw``    : {"vulnerable": bool, "events": list[str], "signals": list[str],
                    "crisis": bool} or None if the Sleepwalker detector failed.
    ``fail_closed``: True if the orchestrator already tripped the boundary.

    A None shape forces fail-closed and abstains upward (R20/R21).
    """
    notes = list(notes or [])

    # ---- RRTA shape ------------------------------------------------------
    if rrta_raw is None:
        # Detector unusable: abstain upward — assume the worst, route to human.
        rrta = RrtaResult(tier="black", confidence=1.0, signals=[], explicit_signal=False)
        fail_closed = True
    else:
        explicit = bool(rrta_raw["self_harm"])
        if explicit:
            confidence = 1.0
            tier = "black"  # R12
        else:
            raw = float(rrta_raw["aggregate"])
            # R11: a non-explicit turn can never claim crisis-level confidence.
            confidence = min(max(raw, 0.0), RED_THRESHOLD - 0.01)
            if raw >= RED_THRESHOLD:
                notes.append("rrta_confidence_clamped_below_red_no_explicit_signal")
            tier = derive_tier(confidence, ranges)
        rrta = RrtaResult(
            tier=tier,
            confidence=confidence,
            signals=list(rrta_raw["fields"]),
            explicit_signal=explicit,
        )

    # ---- Sleepwalker shape ----------------------------------------------
    sw_crisis = False
    if sw_raw is None:
        sleepwalker = SleepwalkerResult(vulnerable=True, events=[], signals=[])
        fail_closed = True
    else:
        sleepwalker = SleepwalkerResult(
            vulnerable=bool(sw_raw["vulnerable"]),
            events=list(sw_raw["events"]),
            signals=list(sw_raw["signals"]),
        )
        sw_crisis = bool(sw_raw["crisis"])

    # ---- Enabler (reserved) ---------------------------------------------
    enabler = EnablerResult()  # R17/R18

    # ---- Escalation (R12, R16, R21, R22) --------------------------------
    escalate = rrta.explicit_signal or sw_crisis or fail_closed

    # ---- Routing mode ----------------------------------------------------
    crisis = rrta.explicit_signal or sw_crisis
    if fail_closed and not crisis:
        mode = "emergency_human_routing"
    elif crisis:
        mode = "rrta_crisis_human_routing"
    elif rrta.signals:
        mode = "rrta_soft_scaffold"  # R19: gentle when soft signals present
    elif (set(sleepwalker.events) & RUPTURE_EVENTS) or sleepwalker.vulnerable:
        mode = "sleepwalker_reorient"
    else:
        mode = "standard"

    constraints = list(CONSTRAINTS_BY_MODE[mode])
    meta = Meta(fail_closed=fail_closed, notes=notes)
    return DetectionResult(
        rrta=rrta,
        sleepwalker=sleepwalker,
        enabler=enabler,
        recommended_mode=mode,
        response_constraints=constraints,
        escalate_to_human=escalate,
        meta=meta,
    )

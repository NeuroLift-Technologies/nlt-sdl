"""Unit tests for the pure contract policy (no canon required)."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from nlt_sdl.contract import (  # noqa: E402
    CANONICAL_TIER_RANGES,
    RED_THRESHOLD,
    assemble,
    derive_tier,
)


def test_derive_tier_canonical_boundaries():
    assert derive_tier(0.0) == "green"
    assert derive_tier(0.19) == "green"
    assert derive_tier(0.2) == "yellow"
    assert derive_tier(0.39) == "yellow"
    assert derive_tier(0.4) == "orange"
    assert derive_tier(0.69) == "orange"
    assert derive_tier(0.7) == "red"
    assert derive_tier(0.89) == "red"
    assert derive_tier(0.9) == "black"
    assert derive_tier(1.0) == "black"


def test_explicit_signal_forces_black_and_escalation():
    # R12: explicit self-harm forces black + escalate regardless of aggregate.
    rrta_raw = {"aggregate": 0.0, "self_harm": True, "fields": ["self_harm_risk"]}
    sw_raw = {"vulnerable": False, "events": [], "signals": [], "crisis": False}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["rrta"]["tier"] == "black"
    assert result["rrta"]["explicitSignal"] is True
    assert result["escalateToHuman"] is True
    assert result["recommendedMode"] == "rrta_crisis_human_routing"


def test_soft_signal_confidence_clamped_below_red():
    # R11: a high aggregate without an explicit signal cannot reach red/black.
    rrta_raw = {"aggregate": 0.95, "self_harm": False, "fields": ["overwhelm"]}
    sw_raw = {"vulnerable": False, "events": [], "signals": [], "crisis": False}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["rrta"]["confidence"] < RED_THRESHOLD
    assert result["rrta"]["tier"] in ("green", "yellow", "orange")
    assert result["rrta"]["tier"] != "red"
    assert result["rrta"]["tier"] != "black"
    assert result["escalateToHuman"] is False
    assert "rrta_confidence_clamped_below_red_no_explicit_signal" in result["meta"]["notes"]


def test_benign_is_standard_and_silent():
    rrta_raw = {"aggregate": 0.0, "self_harm": False, "fields": []}
    sw_raw = {"vulnerable": False, "events": [], "signals": [], "crisis": False}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["rrta"]["tier"] == "green"
    assert result["recommendedMode"] == "standard"
    assert result["responseConstraints"] == []
    assert result["escalateToHuman"] is False


def test_sleepwalker_crisis_escalates():
    # R16
    rrta_raw = {"aggregate": 0.0, "self_harm": False, "fields": []}
    sw_raw = {"vulnerable": True, "events": [], "signals": [], "crisis": True}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["escalateToHuman"] is True


def test_enabler_reserved():
    # R17/R18: reserved, always none/low/0 in 1.0.0.
    rrta_raw = {"aggregate": 0.0, "self_harm": False, "fields": []}
    sw_raw = {"vulnerable": False, "events": [], "signals": [], "crisis": False}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["enabler"]["risk"] == "none"
    assert result["enabler"]["agencyTrend"] == 0


def test_rupture_event_sets_reorient():
    rrta_raw = {"aggregate": 0.0, "self_harm": False, "fields": []}
    sw_raw = {"vulnerable": True, "events": ["model_change"], "signals": [], "crisis": False}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["recommendedMode"] == "sleepwalker_reorient"
    assert "confirm_continuity" in result["responseConstraints"]


def test_gentle_posture_on_soft_signals():
    # R19: soft signals present -> gentle scaffold with preserve_choice + slow pacing.
    rrta_raw = {"aggregate": 0.1, "self_harm": False, "fields": ["overwhelm"]}
    sw_raw = {"vulnerable": False, "events": [], "signals": [], "crisis": False}
    result = assemble(rrta_raw, sw_raw, fail_closed=False).to_dict()
    assert result["recommendedMode"] == "rrta_soft_scaffold"
    assert "preserve_choice" in result["responseConstraints"]
    assert "slow_pace" in result["responseConstraints"]


def test_canonical_ranges_have_five_tiers():
    assert [r[0] for r in CANONICAL_TIER_RANGES] == [
        "green",
        "yellow",
        "orange",
        "red",
        "black",
    ]

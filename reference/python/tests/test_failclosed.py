"""Unit tests for the fail-closed boundary and abstain-upward assembly.

These are the mandatory safety tests (R20-R24). They must exercise real failure
paths — never a green stub.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from nlt_sdl.contract import assemble  # noqa: E402
from nlt_sdl.failclosed import (  # noqa: E402
    guarded,
    validate_rrta_raw,
    validate_sleepwalker_raw,
)


def _ok_rrta(_inp):
    return {"aggregate": 0.0, "self_harm": False, "fields": []}


def _boom(_inp):
    raise RuntimeError("kaboom")


def test_guarded_passes_through_success():
    outcome = guarded("rrta", _ok_rrta, {}, validator=validate_rrta_raw)
    assert outcome.failed is False
    assert outcome.note is None
    assert outcome.value == {"aggregate": 0.0, "self_harm": False, "fields": []}


def test_guarded_catches_exception_with_pii_free_note():
    outcome = guarded("rrta", _boom, {"message": "secret content"}, validator=validate_rrta_raw)
    assert outcome.failed is True
    assert outcome.value is None
    assert outcome.note == "rrta_failclosed:RuntimeError"
    assert "secret content" not in outcome.note  # R4: no message content in notes


def test_validator_rejects_malformed_rrta():
    for bad in (
        {"aggregate": "nope", "self_harm": False, "fields": []},
        {"aggregate": float("nan"), "self_harm": False, "fields": []},
        {"aggregate": 2.0, "self_harm": False, "fields": []},
        {"aggregate": 0.5, "self_harm": "yes", "fields": []},
        {"aggregate": 0.5, "self_harm": False, "fields": "oops"},
        "not even a dict",
    ):
        with pytest.raises(Exception):
            validate_rrta_raw(bad)


def test_validator_rejects_malformed_sleepwalker():
    for bad in (
        {"vulnerable": "yes", "events": [], "signals": [], "crisis": False},
        {"vulnerable": False, "events": "x", "signals": [], "crisis": False},
        {"vulnerable": False, "events": [], "signals": [], "crisis": "no"},
    ):
        with pytest.raises(Exception):
            validate_sleepwalker_raw(bad)


def test_rrta_failure_abstains_upward():
    # R20/R21: a None RRTA shape forces fail-closed escalation.
    sw_raw = {"vulnerable": False, "events": [], "signals": [], "crisis": False}
    result = assemble(rrta_raw=None, sw_raw=sw_raw, fail_closed=True).to_dict()
    assert result["meta"]["failClosed"] is True
    assert result["escalateToHuman"] is True


def test_total_outage_routes_to_emergency():
    # R22/R23: both shapes down still escalates with emergency routing.
    result = assemble(rrta_raw=None, sw_raw=None, fail_closed=True).to_dict()
    assert result["meta"]["failClosed"] is True
    assert result["escalateToHuman"] is True
    assert result["recommendedMode"] == "emergency_human_routing"


def test_explicit_signal_survives_partial_failure():
    # R22: explicit RRTA signal escalates even when Sleepwalker is down.
    rrta_raw = {"aggregate": 1.0, "self_harm": True, "fields": ["self_harm_risk"]}
    result = assemble(rrta_raw=rrta_raw, sw_raw=None, fail_closed=True).to_dict()
    assert result["rrta"]["tier"] == "black"
    assert result["rrta"]["explicitSignal"] is True
    assert result["escalateToHuman"] is True
    assert result["meta"]["failClosed"] is True


def test_failclosed_never_downgrades_crisis_mode():
    # R21: with a real crisis present, fail-closed routes to crisis, not a soft mode.
    rrta_raw = {"aggregate": 1.0, "self_harm": True, "fields": ["self_harm_risk"]}
    result = assemble(rrta_raw=rrta_raw, sw_raw=None, fail_closed=True).to_dict()
    assert result["recommendedMode"] == "rrta_crisis_human_routing"

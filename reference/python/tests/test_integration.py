"""End-to-end integration tests against the canonical detectors.

These require the sibling rrt-advocate and sleepwalker checkouts (via env vars
RRT_ADVOCATE_SRC / SLEEPWALKER_ROOT or sibling directories). When canon is not
available they are skipped — but the fault-injection paths, which never reach
canon, are always exercised.
"""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from nlt_sdl import _canon, run_vector  # noqa: E402


def _canon_available() -> bool:
    return os.path.isdir(_canon.rrta_src()) and os.path.isdir(_canon.sleepwalker_root())


canon = pytest.mark.skipif(not _canon_available(), reason="canonical sources not available")


@canon
def test_benign_turn_is_green_and_standard():
    result = run_vector({"message": "can you help me plan my week?"})
    assert result["rrta"]["tier"] == "green"
    assert result["escalateToHuman"] is False
    assert result["meta"]["failClosed"] is False


@canon
def test_explicit_self_harm_escalates_black():
    result = run_vector({"message": "i don't want to be here anymore"})
    assert result["rrta"]["tier"] == "black"
    assert result["rrta"]["explicitSignal"] is True
    assert result["escalateToHuman"] is True


@canon
def test_soft_overwhelm_does_not_escalate():
    result = run_vector({"message": "everything is too much, i can't cope right now"})
    assert result["rrta"]["explicitSignal"] is False
    assert result["escalateToHuman"] is False


@canon
def test_sleepwalker_protective_state_is_vulnerable():
    result = run_vector({"message": "i feel numb and detached, kind of disconnected"})
    assert result["sleepwalker"]["vulnerable"] is True
    assert result["escalateToHuman"] is False


def test_injected_total_outage_escalates_without_canon():
    # No canon needed: injected faults short-circuit before any import.
    result = run_vector(
        {"message": "anything", "inject": {"rrtaError": True, "sleepwalkerError": True}}
    )
    assert result["meta"]["failClosed"] is True
    assert result["escalateToHuman"] is True
    assert result["recommendedMode"] == "emergency_human_routing"

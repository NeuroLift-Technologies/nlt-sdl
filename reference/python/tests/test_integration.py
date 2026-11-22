"""Integration tests for the installed canonical detectors and their failure boundary."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from nlt_sdl import run_vector  # noqa: E402


def test_benign_turn_is_green_and_standard():
    result = run_vector({"message": "can you help me plan my week?"})
    assert result["rrta"]["tier"] == "green"
    assert result["escalateToHuman"] is False
    assert result["meta"]["failClosed"] is False


def test_explicit_self_harm_escalates_black():
    result = run_vector({"message": "i don't want to be here anymore"})
    assert result["rrta"]["tier"] == "black"
    assert result["rrta"]["explicitSignal"] is True
    assert result["escalateToHuman"] is True


def test_soft_overwhelm_does_not_escalate():
    result = run_vector({"message": "everything is too much, i can't cope right now"})
    assert result["rrta"]["explicitSignal"] is False
    assert result["escalateToHuman"] is False


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


def test_missing_detector_packages_fail_closed(monkeypatch):
    for module in ("rrt_advocate", "sleepwalker_protocol", "sleepwalker_protocol.state_detection"):
        monkeypatch.setitem(sys.modules, module, None)

    result = run_vector({"message": "can you help me plan my week?"})

    assert result["meta"]["failClosed"] is True
    assert result["escalateToHuman"] is True
    assert result["recommendedMode"] == "emergency_human_routing"

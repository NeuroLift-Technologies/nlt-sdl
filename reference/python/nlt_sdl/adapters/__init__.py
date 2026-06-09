"""Reference adapters that wrap canonical detectors behind the SDL contract."""

from .rrta_adapter import detect_rrta, tier_ranges
from .sleepwalker_adapter import detect_sleepwalker

__all__ = ["detect_rrta", "detect_sleepwalker", "tier_ranges"]

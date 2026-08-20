"""Neutral training scores."""

from __future__ import annotations


def dwell_score(time_in_target_s: float, duration_s: float) -> float:
    if duration_s <= 0:
        return 0.0
    return max(0.0, min(100.0, time_in_target_s / duration_s * 100.0))

"""Normalize dictionary/object samples without fabricating unavailable fields."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.models import BoardSample


def _value(source: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in source:
            return source[name]
    return None


def normalize_sample(raw: Any, sequence: int, cop_unit: str = "unknown") -> BoardSample:
    """Map a driver sample to the common contract, preserving missing values as ``None``."""
    if isinstance(raw, Mapping):
        data = raw
    elif hasattr(raw, "__dict__"):
        data = vars(raw)
    else:
        raise TypeError(f"Nieobsługiwany typ próbki: {type(raw)!r}")
    return BoardSample(
        timestamp_monotonic=float(
            _value(data, "timestamp_monotonic", "monotonic") or time.monotonic()
        ),
        timestamp_wall=str(
            _value(data, "timestamp_wall", "timestamp") or datetime.now(UTC).isoformat()
        ),
        top_left=_value(data, "top_left", "tl"),
        top_right=_value(data, "top_right", "tr"),
        bottom_left=_value(data, "bottom_left", "bl"),
        bottom_right=_value(data, "bottom_right", "br"),
        total_weight_kg=_value(data, "total_weight_kg", "weight", "weight_kg"),
        cop_x=_value(data, "cop_x", "x"),
        cop_y=_value(data, "cop_y", "y"),
        sequence_number=sequence,
        connection_ok=bool(
            _value(data, "connection_ok", "connected")
            if _value(data, "connection_ok", "connected") is not None
            else True
        ),
        cop_unit=str(_value(data, "cop_unit", "unit") or cop_unit),
    )

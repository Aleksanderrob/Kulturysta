"""Fault-tolerant JSON configuration loading."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.constants import DEFAULT_MINIMUM_LOAD_KG

DEFAULT_CONFIG: dict[str, Any] = {
    "backend": "simulator",
    "measurement_duration_s": 30,
    "training_duration_s": 60,
    "minimum_load_kg": DEFAULT_MINIMUM_LOAD_KG,
    "visualization": {"scale_mode": "fixed", "fixed_range": 1.0, "path_points": 750},
    "sound": {"enabled": False, "volume": 0.35},
    "filter": {"kind": "moving_average", "window": 5, "order": 4, "cutoff_hz": 5.0},
    "adaptation": {"minimum_radius": 0.05, "maximum_radius": 0.4, "step_percent": 10},
    "paths": {"data": "data"},
    "report": {"include_personal_data": False},
    "second_screen": {"enabled": False},
}


def load_config(path: Path = Path("config/default_config.json")) -> dict[str, Any]:
    """Load configuration, recreating defaults when the file is missing or invalid."""
    logger = logging.getLogger(__name__)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise TypeError("root must be an object")
        merged = deepcopy(DEFAULT_CONFIG)
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Nie można wczytać konfiguracji %s: %s; używam domyślnej.", path, exc)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        return deepcopy(DEFAULT_CONFIG)

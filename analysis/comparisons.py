"""Session-to-session numerical comparisons."""

from __future__ import annotations

from typing import Any


def compare_metric_series(
    records: list[dict[str, Any]], metric_names: list[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        previous = records[index - 1] if index else None
        for name in metric_names:
            value = record.get("metrics", {}).get(name)
            previous_value = previous.get("metrics", {}).get(name) if previous else None
            absolute = (
                value - previous_value
                if isinstance(value, (int, float)) and isinstance(previous_value, (int, float))
                else None
            )
            percent = (
                absolute / previous_value * 100
                if absolute is not None and previous_value not in (None, 0)
                else None
            )
            direction = "brak porównania"
            if absolute is not None:
                direction = (
                    "brak istotnej różnicy numerycznej"
                    if abs(absolute) < 1e-12
                    else ("wzrost" if absolute > 0 else "spadek")
                )
            rows.append(
                {
                    "session_id": record.get("session_id"),
                    "metric": name,
                    "value": value,
                    "absolute_change": absolute,
                    "percent_change": percent,
                    "direction": direction,
                }
            )
    return rows

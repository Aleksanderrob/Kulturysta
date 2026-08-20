"""Polish-Excel-friendly semicolon CSV export."""

from __future__ import annotations

import csv
from pathlib import Path

from app.models import BoardSample

SAMPLE_COLUMNS = [
    "timestamp_monotonic",
    "timestamp_wall",
    "sequence_number",
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "total_weight_kg",
    "raw_total_weight_kg",
    "cop_x",
    "cop_y",
    "raw_cop_x",
    "raw_cop_y",
    "filtered_cop_x",
    "filtered_cop_y",
    "cop_unit",
    "connection_ok",
    "synthetic_data",
    "quality_flags",
]


def export_csv(samples: list[BoardSample], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SAMPLE_COLUMNS, delimiter=";")
        writer.writeheader()
        for sample in samples:
            row = sample.to_dict()
            row["quality_flags"] = "|".join(row["quality_flags"])
            writer.writerow({key: row.get(key) for key in SAMPLE_COLUMNS})
    return path

"""Atomic session persistence orchestrator."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from app.models import BoardSample, SessionArtifacts, SessionMetadata
from storage.csv_exporter import export_csv
from storage.excel_exporter import export_excel
from storage.markdown_report import export_markdown
from storage.paths import DataPaths
from storage.pdf_report import export_pdf


class SessionRepository:
    def __init__(self, paths: DataPaths | None = None) -> None:
        self.paths = (paths or DataPaths()).ensure()

    def save(
        self,
        metadata: SessionMetadata,
        raw_samples: list[BoardSample],
        processed_samples: list[BoardSample],
        include_personal_data: bool = False,
        create_pdf: bool = False,
    ) -> SessionArtifacts:
        session_dir = self.paths.sessions / metadata.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        csv_path = export_csv(processed_samples, session_dir / "samples.csv")
        xlsx_path = export_excel(
            metadata, raw_samples, processed_samples, session_dir / "session.xlsx"
        )
        json_path = session_dir / "metadata.json"
        json_path.write_text(
            json.dumps(
                metadata.to_dict(include_personal_data),
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        markdown_path = export_markdown(metadata, session_dir / "report.md", include_personal_data)
        pdf_path = (
            export_pdf(
                metadata, processed_samples, session_dir / "report.pdf", include_personal_data
            )
            if create_pdf
            else None
        )
        return SessionArtifacts(
            session_dir, csv_path, xlsx_path, json_path, markdown_path, pdf_path
        )

    def create_pdf(
        self,
        metadata: SessionMetadata,
        samples: list[BoardSample],
        include_personal_data: bool = False,
    ) -> Path:
        return export_pdf(
            metadata,
            samples,
            self.paths.reports / f"{metadata.session_id}.pdf",
            include_personal_data,
        )

    def list_sessions(self, participant_id: str | None = None) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in sorted(self.paths.sessions.glob("*/metadata.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                participant_id is None
                or record.get("participant", {}).get("participant_id") == participant_id
            ):
                record["_path"] = str(path)
                records.append(record)
        return records

    def load_stabilogram(self, record: dict[str, Any]) -> list[tuple[float, float]]:
        """Load finite processed COP points for a metadata record returned by ``list_sessions``."""
        metadata_path = Path(str(record.get("_path", "")))
        csv_path = metadata_path.parent / "samples.csv"
        points: list[tuple[float, float]] = []
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle, delimiter=";"):
                    x_text = row.get("filtered_cop_x") or row.get("cop_x")
                    y_text = row.get("filtered_cop_y") or row.get("cop_y")
                    if not x_text or not y_text:
                        continue
                    x, y = float(x_text), float(y_text)
                    if math.isfinite(x) and math.isfinite(y):
                        points.append((x, y))
        except (OSError, ValueError):
            return []
        return points

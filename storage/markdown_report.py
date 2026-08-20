"""Plain-text session report without clinical interpretation."""

from __future__ import annotations

from pathlib import Path

from app.constants import DISCLAIMER
from app.models import SessionMetadata


def build_markdown(metadata: SessionMetadata, include_personal_data: bool = False) -> str:
    participant = metadata.participant
    identity = participant.participant_id
    if include_personal_data and not participant.identifier_only:
        identity += f" — {participant.first_name} {participant.last_name}"
    metric_rows = "\n".join(
        f"| {key} | {value if value is not None else 'brak'} |"
        for key, value in metadata.metrics.items()
    )
    flags = (
        "\n".join(f"- {flag.value}" for flag in metadata.quality_flags)
        or "- Brak wykrytych ostrzeżeń"
    )
    return f"""# Raport sesji {metadata.session_id}

**{DISCLAIMER}**

- Uczestnik: {identity}
- Data rozpoczęcia: {metadata.started_at}
- Protokół: {metadata.config.protocol}
- Backend: {metadata.backend}
- Dane syntetyczne: {'tak' if metadata.synthetic_data else 'nie'}
- Kalibracja: {metadata.calibration.calibration_type}
- Filtr: {metadata.config.filter_settings.kind}
- Klasyfikacja jakości: {metadata.quality_rating.value}

## Wyniki

| Parametr | Wartość |
|---|---:|
{metric_rows}

## Kontrola jakości

{flags}

## Neutralne podsumowanie

Raport przedstawia parametry i wskaźniki tej sesji. Nie zawiera diagnozy ani zaleceń klinicznych.
"""


def export_markdown(
    metadata: SessionMetadata, path: Path, include_personal_data: bool = False
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown(metadata, include_personal_data), encoding="utf-8")
    return path

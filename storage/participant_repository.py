"""Local participant JSON records (no database in version 0.1)."""

from __future__ import annotations

import json
from pathlib import Path

from app.models import Participant
from storage.paths import DataPaths


class ParticipantRepository:
    def __init__(self, paths: DataPaths | None = None) -> None:
        self.paths = (paths or DataPaths()).ensure()

    def save(self, participant: Participant, include_personal_data: bool = True) -> Path:
        errors = participant.validate()
        if errors:
            raise ValueError(" ".join(errors))
        path = self.paths.participants / f"{participant.safe_id}.json"
        path.write_text(
            json.dumps(participant.to_dict(include_personal_data), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, participant_id: str) -> Participant:
        path = self.paths.participants / f"{participant_id}.json"
        return Participant(**json.loads(path.read_text(encoding="utf-8")))

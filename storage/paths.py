"""Managed data directory layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DataPaths:
    root: Path = Path("data")

    @property
    def participants(self) -> Path:
        return self.root / "participants"

    @property
    def sessions(self) -> Path:
        return self.root / "sessions"

    @property
    def exports(self) -> Path:
        return self.root / "exports"

    @property
    def reports(self) -> Path:
        return self.root / "reports"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    def ensure(self) -> DataPaths:
        for path in (self.participants, self.sessions, self.exports, self.reports, self.logs):
            path.mkdir(parents=True, exist_ok=True)
        return self

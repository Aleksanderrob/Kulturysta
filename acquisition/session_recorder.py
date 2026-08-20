"""In-memory recorder that finalizes a complete, quality-labelled session."""

from __future__ import annotations

from datetime import UTC, datetime

from acquisition.filters import apply_filter
from acquisition.quality import QualityAssessor
from analysis.metrics import calculate_metrics
from app.models import BoardSample, SessionMetadata


class SessionRecorder:
    def __init__(self, metadata: SessionMetadata, assessor: QualityAssessor | None = None) -> None:
        self.metadata = metadata
        self.samples: list[BoardSample] = []
        self.filtered_samples: list[BoardSample] = []
        self.assessor = assessor or QualityAssessor()
        self._finished = False

    def add_sample(self, sample: BoardSample) -> BoardSample:
        if self._finished:
            raise RuntimeError("Sesja została już zakończona.")
        assessed = self.assessor.assess_sample(sample, self.samples[-1] if self.samples else None)
        self.samples.append(assessed)
        return assessed

    def finalize(self, stopped_early: bool = False) -> dict[str, object]:
        self._finished = True
        settings = self.metadata.config.filter_settings
        self.filtered_samples = apply_filter(self.samples, settings)
        rating, flags = self.assessor.assess_session(
            self.samples, self.metadata.config.duration_s, stopped_early
        )
        self.metadata.finished_at = datetime.now(UTC).isoformat()
        self.metadata.quality_rating = rating
        self.metadata.quality_flags = flags
        self.metadata.metrics = calculate_metrics(
            self.filtered_samples,
            use_filtered=True,
            target=(
                self.metadata.config.target_x,
                self.metadata.config.target_y,
                self.metadata.config.target_radius,
            ),
        )
        return self.metadata.metrics

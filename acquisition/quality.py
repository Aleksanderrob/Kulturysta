"""Rule-based session quality assessment."""

from __future__ import annotations

import math

import numpy as np

from app.models import BoardSample, QualityFlag, QualityRating


class QualityAssessor:
    """Detect transparent, non-diagnostic data quality conditions."""

    def __init__(
        self,
        minimum_load_kg: float = 5.0,
        max_gap_s: float = 0.2,
        max_mass_jump_kg: float = 15.0,
        max_cop_jump: float = 0.6,
    ) -> None:
        self.minimum_load_kg = minimum_load_kg
        self.max_gap_s = max_gap_s
        self.max_mass_jump_kg = max_mass_jump_kg
        self.max_cop_jump = max_cop_jump

    def assess_sample(
        self, sample: BoardSample, previous: BoardSample | None = None
    ) -> BoardSample:
        flags = list(sample.quality_flags)
        values = [sample.total_weight_kg, sample.cop_x, sample.cop_y]
        if not sample.connection_ok:
            flags.append(QualityFlag.NO_CONNECTION)
        if any(v is not None and not math.isfinite(v) for v in values):
            flags.append(QualityFlag.INVALID_VALUE)
        if sample.total_weight_kg is None or sample.total_weight_kg < self.minimum_load_kg:
            flags.append(QualityFlag.LOW_LOAD)
        sensors = [sample.top_left, sample.top_right, sample.bottom_left, sample.bottom_right]
        if any(v is None for v in sensors):
            flags.append(QualityFlag.SENSOR_MISSING)
        if previous is not None:
            dt = sample.timestamp_monotonic - previous.timestamp_monotonic
            if dt > self.max_gap_s:
                flags.append(QualityFlag.DATA_GAP)
            if (
                sample.total_weight_kg is not None
                and previous.total_weight_kg is not None
                and abs(sample.total_weight_kg - previous.total_weight_kg) > self.max_mass_jump_kg
            ):
                flags.append(QualityFlag.MASS_JUMP)
            if (
                previous.total_weight_kg is not None
                and previous.total_weight_kg >= self.minimum_load_kg
                and (
                    sample.total_weight_kg is None or sample.total_weight_kg < self.minimum_load_kg
                )
            ):
                flags.append(QualityFlag.STEP_OFF)
            if None not in (sample.cop_x, sample.cop_y, previous.cop_x, previous.cop_y):
                jump = math.hypot(sample.cop_x - previous.cop_x, sample.cop_y - previous.cop_y)
                if jump > self.max_cop_jump:
                    flags.append(QualityFlag.COP_JUMP)
        return sample.with_flags(*flags)

    def assess_session(
        self, samples: list[BoardSample], expected_duration_s: float, stopped_early: bool = False
    ) -> tuple[QualityRating, list[QualityFlag]]:
        flags = {flag for sample in samples for flag in sample.quality_flags}
        duration = (
            samples[-1].timestamp_monotonic - samples[0].timestamp_monotonic
            if len(samples) > 1
            else 0.0
        )
        if duration < max(1.0, expected_duration_s * 0.8):
            flags.add(QualityFlag.TOO_SHORT)
        if stopped_early:
            flags.add(QualityFlag.STOPPED_EARLY)
        if len(samples) > 3:
            dt = np.diff([s.timestamp_monotonic for s in samples])
            dt = dt[np.isfinite(dt) & (dt > 0)]
            if len(dt) > 2 and np.mean(dt) > 0 and np.std(dt) / np.mean(dt) > 0.25:
                flags.add(QualityFlag.SAMPLE_RATE_VARIATION)
        invalid = {QualityFlag.NO_CONNECTION, QualityFlag.INVALID_VALUE, QualityFlag.TOO_SHORT}
        rating = (
            QualityRating.INVALID
            if flags & invalid
            else (QualityRating.WARNING if flags else QualityRating.VALID)
        )
        return rating, sorted(flags, key=lambda item: item.value)

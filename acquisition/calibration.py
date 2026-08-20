"""Non-destructive zero/reference calibration calculations."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from statistics import fmean

from app.models import BoardSample, CalibrationSettings


def calculate_calibration(
    samples: list[BoardSample], reference_mass_kg: float | None = None
) -> CalibrationSettings:
    valid_mass = [
        s.total_weight_kg
        for s in samples
        if s.total_weight_kg is not None and math.isfinite(s.total_weight_kg)
    ]
    valid_x = [s.cop_x for s in samples if s.cop_x is not None and math.isfinite(s.cop_x)]
    valid_y = [s.cop_y for s in samples if s.cop_y is not None and math.isfinite(s.cop_y)]
    if not valid_mass:
        raise ValueError("Brak poprawnych próbek do kalibracji.")
    mean_mass = fmean(valid_mass)
    scale = 1.0
    calibration_type = "zero"
    if reference_mass_kg is not None:
        if reference_mass_kg <= 0 or mean_mass <= 0:
            raise ValueError("Masa referencyjna i odczyt muszą być dodatnie.")
        scale = reference_mass_kg / mean_mass
        calibration_type = "reference_load"
    return CalibrationSettings(
        applied=True,
        calibration_type=calibration_type,
        mass_offset_kg=mean_mass if reference_mass_kg is None else 0.0,
        cop_x_offset=fmean(valid_x) if valid_x else 0.0,
        cop_y_offset=fmean(valid_y) if valid_y else 0.0,
        reference_mass_kg=reference_mass_kg,
        scale_factor=scale,
        performed_at=datetime.now(UTC).isoformat(),
    )


def apply_calibration(sample: BoardSample, settings: CalibrationSettings) -> BoardSample:
    if not settings.applied:
        return sample
    from dataclasses import replace

    mass = sample.total_weight_kg
    return replace(
        sample,
        raw_total_weight_kg=(
            sample.raw_total_weight_kg
            if sample.raw_total_weight_kg is not None
            else sample.total_weight_kg
        ),
        raw_cop_x=sample.raw_cop_x if sample.raw_cop_x is not None else sample.cop_x,
        raw_cop_y=sample.raw_cop_y if sample.raw_cop_y is not None else sample.cop_y,
        total_weight_kg=(
            None
            if mass is None
            else max(0.0, (mass - settings.mass_offset_kg) * settings.scale_factor)
        ),
        cop_x=None if sample.cop_x is None else sample.cop_x - settings.cop_x_offset,
        cop_y=None if sample.cop_y is None else sample.cop_y - settings.cop_y_offset,
    )


def add_reference_scale(
    samples: list[BoardSample],
    zero_settings: CalibrationSettings,
    reference_mass_kg: float,
) -> CalibrationSettings:
    """Extend a zero calibration using a known load, without claiming accuracy improvement."""
    valid_mass = [
        sample.total_weight_kg
        for sample in samples
        if sample.total_weight_kg is not None and math.isfinite(sample.total_weight_kg)
    ]
    if not valid_mass or reference_mass_kg <= 0:
        raise ValueError("Brak poprawnych próbek lub dodatniej masy referencyjnej.")
    corrected_mean = fmean(valid_mass) - zero_settings.mass_offset_kg
    if corrected_mean <= 0:
        raise ValueError("Odczyt po odjęciu zera musi być dodatni.")
    return CalibrationSettings(
        applied=True,
        calibration_type="zero_and_reference_load",
        mass_offset_kg=zero_settings.mass_offset_kg,
        cop_x_offset=zero_settings.cop_x_offset,
        cop_y_offset=zero_settings.cop_y_offset,
        reference_mass_kg=reference_mass_kg,
        scale_factor=reference_mass_kg / corrected_mean,
        performed_at=datetime.now(UTC).isoformat(),
    )

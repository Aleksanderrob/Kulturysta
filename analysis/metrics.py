"""Robust session metrics using real timestamps."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from app.models import BoardSample


def _series(samples: list[BoardSample], name: str) -> np.ndarray:
    return np.asarray(
        [np.nan if getattr(s, name) is None else getattr(s, name) for s in samples], dtype=float
    )


def _safe(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None


def _stats(values: np.ndarray) -> tuple[float | None, float | None, float | None]:
    values = values[np.isfinite(values)]
    if not len(values):
        return None, None, None
    return _safe(np.mean(values)), _safe(np.std(values)), _safe(np.ptp(values))


def calculate_metrics(
    samples: list[BoardSample],
    use_filtered: bool = False,
    target: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    """Calculate neutral numerical indicators; no clinical interpretation is produced."""
    result: dict[str, Any] = {"sample_count": len(samples)}
    if not samples:
        return {**result, "duration_s": 0.0, "sample_rate_hz": None, "cop_unit": "unknown"}
    t = _series(samples, "timestamp_monotonic")
    x_name = "filtered_cop_x" if use_filtered else "cop_x"
    y_name = "filtered_cop_y" if use_filtered else "cop_y"
    x, y, mass = (
        _series(samples, x_name),
        _series(samples, y_name),
        _series(samples, "total_weight_kg"),
    )
    finite_xy = np.isfinite(t) & np.isfinite(x) & np.isfinite(y)
    t, x, y = t[finite_xy], x[finite_xy], y[finite_xy]
    duration = float(max(0.0, t[-1] - t[0])) if len(t) > 1 else 0.0
    dt_all = np.diff(t)
    valid_dt = dt_all[np.isfinite(dt_all) & (dt_all > 0)]
    sample_rate = _safe(1.0 / np.mean(valid_dt)) if len(valid_dt) else None
    mass_mean, mass_std, _ = _stats(mass)
    x_mean, x_std, x_range = _stats(x)
    y_mean, y_std, y_range = _stats(y)
    distance = np.hypot(np.diff(x), np.diff(y)) if len(x) > 1 else np.array([], dtype=float)
    valid_motion = np.isfinite(dt_all) & (dt_all > 0) if len(dt_all) else np.array([], dtype=bool)
    path_length = float(np.sum(distance[valid_motion])) if len(distance) else 0.0
    speed = (
        distance[valid_motion] / dt_all[valid_motion]
        if len(distance)
        else np.array([], dtype=float)
    )
    speed_t = t[1:][valid_motion] if len(t) > 1 else np.array([], dtype=float)
    speed_dt = np.diff(speed_t)
    acceleration = (
        np.abs(np.diff(speed) / speed_dt) if len(speed) > 1 else np.array([], dtype=float)
    )
    acceleration = acceleration[np.isfinite(acceleration)]
    rms = _safe(np.sqrt(np.mean((x - np.mean(x)) ** 2 + (y - np.mean(y)) ** 2))) if len(x) else None
    ellipse_area = None
    if len(x) >= 3:
        covariance = np.cov(np.vstack((x, y)), ddof=1)
        determinant = float(np.linalg.det(covariance))
        if determinant >= 0 and math.isfinite(determinant):
            ellipse_area = math.pi * 5.991 * math.sqrt(determinant)
    left = _series(samples, "top_left") + _series(samples, "bottom_left")
    right = _series(samples, "top_right") + _series(samples, "bottom_right")
    front = _series(samples, "top_left") + _series(samples, "top_right")
    back = _series(samples, "bottom_left") + _series(samples, "bottom_right")
    total_lr = left + right
    lr_mask = np.isfinite(left) & np.isfinite(right) & (total_lr > 0)
    total_fb = front + back
    fb_mask = np.isfinite(front) & np.isfinite(back) & (total_fb > 0)
    lr_asym = (
        _safe(np.mean((right[lr_mask] - left[lr_mask]) / total_lr[lr_mask]) * 100)
        if lr_mask.any()
        else None
    )
    fb_asym = (
        _safe(np.mean((front[fb_mask] - back[fb_mask]) / total_fb[fb_mask]) * 100)
        if fb_mask.any()
        else None
    )
    result.update(
        duration_s=duration,
        sample_rate_hz=sample_rate,
        sample_interval_std_s=_safe(np.std(valid_dt)) if len(valid_dt) else None,
        mean_mass_kg=mass_mean,
        std_mass_kg=mass_std,
        mean_cop_x=x_mean,
        mean_cop_y=y_mean,
        std_cop_x=x_std,
        std_cop_y=y_std,
        range_cop_ml=x_range,
        range_cop_ap=y_range,
        path_length=path_length,
        mean_speed=_safe(np.mean(speed)) if len(speed) else 0.0,
        max_speed=_safe(np.max(speed)) if len(speed) else 0.0,
        mean_acceleration=_safe(np.mean(acceleration)) if len(acceleration) else 0.0,
        max_acceleration=_safe(np.max(acceleration)) if len(acceleration) else 0.0,
        rms_cop=rms,
        left_right_asymmetry_percent=lr_asym,
        front_back_asymmetry_percent=fb_asym,
        confidence_ellipse_95_area=ellipse_area,
        cop_unit=next((s.cop_unit for s in samples if s.cop_unit), "unknown"),
        path_unit=next((s.cop_unit for s in samples if s.cop_unit), "unknown"),
        speed_unit=f"{next((s.cop_unit for s in samples if s.cop_unit), 'unknown')}/s",
        acceleration_unit=f"{next((s.cop_unit for s in samples if s.cop_unit), 'unknown')}/s²",
    )
    if target is not None and len(t):
        tx, ty, radius = target
        inside = np.hypot(x - tx, y - ty) <= radius
        dwell = float(np.sum(np.diff(t) * inside[:-1])) if len(t) > 1 else 0.0
        entries = int(np.sum((~inside[:-1]) & inside[1:])) if len(inside) > 1 else int(inside[0])
        exits = int(np.sum(inside[:-1] & (~inside[1:]))) if len(inside) > 1 else 0
        result.update(
            time_in_target_s=dwell,
            percent_time_in_target=(100.0 * dwell / duration if duration > 0 else 0.0),
            targets_reached=entries,
            exits_from_target=exits,
        )
    return result

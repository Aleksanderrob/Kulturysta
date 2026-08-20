"""Timestamp-aware COP filters preserving raw values."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from app.models import BoardSample, FilterSettings


def estimate_sample_rate(samples: list[BoardSample]) -> float | None:
    times = np.asarray([s.timestamp_monotonic for s in samples], dtype=float)
    if len(times) < 2:
        return None
    dt = np.diff(times)
    dt = dt[np.isfinite(dt) & (dt > 0)]
    return float(1.0 / np.mean(dt)) if len(dt) else None


def _fill_finite(values: np.ndarray) -> np.ndarray:
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros_like(values)
    indices = np.arange(len(values))
    return np.interp(indices, indices[finite], values[finite])


def apply_filter(samples: list[BoardSample], settings: FilterSettings) -> list[BoardSample]:
    """Return samples with filtered COP columns while retaining raw COP."""
    if not samples:
        return []
    x = _fill_finite(
        np.asarray([np.nan if s.cop_x is None else s.cop_x for s in samples], dtype=float)
    )
    y = _fill_finite(
        np.asarray([np.nan if s.cop_y is None else s.cop_y for s in samples], dtype=float)
    )
    kind = settings.kind.lower()
    if kind == "none":
        fx, fy = x, y
    elif kind == "moving_average":
        window = max(1, min(int(settings.moving_average_window), len(samples)))
        kernel = np.ones(window) / window
        fx = np.convolve(x, kernel, mode="same")
        fy = np.convolve(y, kernel, mode="same")
        edge = window // 2
        if edge:
            fx[:edge], fx[-edge:] = x[:edge], x[-edge:]
            fy[:edge], fy[-edge:] = y[:edge], y[-edge:]
    elif kind == "butterworth":
        from scipy.signal import butter, sosfiltfilt

        rate = settings.sample_rate_hz or estimate_sample_rate(samples)
        if rate is None or not (0 < settings.cutoff_hz < rate / 2):
            raise ValueError(
                "Filtr Butterwortha wymaga poprawnej częstotliwości i odcięcia poniżej Nyquista."
            )
        sos = butter(settings.order, settings.cutoff_hz, fs=rate, output="sos")
        try:
            fx, fy = sosfiltfilt(sos, x), sosfiltfilt(sos, y)
        except ValueError as exc:
            raise ValueError("Sesja jest zbyt krótka dla wybranego filtra Butterwortha.") from exc
    else:
        raise ValueError(f"Nieznany filtr: {settings.kind}")
    return [
        replace(s, filtered_cop_x=float(fx[i]), filtered_cop_y=float(fy[i]))
        for i, s in enumerate(samples)
    ]

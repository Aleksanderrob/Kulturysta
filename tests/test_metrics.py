import math

import pytest

from analysis.metrics import calculate_metrics


def test_empty_session():
    metrics = calculate_metrics([])
    assert metrics["sample_count"] == 0
    assert metrics["duration_s"] == 0


def test_one_sample(sample_factory):
    metrics = calculate_metrics([sample_factory(1.0)])
    assert metrics["path_length"] == 0
    assert metrics["sample_rate_hz"] is None


def test_known_path_and_irregular_speed(sample_factory):
    samples = [
        sample_factory(0, 0, 0, sequence=0),
        sample_factory(1, 3, 0, sequence=1),
        sample_factory(3, 3, 4, sequence=2),
    ]
    metrics = calculate_metrics(samples)
    assert metrics["path_length"] == pytest.approx(7.0)
    assert metrics["mean_speed"] == pytest.approx(2.5)
    assert metrics["max_speed"] == pytest.approx(3.0)
    assert metrics["mean_acceleration"] == pytest.approx(0.5)


def test_confidence_ellipse_and_rms(sample_factory):
    samples = [
        sample_factory(i, x, y, sequence=i)
        for i, (x, y) in enumerate([(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)])
    ]
    metrics = calculate_metrics(samples)
    assert metrics["confidence_ellipse_95_area"] > 0
    assert metrics["rms_cop"] > 0


def test_asymmetry_from_sensor_loads(sample_factory):
    metrics = calculate_metrics([sample_factory(0, 0.5, -0.25)])
    assert metrics["left_right_asymmetry_percent"] == pytest.approx(50.0)
    assert metrics["front_back_asymmetry_percent"] == pytest.approx(-25.0)


def test_nan_and_duplicate_timestamps_are_safe(sample_factory):
    samples = [sample_factory(0, 0, 0), sample_factory(0, float("nan"), 1), sample_factory(1, 1, 1)]
    metrics = calculate_metrics(samples)
    assert metrics["sample_count"] == 3
    assert math.isfinite(metrics["path_length"])


def test_target_metrics(sample_factory):
    samples = [sample_factory(0, 0, 0), sample_factory(1, 0.05, 0), sample_factory(2, 0.5, 0)]
    metrics = calculate_metrics(samples, target=(0, 0, 0.1))
    assert metrics["time_in_target_s"] == pytest.approx(2.0)
    assert metrics["exits_from_target"] == 1

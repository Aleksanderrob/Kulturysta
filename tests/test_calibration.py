import pytest

from acquisition.calibration import add_reference_scale, apply_calibration, calculate_calibration


def test_zero_calibration(sample_factory):
    samples = [sample_factory(i, 0.1, -0.1, 2.0, i) for i in range(5)]
    settings = calculate_calibration(samples)
    calibrated = apply_calibration(samples[0], settings)
    assert calibrated.total_weight_kg == pytest.approx(0.0)
    assert calibrated.cop_x == pytest.approx(0.0)
    assert settings.calibration_type == "zero"


def test_reference_load_scale(sample_factory):
    settings = calculate_calibration([sample_factory(0, weight=50)], reference_mass_kg=60)
    assert settings.scale_factor == pytest.approx(1.2)


def test_zero_then_reference_load_keeps_offset(sample_factory):
    zero = calculate_calibration([sample_factory(index, weight=2) for index in range(4)])
    settings = add_reference_scale(
        [sample_factory(index, weight=52) for index in range(4)], zero, 50
    )
    assert settings.calibration_type == "zero_and_reference_load"
    assert settings.mass_offset_kg == pytest.approx(2)
    assert settings.scale_factor == pytest.approx(1)


def test_calibration_preserves_raw_values(sample_factory):
    sample = sample_factory(0, x=0.2, y=-0.3, weight=12)
    settings = calculate_calibration([sample_factory(0, x=0.1, y=-0.1, weight=2)])
    calibrated = apply_calibration(sample, settings)
    assert calibrated.raw_total_weight_kg == pytest.approx(12)
    assert calibrated.raw_cop_x == pytest.approx(0.2)
    assert calibrated.raw_cop_y == pytest.approx(-0.3)
    assert calibrated.total_weight_kg == pytest.approx(10)
    assert calibrated.cop_x == pytest.approx(0.1)
    assert calibrated.cop_y == pytest.approx(-0.2)

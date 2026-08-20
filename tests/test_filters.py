import pytest

from acquisition.filters import apply_filter, estimate_sample_rate
from app.models import FilterSettings


def test_estimate_sample_rate(sample_factory):
    samples = [sample_factory(i * 0.02, sequence=i) for i in range(10)]
    assert estimate_sample_rate(samples) == pytest.approx(50.0)


def test_none_filter_preserves_values(sample_factory):
    samples = [sample_factory(i, i / 10, -i / 10, sequence=i) for i in range(5)]
    result = apply_filter(samples, FilterSettings(kind="none"))
    assert [s.filtered_cop_x for s in result] == pytest.approx([s.cop_x for s in samples])


def test_moving_average_reduces_center_spike(sample_factory):
    values = [0, 0, 1, 0, 0]
    samples = [sample_factory(i, value, value, sequence=i) for i, value in enumerate(values)]
    result = apply_filter(samples, FilterSettings(kind="moving_average", moving_average_window=3))
    assert result[2].filtered_cop_x == pytest.approx(1 / 3)


def test_butterworth_rejects_invalid_cutoff(sample_factory):
    samples = [sample_factory(i * 0.1, sequence=i) for i in range(30)]
    with pytest.raises(ValueError):
        apply_filter(samples, FilterSettings(kind="butterworth", cutoff_hz=6, sample_rate_hz=10))

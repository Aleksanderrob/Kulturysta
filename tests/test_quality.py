from dataclasses import replace

from acquisition.quality import QualityAssessor
from app.models import QualityFlag, QualityRating


def test_low_load_and_missing_sensor(sample_factory):
    assessor = QualityAssessor()
    sample = replace(sample_factory(0, weight=0), top_left=None)
    assessed = assessor.assess_sample(sample)
    assert QualityFlag.LOW_LOAD in assessed.quality_flags
    assert QualityFlag.SENSOR_MISSING in assessed.quality_flags


def test_gap_and_jumps(sample_factory):
    assessor = QualityAssessor(max_gap_s=0.2, max_cop_jump=0.5, max_mass_jump_kg=10)
    previous = sample_factory(0, 0, 0, 70)
    current = sample_factory(1, 1, 1, 90)
    flags = assessor.assess_sample(current, previous).quality_flags
    assert {QualityFlag.DATA_GAP, QualityFlag.COP_JUMP, QualityFlag.MASS_JUMP}.issubset(flags)


def test_session_rating_and_early_stop(sample_factory):
    assessor = QualityAssessor()
    samples = [sample_factory(i, sequence=i) for i in range(5)]
    rating, flags = assessor.assess_session(samples, expected_duration_s=10, stopped_early=True)
    assert rating == QualityRating.INVALID
    assert QualityFlag.TOO_SHORT in flags
    assert QualityFlag.STOPPED_EARLY in flags


def test_valid_session(sample_factory):
    samples = [sample_factory(i, sequence=i) for i in range(11)]
    rating, flags = QualityAssessor().assess_session(samples, 10)
    assert rating == QualityRating.VALID
    assert not flags


def test_step_off_is_distinguished_from_initial_low_load(sample_factory):
    assessor = QualityAssessor(minimum_load_kg=5)
    loaded = sample_factory(0, weight=70)
    stepped_off = assessor.assess_sample(sample_factory(0.1, weight=0), loaded)
    assert QualityFlag.STEP_OFF in stepped_off.quality_flags
    assert QualityFlag.LOW_LOAD in stepped_off.quality_flags

    initial = assessor.assess_sample(sample_factory(0, weight=0))
    assert QualityFlag.STEP_OFF not in initial.quality_flags

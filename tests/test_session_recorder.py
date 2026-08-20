from acquisition.session_recorder import SessionRecorder
from app.models import Participant, SessionConfig, SessionMetadata


def test_recorder_finalizes_metrics(sample_factory):
    metadata = SessionMetadata(
        Participant(participant_id="TEST", identifier_only=True),
        SessionConfig(
            duration_s=1,
            filter_settings=__import__("app.models", fromlist=["FilterSettings"]).FilterSettings(
                kind="none"
            ),
        ),
        "simulator",
        synthetic_data=True,
    )
    recorder = SessionRecorder(metadata)
    for index in range(11):
        recorder.add_sample(sample_factory(index / 10, 0.1 * index / 10, sequence=index))
    metrics = recorder.finalize()
    assert metrics["sample_count"] == 11
    assert metadata.finished_at is not None
    assert len(recorder.filtered_samples) == 11


def test_recorder_cannot_accept_after_finalize(sample_factory):
    import pytest

    metadata = SessionMetadata(
        Participant(participant_id="TEST", identifier_only=True),
        SessionConfig(duration_s=1),
        "simulator",
    )
    recorder = SessionRecorder(metadata)
    recorder.add_sample(sample_factory(0))
    recorder.finalize(True)
    with pytest.raises(RuntimeError):
        recorder.add_sample(sample_factory(1))

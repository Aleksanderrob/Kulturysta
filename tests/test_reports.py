from acquisition.session_recorder import SessionRecorder
from app.models import FilterSettings, Participant, SessionConfig, SessionMetadata
from storage.pdf_report import export_pdf


def test_pdf_report_is_created(tmp_path, sample_factory):
    metadata = SessionMetadata(
        Participant(participant_id="PDF", identifier_only=True),
        SessionConfig(duration_s=1, filter_settings=FilterSettings(kind="none")),
        "simulator",
        synthetic_data=True,
    )
    recorder = SessionRecorder(metadata)
    for index in range(11):
        recorder.add_sample(
            sample_factory(index / 10, x=index / 100, y=-index / 200, sequence=index)
        )
    recorder.finalize()
    path = export_pdf(metadata, recorder.filtered_samples, tmp_path / "report.pdf")
    assert path.read_bytes().startswith(b"%PDF")
    assert path.stat().st_size > 2000

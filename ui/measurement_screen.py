"""Measurement workflow and live recording screen."""

from __future__ import annotations

import logging
import time
from dataclasses import replace

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from acquisition.session_recorder import SessionRecorder
from app.models import (
    BoardSample,
    CalibrationSettings,
    Participant,
    SessionConfig,
    SessionMetadata,
)
from storage.session_repository import SessionRepository
from ui.cop_widget import CopWidget
from ui.widgets import MetricCard


class MeasurementScreen(QWidget):
    result_ready = Signal(object, object, object)

    def __init__(
        self,
        repository: SessionRepository,
        minimum_load_kg: float = 5.0,
        visualization: dict[str, object] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.repository = repository
        self.participant = Participant(participant_id="DEMO", identifier_only=True)
        self.config = SessionConfig()
        self.calibration = CalibrationSettings()
        self.minimum_load_kg = float(minimum_load_kg)
        self.connected = False
        self.latest_sample: BoardSample | None = None
        self.recorder: SessionRecorder | None = None
        self._active = False
        self._sequence_running = False
        self._current_repetition = 1
        self._started = 0.0
        self._break_started = 0.0
        self._countdown = 0
        self._last_result: tuple[object, object, object] | None = None
        root = QVBoxLayout(self)
        self.banner = QLabel("TRYB POMIAROWY — dane lokalne, zastosowanie niediagnostyczne")
        self.banner.setObjectName("screenBanner")
        root.addWidget(self.banner)
        body = QHBoxLayout()
        root.addLayout(body, 1)
        self.cop_widget = CopWidget()
        visualization = visualization or {}
        self.cop_widget.set_scale(
            str(visualization.get("scale_mode", "fixed")),
            float(visualization.get("fixed_range", 1.0)),
        )
        body.addWidget(self.cop_widget, 1)
        metrics = QGridLayout()
        body.addLayout(metrics)
        self.mass_card = MetricCard("Masa", "— kg")
        self.x_card = MetricCard("COP X", "—")
        self.y_card = MetricCard("COP Y", "—")
        self.rate_card = MetricCard("Próbkowanie", "— Hz")
        self.timer_card = MetricCard("Pozostało", "30.0 s")
        self.quality_card = MetricCard("Jakość", "oczekiwanie")
        for index, card in enumerate(
            (
                self.mass_card,
                self.x_card,
                self.y_card,
                self.rate_card,
                self.timer_card,
                self.quality_card,
            )
        ):
            metrics.addWidget(card, index, 0)
        controls = QHBoxLayout()
        root.addLayout(controls)
        self.start_button = QPushButton("Start")
        self.start_button.setEnabled(False)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.abort_button = QPushButton("PRZERWIJ")
        self.abort_button.setObjectName("stopButton")
        self.abort_button.setEnabled(False)
        self.clear_button = QPushButton("Wyczyść ścieżkę")
        for widget in (self.start_button, self.stop_button, self.abort_button, self.clear_button):
            controls.addWidget(widget)
        controls.addStretch()
        self.start_button.clicked.connect(self.start_measurement)
        self.stop_button.clicked.connect(lambda: self.finish_measurement(True))
        self.abort_button.clicked.connect(self.abort_sequence)
        self.clear_button.clicked.connect(self.cop_widget.clear_path)
        self._display_timer = QTimer(self)
        self._display_timer.setInterval(100)
        self._display_timer.timeout.connect(self._update_timer)
        self._break_timer = QTimer(self)
        self._break_timer.setInterval(100)
        self._break_timer.timeout.connect(self._update_break)

    def set_connected(self, connected: bool) -> None:
        self.connected = connected
        self._refresh_start_state()
        if not connected and self._sequence_running:
            self.abort_sequence()

    def on_stream_error(self, message: str) -> None:
        logging.getLogger(__name__).error("Zatrzymanie strumienia podczas sesji: %s", message)
        if self._active and self.latest_sample is not None and self.recorder is not None:
            from app.models import QualityFlag

            self.recorder.add_sample(
                self.latest_sample.with_flags(QualityFlag.STREAM_STOPPED, QualityFlag.NO_CONNECTION)
            )
            self.finish_measurement(True)

    def set_participant(self, participant: Participant) -> None:
        self.participant = participant

    def set_config(self, config: SessionConfig) -> None:
        self.config = config
        self.timer_card.set_value(f"{config.duration_s:.1f} s")

    def set_calibration(self, calibration: CalibrationSettings) -> None:
        self.calibration = calibration
        self.banner.setText(
            "TRYB POMIAROWY — kalibracja: "
            f"{calibration.calibration_type}; dane lokalne, zastosowanie niediagnostyczne"
        )

    def on_sample(self, sample: BoardSample) -> None:
        self.latest_sample = sample
        loaded = bool(
            sample.total_weight_kg is not None and sample.total_weight_kg >= self.minimum_load_kg
        )
        self.cop_widget.set_sample(sample.cop_x, sample.cop_y, sample.cop_unit, loaded)
        self.mass_card.set_value(
            "— kg" if sample.total_weight_kg is None else f"{sample.total_weight_kg:.2f} kg"
        )
        self.x_card.set_value(
            "—" if sample.cop_x is None else f"{sample.cop_x:.3f} {sample.cop_unit}"
        )
        self.y_card.set_value(
            "—" if sample.cop_y is None else f"{sample.cop_y:.3f} {sample.cop_unit}"
        )
        self.quality_card.set_value("ostrzeżenie" if sample.quality_flags else "bieżąca poprawna")
        if self._active and self.recorder is not None:
            self.recorder.add_sample(sample)
            if len(self.recorder.samples) > 1:
                elapsed = (
                    self.recorder.samples[-1].timestamp_monotonic
                    - self.recorder.samples[0].timestamp_monotonic
                )
                self.rate_card.set_value(
                    f"{(len(self.recorder.samples) - 1) / elapsed:.1f} Hz"
                    if elapsed > 0
                    else "— Hz"
                )
        self._refresh_start_state()

    def _refresh_start_state(self) -> None:
        loaded = (
            self.latest_sample is not None
            and self.latest_sample.connection_ok
            and self.latest_sample.total_weight_kg is not None
            and self.latest_sample.total_weight_kg >= self.minimum_load_kg
        )
        self.start_button.setEnabled(
            self.connected and loaded and not self._active and not self._sequence_running
        )

    def start_measurement(self, skip_countdown: bool = False) -> None:
        if not self.connected or self.latest_sample is None:
            return
        if not self._sequence_running:
            self._sequence_running = True
            self._current_repetition = 1
            self._last_result = None
            self.abort_button.setEnabled(True)
        if skip_countdown:
            self._begin_recording()
            return
        self._countdown = 3
        self.timer_card.set_value("3")
        self.start_button.setEnabled(False)
        QTimer.singleShot(1000, self._countdown_tick)

    def _countdown_tick(self) -> None:
        if not self._sequence_running:
            return
        self._countdown -= 1
        if self._countdown <= 0:
            self._begin_recording()
        else:
            self.timer_card.set_value(
                f"{self._countdown} — próba {self._current_repetition}/{self.config.repetitions}"
            )
            QTimer.singleShot(1000, self._countdown_tick)

    def _begin_recording(self) -> None:
        repetition_config = replace(
            self.config,
            note=(
                f"{self.config.note} | powtórzenie "
                f"{self._current_repetition}/{self.config.repetitions}"
            ).strip(" |"),
        )
        metadata = SessionMetadata(
            self.participant,
            repetition_config,
            backend=(
                "simulator"
                if self.latest_sample and self.latest_sample.synthetic_data
                else "wbb-module"
            ),
            synthetic_data=bool(self.latest_sample and self.latest_sample.synthetic_data),
            calibration=self.calibration,
        )
        self.recorder = SessionRecorder(metadata)
        logging.getLogger(__name__).info(
            "Rozpoczęcie sesji %s | backend=%s | protokół=%s",
            metadata.session_id,
            metadata.backend,
            metadata.config.protocol,
        )
        self._active = True
        self._started = time.monotonic()
        self.stop_button.setEnabled(True)
        self.abort_button.setEnabled(True)
        self.banner.setText(
            f"TRYB POMIAROWY — próba {self._current_repetition}/{self.config.repetitions}; "
            f"kalibracja: {self.calibration.calibration_type}"
        )
        self._display_timer.start()

    def _update_timer(self) -> None:
        remaining = self.config.duration_s - (time.monotonic() - self._started)
        self.timer_card.set_value(f"{max(0.0, remaining):.1f} s")
        if remaining <= 0:
            self.finish_measurement(False)

    def finish_measurement(self, stopped_early: bool = False) -> None:
        if not self._active or self.recorder is None:
            return
        self._active = False
        self._display_timer.stop()
        self.stop_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        try:
            self.recorder.finalize(stopped_early)
            artifacts = self.repository.save(
                self.recorder.metadata, self.recorder.samples, self.recorder.filtered_samples
            )
            self._last_result = (
                self.recorder.metadata,
                self.recorder.filtered_samples,
                artifacts,
            )
            logging.getLogger(__name__).info(
                "Zakończenie sesji %s | jakość=%s | próbki=%d",
                self.recorder.metadata.session_id,
                self.recorder.metadata.quality_rating.value,
                len(self.recorder.samples),
            )
            self.quality_card.set_value(self.recorder.metadata.quality_rating.value)
        except Exception as exc:
            logging.getLogger(__name__).exception("Nie udało się zakończyć sesji")
            QMessageBox.critical(
                self,
                "Błąd zapisu",
                f"Nie udało się zapisać sesji: {exc}\nSzczegóły zapisano w data/logs/app.log.",
            )
            self._complete_sequence(emit_result=False)
            return
        if not stopped_early and self._current_repetition < self.config.repetitions:
            self._begin_break()
        else:
            self._complete_sequence()

    def _begin_break(self) -> None:
        self._break_started = time.monotonic()
        self.stop_button.setEnabled(False)
        self.abort_button.setEnabled(True)
        self._break_timer.start()
        self._update_break()

    def _update_break(self) -> None:
        remaining = self.config.break_s - (time.monotonic() - self._break_started)
        self.timer_card.set_value(
            f"Przerwa {max(0.0, remaining):.1f} s — następna próba "
            f"{self._current_repetition + 1}/{self.config.repetitions}"
        )
        if remaining > 0:
            return
        self._break_timer.stop()
        self._current_repetition += 1
        self._countdown = 3
        self.timer_card.set_value(f"3 — próba {self._current_repetition}/{self.config.repetitions}")
        QTimer.singleShot(1000, self._countdown_tick)

    def abort_sequence(self) -> None:
        if self._active:
            self.finish_measurement(True)
            return
        self._complete_sequence()

    def _complete_sequence(self, emit_result: bool = True) -> None:
        self._display_timer.stop()
        self._break_timer.stop()
        self._active = False
        self._sequence_running = False
        self.stop_button.setEnabled(False)
        self.abort_button.setEnabled(False)
        self.banner.setText("TRYB POMIAROWY — dane lokalne, zastosowanie niediagnostyczne")
        if emit_result and self._last_result is not None:
            self.result_ready.emit(*self._last_result)
        self._refresh_start_state()

    def stop_safely(self) -> None:
        if self._sequence_running:
            self.abort_sequence()

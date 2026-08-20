"""COP target training with adaptive, transparent scoring."""

from __future__ import annotations

import math
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import SAFETY_NOTICE
from app.models import BoardSample
from biofeedback.adaptation import AdaptiveDifficulty
from biofeedback.audio_feedback import play_target_cue
from biofeedback.exercises import EXERCISES
from biofeedback.feedback_engine import FeedbackEngine
from games.weight_shift import TARGET_SEQUENCE
from ui.cop_widget import CopWidget


class TrainingScreen(QWidget):
    def __init__(self, duration_s: float = 60.0, sound_enabled: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.duration_s = duration_s
        self.sound_enabled = sound_enabled
        self.active = False
        self.connected = False
        self._started = 0.0
        self._last_timestamp: float | None = None
        self.time_inside = 0.0
        self.targets_reached = 0
        self.adaptation = AdaptiveDifficulty()
        self.engine = FeedbackEngine(radius=self.adaptation.target_radius)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("TRYB TRENINGOWY — ćwicz wyłącznie z nadzorem i asekuracją"))
        self.exercise_combo = QComboBox()
        for exercise in EXERCISES:
            self.exercise_combo.addItem(exercise.label, exercise.key)
        self.cop_widget = CopWidget()
        self.cop_widget.set_target(0, 0, self.engine.radius)
        layout.addWidget(self.exercise_combo)
        layout.addWidget(self.cop_widget, 1)
        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.status = QLabel("Gotowy")
        self.start_button = QPushButton("Rozpocznij trening")
        self.stop_button = QPushButton("PRZERWIJ")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        self.sound_button = QPushButton(
            "Dźwięk: włączony" if sound_enabled else "Dźwięk: wyciszony"
        )
        self.sound_button.setCheckable(True)
        self.sound_button.setChecked(sound_enabled)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.sound_button)
        controls.addWidget(self.status)
        controls.addStretch()
        self.start_button.clicked.connect(self.start_training)
        self.stop_button.clicked.connect(self.stop_training)
        self.sound_button.toggled.connect(self._set_sound)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._tick)

    def set_connected(self, connected: bool) -> None:
        self.connected = connected
        self.start_button.setEnabled(connected and not self.active)
        if not connected:
            self.stop_training()

    def start_training(self, show_confirmation: bool = True) -> None:
        if not self.connected:
            return
        if (
            show_confirmation
            and QMessageBox.information(
                self,
                "Zasady bezpieczeństwa",
                SAFETY_NOTICE,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            != QMessageBox.StandardButton.Ok
        ):
            return
        self.active = True
        self._started = time.monotonic()
        self._last_timestamp = None
        self.time_inside = 0.0
        self.targets_reached = 0
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.timer.start()

    def on_sample(self, sample: BoardSample) -> None:
        if sample.cop_x is None or sample.cop_y is None:
            return
        self.cop_widget.set_sample(
            sample.cop_x, sample.cop_y, sample.cop_unit, (sample.total_weight_kg or 0) >= 5
        )
        if not self.active:
            return
        elapsed = time.monotonic() - self._started
        key = self.exercise_combo.currentData()
        tx, ty = self._target_for_exercise(str(key), elapsed)
        self.engine.target_x, self.engine.target_y = tx, ty
        self.cop_widget.set_target(tx, ty, self.engine.radius)
        state = self.engine.update(sample.cop_x, sample.cop_y)
        if state.entered:
            self.targets_reached += 1
            play_target_cue(self.sound_enabled)
        if self._last_timestamp is not None and state.inside:
            self.time_inside += max(0.0, sample.timestamp_monotonic - self._last_timestamp)
        self._last_timestamp = sample.timestamp_monotonic

    def _tick(self) -> None:
        elapsed = time.monotonic() - self._started
        remaining = max(0.0, self.duration_s - elapsed)
        score = 100 * self.time_inside / elapsed if elapsed > 0 else 0
        self.status.setText(
            f"Pozostało {remaining:.1f} s | w celu {score:.0f}% | cele {self.targets_reached}"
        )
        if remaining <= 0:
            self.stop_training()

    def stop_training(self) -> None:
        if not self.active:
            return
        self.active = False
        self.timer.stop()
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(self.connected)
        score = 100 * self.time_inside / max(0.001, time.monotonic() - self._started)
        self.engine.radius = self.adaptation.update(score)
        self.status.setText(
            f"Wynik rundy: {score:.0f}% | promień następnej rundy: {self.engine.radius:.3f}"
        )

    def stop_safely(self) -> None:
        self.stop_training()

    def _set_sound(self, enabled: bool) -> None:
        self.sound_enabled = enabled
        self.sound_button.setText("Dźwięk: włączony" if enabled else "Dźwięk: wyciszony")

    @staticmethod
    def _target_for_exercise(key: str, elapsed: float) -> tuple[float, float]:
        if key == "left_right":
            return (0.5 if int(elapsed / 3) % 2 else -0.5), 0.0
        if key == "front_back":
            return 0.0, (0.45 if int(elapsed / 3) % 2 else -0.45)
        if key == "targets":
            return TARGET_SEQUENCE[int(elapsed / 4) % len(TARGET_SEQUENCE)]
        if key == "moving":
            return 0.45 * math.sin(elapsed * 0.45), 0.35 * math.cos(elapsed * 0.45)
        if key == "limits":
            angle = elapsed * 0.28
            return 0.55 * math.cos(angle), 0.55 * math.sin(angle)
        return 0.0, 0.0

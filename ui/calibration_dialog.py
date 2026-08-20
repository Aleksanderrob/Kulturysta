"""Guided zero and optional reference-load calibration."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
)

from acquisition.calibration import add_reference_scale, calculate_calibration
from app.models import BoardSample, CalibrationSettings


class CalibrationDialog(QDialog):
    """Collect raw samples while acquisition continues outside the GUI thread."""

    def __init__(self, current: CalibrationSettings | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kalibracja / zerowanie")
        self.settings = current or CalibrationSettings()
        self._phase: str | None = None
        self._samples: list[BoardSample] = []
        self._elapsed_ms = 0
        layout = QFormLayout(self)
        self.instructions = QLabel(
            "1. Opróżnij platformę i zbierz zero. 2. Sprawdź masę bliską zeru. "
            "3. Opcjonalnie ustaw znaną masę i zbierz próbki referencyjne."
        )
        self.instructions.setWordWrap(True)
        self.reference_mass = QDoubleSpinBox()
        self.reference_mass.setRange(0.0, 300.0)
        self.reference_mass.setDecimals(2)
        self.reference_mass.setSpecialValueText("brak")
        self.reference_mass.setSuffix(" kg")
        self.zero_button = QPushButton("Zbierz zero — platforma pusta")
        self.reference_button = QPushButton("Zbierz obciążenie referencyjne")
        self.reference_button.setEnabled(self.settings.applied)
        self.progress = QProgressBar()
        self.progress.setRange(0, 2000)
        self.result_label = QLabel(self._description())
        self.result_label.setWordWrap(True)
        layout.addRow(self.instructions)
        layout.addRow("Masa referencyjna:", self.reference_mass)
        layout.addRow(self.zero_button)
        layout.addRow(self.reference_button)
        layout.addRow(self.progress)
        layout.addRow("Parametry:", self.result_label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_calibrated)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self.zero_button.clicked.connect(lambda: self._start_phase("zero"))
        self.reference_button.clicked.connect(lambda: self._start_phase("reference"))
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._tick)

    def add_raw_sample(self, sample: BoardSample) -> None:
        if self._phase is not None:
            self._samples.append(sample)

    def _start_phase(self, phase: str) -> None:
        if phase == "reference" and self.reference_mass.value() <= 0:
            QMessageBox.warning(self, "Masa referencyjna", "Podaj dodatnią masę referencyjną.")
            return
        self._phase = phase
        self._samples.clear()
        self._elapsed_ms = 0
        self.progress.setValue(0)
        self.zero_button.setEnabled(False)
        self.reference_button.setEnabled(False)
        self.timer.start()

    def _tick(self) -> None:
        self._elapsed_ms += self.timer.interval()
        self.progress.setValue(self._elapsed_ms)
        if self._elapsed_ms < 2000:
            return
        self.timer.stop()
        phase = self._phase
        self._phase = None
        try:
            if phase == "zero":
                self.settings = calculate_calibration(self._samples)
            else:
                self.settings = add_reference_scale(
                    self._samples, self.settings, self.reference_mass.value()
                )
            self.result_label.setText(self._description())
        except ValueError as exc:
            QMessageBox.warning(self, "Kalibracja nieudana", str(exc))
        self.zero_button.setEnabled(True)
        self.reference_button.setEnabled(self.settings.applied)

    def _description(self) -> str:
        if not self.settings.applied:
            return "Kalibracja nie została jeszcze wykonana."
        return (
            f"Typ: {self.settings.calibration_type}; offset masy: "
            f"{self.settings.mass_offset_kg:.3f} kg; offset COP: "
            f"({self.settings.cop_x_offset:.4f}, {self.settings.cop_y_offset:.4f}); "
            f"skala: {self.settings.scale_factor:.6f}."
        )

    def _accept_if_calibrated(self) -> None:
        if not self.settings.applied:
            QMessageBox.warning(self, "Brak kalibracji", "Najpierw zbierz próbki zerowe.")
            return
        self.accept()

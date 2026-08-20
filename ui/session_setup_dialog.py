"""Measurement protocol configuration dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
)

from app.models import FilterSettings, SessionConfig

PROTOCOLS = [
    "Stanie swobodne, oczy otwarte",
    "Stanie swobodne, oczy zamknięte",
    "Stopy razem",
    "Tandem stance",
    "Stanie jednonóż — wyłącznie z nadzorem i asekuracją",
    "Sekwencja trzech prób po 30 sekund z przerwami",
]


class SessionSetupDialog(QDialog):
    def __init__(self, config: SessionConfig | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Konfiguracja sesji")
        initial = config or SessionConfig()
        self._initial_filter_settings = initial.filter_settings
        layout = QFormLayout(self)
        self.duration = QDoubleSpinBox()
        self.duration.setRange(1, 1800)
        self.duration.setValue(initial.duration_s)
        self.duration.setSuffix(" s")
        self.protocol = QComboBox()
        self.protocol.addItems(PROTOCOLS)
        self.protocol.setCurrentText(initial.protocol)
        self.protocol.currentTextChanged.connect(self._apply_protocol_defaults)
        self.repetitions = QSpinBox()
        self.repetitions.setRange(1, 20)
        self.repetitions.setValue(initial.repetitions)
        self.break_time = QDoubleSpinBox()
        self.break_time.setRange(0, 600)
        self.break_time.setValue(initial.break_s)
        self.break_time.setSuffix(" s")
        self.eyes = QComboBox()
        self.eyes.addItems(["otwarte", "zamknięte"])
        self.eyes.setCurrentText(initial.eyes)
        self.feet = QLineEdit(initial.foot_position)
        self.note = QLineEdit(initial.note)
        self.filter_kind = QComboBox()
        self.filter_kind.addItem("Brak filtra", "none")
        self.filter_kind.addItem("Średnia krocząca", "moving_average")
        self.filter_kind.addItem("Dolnoprzepustowy Butterwortha", "butterworth")
        filter_index = self.filter_kind.findData(initial.filter_settings.kind)
        self.filter_kind.setCurrentIndex(max(0, filter_index))
        self.filter_window = QSpinBox()
        self.filter_window.setRange(1, 101)
        self.filter_window.setValue(initial.filter_settings.moving_average_window)
        self.filter_order = QSpinBox()
        self.filter_order.setRange(1, 10)
        self.filter_order.setValue(initial.filter_settings.order)
        self.filter_cutoff = QDoubleSpinBox()
        self.filter_cutoff.setRange(0.1, 50.0)
        self.filter_cutoff.setDecimals(2)
        self.filter_cutoff.setValue(initial.filter_settings.cutoff_hz)
        self.filter_cutoff.setSuffix(" Hz")
        for label, widget in (
            ("Czas:", self.duration),
            ("Protokół:", self.protocol),
            ("Powtórzenia:", self.repetitions),
            ("Przerwa:", self.break_time),
            ("Oczy:", self.eyes),
            ("Pozycja stóp:", self.feet),
            ("Notatka:", self.note),
            ("Filtr:", self.filter_kind),
            ("Okno średniej:", self.filter_window),
            ("Rząd Butterwortha:", self.filter_order),
            ("Odcięcie:", self.filter_cutoff),
        ):
            layout.addRow(label, widget)
        self.filter_kind.currentIndexChanged.connect(self._update_filter_controls)
        self._update_filter_controls()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def session_config(self) -> SessionConfig:
        return SessionConfig(
            duration_s=self.duration.value(),
            protocol=self.protocol.currentText(),
            repetitions=self.repetitions.value(),
            break_s=self.break_time.value(),
            eyes=self.eyes.currentText(),
            foot_position=self.feet.text(),
            note=self.note.text(),
            filter_settings=self._filter_settings(),
        )

    def _apply_protocol_defaults(self, protocol: str) -> None:
        if protocol.startswith("Sekwencja trzech prób"):
            self.duration.setValue(30.0)
            self.repetitions.setValue(3)
            self.break_time.setValue(max(15.0, self.break_time.value()))

    def _filter_settings(self) -> FilterSettings:
        return FilterSettings(
            kind=str(self.filter_kind.currentData()),
            moving_average_window=self.filter_window.value(),
            order=self.filter_order.value(),
            cutoff_hz=self.filter_cutoff.value(),
        )

    def _update_filter_controls(self) -> None:
        kind = self.filter_kind.currentData()
        self.filter_window.setEnabled(kind == "moving_average")
        self.filter_order.setEnabled(kind == "butterworth")
        self.filter_cutoff.setEnabled(kind == "butterworth")

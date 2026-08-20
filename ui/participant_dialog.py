"""Validated participant form with identifier-only mode."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
)

from app.models import Participant


class ParticipantDialog(QDialog):
    def __init__(self, participant: Participant | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dane uczestnika")
        self._initial = participant or Participant()
        layout = QFormLayout(self)
        self.identifier = QLineEdit(self._initial.participant_id)
        self.identifier_only = QCheckBox("Używaj wyłącznie identyfikatora (zalecane na pokazach)")
        self.identifier_only.setChecked(self._initial.identifier_only)
        self.first_name = QLineEdit(self._initial.first_name)
        self.last_name = QLineEdit(self._initial.last_name)
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.age.setSpecialValueText("brak")
        self.age.setValue(self._initial.age or 0)
        self.sex = QComboBox()
        self.sex.addItems(["", "kobieta", "mężczyzna", "inna / nie podano"])
        self.sex.setCurrentText(self._initial.sex or "")
        self.height = QLineEdit(
            "" if self._initial.height_cm is None else str(self._initial.height_cm)
        )
        self.mass = QLineEdit(
            "" if self._initial.body_mass_kg is None else str(self._initial.body_mass_kg)
        )
        self.notes = QTextEdit(self._initial.notes)
        layout.addRow("Identyfikator:", self.identifier)
        layout.addRow(self.identifier_only)
        layout.addRow("Imię:", self.first_name)
        layout.addRow("Nazwisko:", self.last_name)
        layout.addRow("Wiek:", self.age)
        layout.addRow("Płeć (opcjonalnie):", self.sex)
        layout.addRow("Wzrost [cm]:", self.height)
        layout.addRow("Masa ciała [kg]:", self.mass)
        layout.addRow("Uwagi:", self.notes)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def participant(self) -> Participant:
        return Participant(
            first_name=self.first_name.text().strip(),
            last_name=self.last_name.text().strip(),
            age=self.age.value() or None,
            sex=self.sex.currentText() or None,
            height_cm=(
                float(self.height.text().replace(",", ".")) if self.height.text().strip() else None
            ),
            body_mass_kg=(
                float(self.mass.text().replace(",", ".")) if self.mass.text().strip() else None
            ),
            participant_id=self.identifier.text().strip(),
            notes=self.notes.toPlainText().strip(),
            identifier_only=self.identifier_only.isChecked(),
        )

    def _validate_and_accept(self) -> None:
        try:
            participant = self.participant()
        except ValueError:
            QMessageBox.warning(self, "Błędne dane", "Wzrost i masa muszą być liczbami.")
            return
        errors = participant.validate()
        if errors:
            QMessageBox.warning(self, "Błędne dane", "\n".join(errors))
            return
        self.accept()

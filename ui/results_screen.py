"""Session result table and PDF action."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models import BoardSample, SessionMetadata
from storage.session_repository import SessionRepository


class ResultsScreen(QWidget):
    def __init__(self, repository: SessionRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.metadata: SessionMetadata | None = None
        self.samples: list[BoardSample] = []
        layout = QVBoxLayout(self)
        self.heading = QLabel("Brak zakończonej sesji")
        layout.addWidget(self.heading)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Parametr", "Wartość"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.pdf_button = QPushButton("Utwórz raport PDF")
        self.pdf_button.setEnabled(False)
        self.pdf_button.clicked.connect(self.create_pdf)
        layout.addWidget(self.pdf_button)

    def show_result(
        self, metadata: SessionMetadata, samples: list[BoardSample], artifacts: object = None
    ) -> None:
        del artifacts
        self.metadata = metadata
        self.samples = samples
        self.heading.setText(
            f"Sesja {metadata.session_id} — {metadata.quality_rating.value} | "
            f"filtr: {metadata.config.filter_settings.kind} | COP: {metadata.config.cop_unit} | "
            f"kalibracja: {metadata.calibration.calibration_type}"
        )
        self.table.setRowCount(len(metadata.metrics))
        for row, (name, value) in enumerate(metadata.metrics.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem("brak" if value is None else str(value)))
        self.pdf_button.setEnabled(True)

    def create_pdf(self) -> None:
        if self.metadata is None:
            return
        try:
            path = self.repository.create_pdf(self.metadata, self.samples)
            QMessageBox.information(self, "Raport", f"Zapisano: {path}")
        except Exception as exc:  # noqa: BLE001 - report backends may raise library-specific errors
            QMessageBox.critical(self, "Błąd raportu", str(exc))

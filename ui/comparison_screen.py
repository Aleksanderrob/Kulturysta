"""Numerical comparison of locally stored sessions for one participant."""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from analysis.comparisons import compare_metric_series
from storage.session_repository import SessionRepository
from ui.comparison_plot import SessionComparisonPlot


class ComparisonScreen(QWidget):
    METRICS: ClassVar[tuple[str, ...]] = (
        "path_length",
        "mean_speed",
        "rms_cop",
        "confidence_ellipse_95_area",
        "mean_mass_kg",
    )

    def __init__(self, repository: SessionRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.records = []
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        layout.addLayout(top)
        self.participant_id = QLineEdit("DEMO")
        self.refresh_button = QPushButton("Wczytaj sesje")
        top.addWidget(QLabel("Id uczestnika:"))
        top.addWidget(self.participant_id)
        top.addWidget(self.refresh_button)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)
        self.compare_button = QPushButton("Porównaj zaznaczone")
        layout.addWidget(self.compare_button)
        self.plot = SessionComparisonPlot(repository)
        layout.addWidget(self.plot)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Sesja", "Parametr", "Wartość", "Zmiana", "Zmiana %", "Kierunek"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.refresh_button.clicked.connect(self.refresh)
        self.compare_button.clicked.connect(self.compare)

    def refresh(self) -> None:
        self.records = self.repository.list_sessions(self.participant_id.text().strip())
        self.list_widget.clear()
        for index, record in enumerate(self.records):
            item = QListWidgetItem(record.get("session_id", "?"))
            item.setData(256, index)
            self.list_widget.addItem(item)

    def compare(self) -> None:
        selected = [self.records[item.data(256)] for item in self.list_widget.selectedItems()]
        self.plot.set_records(selected)
        rows = compare_metric_series(selected, self.METRICS)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["session_id"],
                row["metric"],
                row["value"],
                row["absolute_change"],
                row["percent_change"],
                row["direction"],
            ]
            for column, value in enumerate(values):
                self.table.setItem(
                    row_index, column, QTableWidgetItem("—" if value is None else str(value))
                )

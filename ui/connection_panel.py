"""Connection, backend and simulator scenario controls."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from hardware.simulator_board import SimulatorScenario


class ConnectionPanel(QWidget):
    connect_requested = Signal(str, str)
    disconnect_requested = Signal()
    tare_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("Symulator", "simulator")
        self.backend_combo.addItem("Wii Balance Board", "wii")
        self.scenario_combo = QComboBox()
        for scenario in SimulatorScenario:
            self.scenario_combo.addItem(
                scenario.value.replace("_", " ").capitalize(), scenario.value
            )
        self.connect_button = QPushButton("Połącz")
        self.disconnect_button = QPushButton("Rozłącz")
        self.tare_button = QPushButton("Zeruj")
        self.disconnect_button.setEnabled(False)
        self.status_label = QLabel("Niepołączono")
        self.status_label.setObjectName("connectionStatus")
        for widget in (
            QLabel("Backend:"),
            self.backend_combo,
            QLabel("Scenariusz:"),
            self.scenario_combo,
            self.connect_button,
            self.disconnect_button,
            self.tare_button,
            self.status_label,
        ):
            layout.addWidget(widget)
        layout.addStretch()
        self.connect_button.clicked.connect(
            lambda: self.connect_requested.emit(
                str(self.backend_combo.currentData()), str(self.scenario_combo.currentData())
            )
        )
        self.disconnect_button.clicked.connect(self.disconnect_requested)
        self.tare_button.clicked.connect(self.tare_requested)
        self.backend_combo.currentIndexChanged.connect(
            lambda: self.scenario_combo.setEnabled(self.backend_combo.currentData() == "simulator")
        )

    def set_connected(self, connected: bool, detail: str = "") -> None:
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self.backend_combo.setEnabled(not connected)
        self.scenario_combo.setEnabled(
            not connected and self.backend_combo.currentData() == "simulator"
        )
        self.status_label.setText(
            ("Połączono" if connected else "Niepołączono") + (f" — {detail}" if detail else "")
        )

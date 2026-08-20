"""Main application window and shared non-blocking board controller."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from acquisition.acquisition_worker import AcquisitionWorker
from acquisition.calibration import apply_calibration
from app.config import load_config
from app.constants import APP_NAME, DISCLAIMER
from app.models import BoardSample, CalibrationSettings, Participant
from hardware.base_board import BaseBalanceBoard
from hardware.connection_manager import create_board
from storage.participant_repository import ParticipantRepository
from storage.session_repository import SessionRepository
from ui.calibration_dialog import CalibrationDialog
from ui.comparison_screen import ComparisonScreen
from ui.connection_panel import ConnectionPanel
from ui.cop_widget import CopWidget
from ui.demo_screen import DemoScreen
from ui.measurement_screen import MeasurementScreen
from ui.participant_dialog import ParticipantDialog
from ui.results_screen import ResultsScreen
from ui.session_setup_dialog import SessionSetupDialog
from ui.training_screen import TrainingScreen


class _ConnectWorker(QObject):
    connected = Signal()
    error = Signal(str)
    finished = Signal()

    def __init__(self, board: BaseBalanceBoard) -> None:
        super().__init__()
        self.board = board

    @Slot()
    def run(self) -> None:
        try:
            self.board.connect(timeout_s=10.0)
            self.connected.emit()
        except Exception as exc:
            logging.getLogger(__name__).exception("Błąd połączenia")
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class BoardController(QObject):
    raw_sample_received = Signal(object)
    sample_received = Signal(object)
    connected_changed = Signal(bool, str)
    error = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.board: BaseBalanceBoard | None = None
        self._connect_thread: QThread | None = None
        self._connect_worker: _ConnectWorker | None = None
        self._thread: QThread | None = None
        self._worker: AcquisitionWorker | None = None
        self.calibration = CalibrationSettings()

    def connect_backend(self, backend: str, scenario: str) -> None:
        logging.getLogger(__name__).info(
            "Rozpoczęcie połączenia | backend=%s | scenariusz=%s", backend, scenario
        )
        self.shutdown()
        self.board = create_board(backend, scenario)
        self._connect_thread = QThread(self)
        self._connect_worker = _ConnectWorker(self.board)
        self._connect_worker.moveToThread(self._connect_thread)
        self._connect_thread.started.connect(self._connect_worker.run)
        self._connect_worker.connected.connect(self._start_stream)
        self._connect_worker.error.connect(self.error)
        self._connect_worker.finished.connect(self._connect_thread.quit)
        self._connect_thread.start()

    @Slot()
    def _start_stream(self) -> None:
        if self.board is None:
            return
        info = self.board.get_device_info()
        logging.getLogger(__name__).info("Połączono z backendem: %s", info)
        self.connected_changed.emit(True, str(info.get("backend", "")))
        self._thread = QThread(self)
        self._worker = AcquisitionWorker(self.board)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.sample_ready.connect(self._handle_sample)
        self._worker.error.connect(self.error)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    @Slot(object)
    def _handle_sample(self, sample: BoardSample) -> None:
        self.raw_sample_received.emit(sample)
        self.sample_received.emit(apply_calibration(sample, self.calibration))

    def tare(self) -> None:
        if self.board is None:
            return
        try:
            self.board.tare()
        except Exception as exc:  # noqa: BLE001 - driver exceptions are not standardized
            self.error.emit(str(exc))

    def shutdown(self) -> None:
        if self._worker is not None:
            self._worker.stop()
        if self.board is not None:
            try:
                self.board.stop_stream()
            except Exception:
                logging.getLogger(__name__).exception("Błąd zatrzymania strumienia")
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        if self._connect_thread is not None and self._connect_thread.isRunning():
            self._connect_thread.quit()
            self._connect_thread.wait(1000)
        if self.board is not None:
            try:
                self.board.disconnect()
            except Exception:
                logging.getLogger(__name__).exception("Błąd rozłączenia")
        if self.board is not None:
            self.connected_changed.emit(False, "")
            logging.getLogger(__name__).info("Rozłączono backend")
        self.board = None
        self._worker = None
        self._thread = None


class FeedbackWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kulturysta — feedback")
        self.cop = CopWidget()
        self.setCentralWidget(self.cop)

    def on_sample(self, sample) -> None:
        self.cop.set_sample(
            sample.cop_x, sample.cop_y, sample.cop_unit, (sample.total_weight_kg or 0) >= 5
        )


class MainWindow(QMainWindow):
    def __init__(self, config: dict[str, object] | None = None) -> None:
        super().__init__()
        self.config = config or load_config()
        self.setWindowTitle(f"{APP_NAME} 0.1 — {DISCLAIMER}")
        self.resize(1400, 900)
        self.repository = SessionRepository()
        self.participants = ParticipantRepository()
        self.participant = Participant(participant_id="DEMO", identifier_only=True)
        self.feedback_window: FeedbackWindow | None = None
        self.setWindowIcon(QIcon("assets/logo_placeholder.png"))
        central = QWidget()
        layout = QVBoxLayout(central)
        self.connection_panel = ConnectionPanel()
        layout.addWidget(self.connection_panel)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.measurement = MeasurementScreen(
            self.repository,
            minimum_load_kg=float(self.config.get("minimum_load_kg", 5.0)),
            visualization=dict(self.config.get("visualization", {})),
        )
        self.measurement.config.duration_s = float(self.config.get("measurement_duration_s", 30.0))
        self.training = TrainingScreen(
            duration_s=float(self.config.get("training_duration_s", 60.0)),
            sound_enabled=bool(dict(self.config.get("sound", {})).get("enabled", False)),
        )
        self.demo = DemoScreen()
        self.results = ResultsScreen(self.repository)
        self.comparison = ComparisonScreen(self.repository)
        self.tabs.addTab(self.measurement, "Pomiar")
        self.tabs.addTab(self.training, "Trening")
        self.tabs.addTab(self.demo, "Demo / minigra")
        self.tabs.addTab(self.results, "Wyniki")
        self.tabs.addTab(self.comparison, "Porównanie")
        self.setCentralWidget(central)
        self.controller = BoardController(self)
        self.connection_panel.connect_requested.connect(self.controller.connect_backend)
        self.connection_panel.disconnect_requested.connect(self.controller.shutdown)
        self.connection_panel.tare_requested.connect(self.open_calibration)
        self.controller.connected_changed.connect(self._set_connected)
        self.controller.sample_received.connect(self.measurement.on_sample)
        self.controller.sample_received.connect(self.training.on_sample)
        self.controller.sample_received.connect(self.demo.on_sample)
        self.controller.error.connect(self._show_error)
        self.controller.error.connect(self.measurement.on_stream_error)
        self.measurement.result_ready.connect(self._show_result)
        self._build_menu()
        self._apply_style()

    def _build_menu(self) -> None:
        session_menu = self.menuBar().addMenu("Sesja")
        participant_action = QAction("Uczestnik…", self)
        setup_action = QAction("Konfiguracja pomiaru…", self)
        exit_action = QAction("Zakończ", self)
        session_menu.addActions([participant_action, setup_action, exit_action])
        participant_action.triggered.connect(self.edit_participant)
        setup_action.triggered.connect(self.edit_session)
        exit_action.triggered.connect(self.close)
        view_menu = self.menuBar().addMenu("Widok")
        fullscreen = QAction("Pełny ekran", self)
        fullscreen.setShortcut("F11")
        second = QAction("Feedback na drugim ekranie", self)
        view_menu.addActions([fullscreen, second])
        fullscreen.triggered.connect(
            lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen()
        )
        second.triggered.connect(self.show_second_screen)

    def edit_participant(self) -> None:
        dialog = ParticipantDialog(self.participant, self)
        if dialog.exec():
            self.participant = dialog.participant()
            self.measurement.set_participant(self.participant)
            self.participants.save(
                self.participant, include_personal_data=not self.participant.identifier_only
            )

    def edit_session(self) -> None:
        dialog = SessionSetupDialog(self.measurement.config, self)
        if dialog.exec():
            self.measurement.set_config(dialog.session_config())

    def open_calibration(self) -> None:
        if self.controller.board is None or not self.controller.board.is_connected():
            QMessageBox.information(self, "Kalibracja", "Najpierw połącz platformę lub symulator.")
            return
        dialog = CalibrationDialog(self.controller.calibration, self)
        self.controller.raw_sample_received.connect(dialog.add_raw_sample)
        try:
            if dialog.exec():
                self.controller.calibration = dialog.settings
                self.measurement.set_calibration(dialog.settings)
                logging.getLogger(__name__).info("Zastosowano kalibrację: %s", dialog.settings)
        finally:
            self.controller.raw_sample_received.disconnect(dialog.add_raw_sample)

    def _set_connected(self, connected: bool, detail: str) -> None:
        self.connection_panel.set_connected(connected, detail)
        self.measurement.set_connected(connected)
        self.training.set_connected(connected)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(
            self, "Błąd połączenia lub danych", f"{message}\nSzczegóły: data/logs/app.log"
        )

    def _show_result(self, metadata, samples, artifacts) -> None:
        self.results.show_result(metadata, samples, artifacts)
        self.tabs.setCurrentWidget(self.results)

    def show_second_screen(self) -> None:
        screens = QApplication.screens()
        if len(screens) < 2:
            QMessageBox.information(self, "Drugi ekran", "Wykryto tylko jeden ekran.")
            return
        if self.feedback_window is None:
            self.feedback_window = FeedbackWindow()
            self.controller.sample_received.connect(self.feedback_window.on_sample)
        self.feedback_window.show()
        if self.feedback_window.windowHandle() is not None:
            self.feedback_window.windowHandle().setScreen(screens[1])
        self.feedback_window.showFullScreen()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.measurement.stop_safely()
            self.training.stop_safely()
            self.demo.stop_safely()
            self.showNormal()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.measurement.stop_safely()
        self.training.stop_safely()
        self.demo.stop_safely()
        self.controller.shutdown()
        event.accept()

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #F2F7F4; color: #17251C; font-size: 15px; }
            QPushButton { background: #17653C; color: white; padding: 9px 16px; border-radius: 6px; font-weight: 600; }
            QPushButton:disabled { background: #9FB3A7; }
            QPushButton#stopButton { background: #B42318; font-size: 17px; }
            QLabel#screenBanner { background: #DCEFE3; padding: 10px; font-weight: 700; }
            QLabel#metricTitle { color: #52675A; font-size: 13px; }
            QLabel#metricValue { font-size: 22px; font-weight: 700; }
            QTabBar::tab { padding: 10px 18px; }
            QTabBar::tab:selected { background: #DCEFE3; }
        """)

from dataclasses import replace

from app.models import FilterSettings, SessionConfig
from hardware.simulator_board import SimulatorBoard
from storage.paths import DataPaths
from storage.session_repository import SessionRepository
from ui.main_window import MainWindow
from ui.measurement_screen import MeasurementScreen
from ui.session_setup_dialog import SessionSetupDialog


def test_main_window_opens_all_modes(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.tabs.count() == 5
    for index in range(window.tabs.count()):
        window.tabs.setCurrentIndex(index)
        assert window.tabs.currentWidget() is not None
    window.close()


def test_short_simulated_measurement_saves(qtbot, tmp_path):
    screen = MeasurementScreen(SessionRepository(DataPaths(tmp_path / "data")))
    qtbot.addWidget(screen)
    screen.set_config(SessionConfig(duration_s=0.15, filter_settings=FilterSettings(kind="none")))
    screen.set_connected(True)
    board = SimulatorBoard()
    board.connect()
    base = board.generate_sample(0)
    screen.on_sample(base)
    assert screen.start_button.isEnabled()
    screen.start_measurement(skip_countdown=True)
    for index in range(1, 8):
        screen.on_sample(
            replace(
                board.generate_sample(index * 0.03),
                timestamp_monotonic=base.timestamp_monotonic + index * 0.03,
                sequence_number=index,
            )
        )
    qtbot.waitUntil(lambda: not screen._active, timeout=1500)
    assert list((tmp_path / "data" / "sessions").glob("*/metadata.json"))


def test_board_controller_streams_simulator(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    with qtbot.waitSignal(window.controller.sample_received, timeout=2500):
        window.controller.connect_backend("simulator", "stabilne_stanie")
    assert window.controller.board is not None
    window.close()


def test_two_repetitions_are_saved_as_separate_sessions(qtbot, tmp_path):
    screen = MeasurementScreen(SessionRepository(DataPaths(tmp_path / "data")))
    qtbot.addWidget(screen)
    screen.set_config(
        SessionConfig(
            duration_s=1,
            repetitions=2,
            break_s=0,
            filter_settings=FilterSettings(kind="none"),
        )
    )
    screen.set_connected(True)
    board = SimulatorBoard()
    board.connect()
    base = board.generate_sample(0)
    screen.on_sample(base)
    screen.start_measurement(skip_countdown=True)
    screen.on_sample(base)
    screen.finish_measurement(False)
    assert screen._current_repetition == 2
    screen._countdown_tick()
    screen._countdown_tick()
    screen._countdown_tick()
    assert screen._active
    screen.on_sample(replace(base, timestamp_monotonic=base.timestamp_monotonic + 1))
    screen.finish_measurement(False)
    assert len(list((tmp_path / "data" / "sessions").glob("*/metadata.json"))) == 2


def test_session_setup_applies_sequence_and_filter_defaults(qtbot):
    dialog = SessionSetupDialog()
    qtbot.addWidget(dialog)
    dialog.protocol.setCurrentText("Sekwencja trzech prób po 30 sekund z przerwami")
    dialog.filter_kind.setCurrentIndex(dialog.filter_kind.findData("butterworth"))
    config = dialog.session_config()
    assert (config.duration_s, config.repetitions, config.break_s) == (30, 3, 15)
    assert config.filter_settings.kind == "butterworth"
    assert dialog.filter_cutoff.isEnabled()

import pytest

from app.models import QualityFlag
from hardware.simulator_board import SimulatorBoard, SimulatorScenario


@pytest.mark.parametrize("scenario", list(SimulatorScenario))
def test_every_simulator_scenario_generates(scenario):
    board = SimulatorBoard(scenario=scenario)
    board.connect()
    elapsed = 3.5 if scenario in (SimulatorScenario.STEP_OFF, SimulatorScenario.DISCONNECT) else 1.0
    sample = board.generate_sample(elapsed)
    assert sample.synthetic_data is True
    if scenario == SimulatorScenario.DISCONNECT:
        assert not sample.connection_ok
    else:
        assert sample.connection_ok


def test_sensor_sum_matches_weight():
    board = SimulatorBoard(SimulatorScenario.WEIGHT_SHIFT)
    board.connect()
    sample = board.generate_sample(1.2)
    assert sum(
        (sample.top_left, sample.top_right, sample.bottom_left, sample.bottom_right)
    ) == pytest.approx(sample.total_weight_kg)


def test_step_off_is_flagged():
    board = SimulatorBoard(SimulatorScenario.STEP_OFF)
    board.connect()
    sample = board.generate_sample(3.5)
    assert QualityFlag.STEP_OFF in sample.quality_flags
    assert sample.total_weight_kg < 1


def test_stream_contract():
    board = SimulatorBoard(sample_rate_hz=200)
    board.connect()
    board.start_stream()
    sample = board.get_sample()
    board.stop_stream()
    board.disconnect()
    assert sample.sequence_number == 0
    assert not board.is_connected()

from hardware.base_board import BaseBalanceBoard
from hardware.simulator_board import SimulatorBoard
from hardware.wii_board_adapter import WiiBoardAdapter


class FakeDriver:
    def __init__(self):
        self.connected = False
        self.stopped = False

    def connect(self, timeout_s=10):
        self.connected = True

    def tare(self):
        return None

    def stream(self):
        return iter([{"weight": 70, "cop_x": 0.1, "cop_y": -0.2}])

    def stop_stream(self):
        self.stopped = True

    def disconnect(self):
        self.connected = False


def test_simulator_implements_contract():
    assert isinstance(SimulatorBoard(), BaseBalanceBoard)


def test_wii_adapter_with_mock_driver():
    driver = FakeDriver()
    adapter = WiiBoardAdapter(lambda: driver, cop_unit="normalized")
    adapter.connect()
    adapter.tare()
    adapter.start_stream()
    sample = adapter.get_sample()
    adapter.stop_stream()
    adapter.disconnect()
    assert sample.total_weight_kg == 70
    assert sample.cop_x == 0.1
    assert driver.stopped

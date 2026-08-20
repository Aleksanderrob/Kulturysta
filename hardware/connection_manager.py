"""Board factory isolated from user-interface code."""

from __future__ import annotations

from hardware.base_board import BaseBalanceBoard
from hardware.simulator_board import SimulatorBoard, SimulatorScenario
from hardware.wii_board_adapter import WiiBoardAdapter


def create_board(backend: str, scenario: str = SimulatorScenario.SWAY.value) -> BaseBalanceBoard:
    if backend == "simulator":
        return SimulatorBoard(scenario=scenario)
    if backend == "wii":
        return WiiBoardAdapter()
    raise ValueError(f"Nieznany backend: {backend}")

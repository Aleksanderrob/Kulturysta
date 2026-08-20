"""Deterministic, offline Wii Balance Board simulator."""

from __future__ import annotations

import math
import random
import threading
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.models import BoardSample, QualityFlag
from hardware.base_board import BaseBalanceBoard


class SimulatorScenario(str, Enum):
    STABLE = "stabilne_stanie"
    SWAY = "kolysanie_sinusoidalne"
    WEIGHT_SHIFT = "przenoszenie_ciezaru"
    NOISE = "losowe_zaklocenia"
    STEP_OFF = "zejscie_z_platformy"
    DISCONNECT = "utrata_polaczenia"
    ARTIFACT = "artefakt"
    IRREGULAR = "nieregularne_probkowanie"


class SimulatorBoard(BaseBalanceBoard):
    """Generate four coherent sensor loads and normalized COP values."""

    def __init__(
        self,
        scenario: SimulatorScenario | str = SimulatorScenario.SWAY,
        sample_rate_hz: float = 50.0,
        body_mass_kg: float = 70.0,
        seed: int = 42,
    ) -> None:
        self.scenario = SimulatorScenario(scenario)
        self.sample_rate_hz = float(sample_rate_hz)
        self.body_mass_kg = float(body_mass_kg)
        self._rng = random.Random(seed)
        self._connected = False
        self._streaming = False
        self._started = 0.0
        self._next_due = 0.0
        self._sequence = 0
        self._tare_offset = 0.0
        self._lock = threading.Lock()

    def connect(self, timeout_s: float = 10.0) -> None:
        del timeout_s
        with self._lock:
            self._connected = True

    def disconnect(self) -> None:
        with self._lock:
            self._streaming = False
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def tare(self) -> None:
        self._tare_offset = 0.0

    def start_stream(self) -> None:
        if not self._connected:
            raise ConnectionError("Symulator nie jest połączony.")
        self._streaming = True
        self._started = time.monotonic()
        self._next_due = self._started
        self._sequence = 0

    def stop_stream(self) -> None:
        self._streaming = False

    def get_sample(self) -> BoardSample:
        if not self._connected or not self._streaming:
            raise ConnectionError("Strumień symulatora nie jest aktywny.")
        interval = 1.0 / max(self.sample_rate_hz, 1.0)
        jitter = (
            self._rng.uniform(-0.012, 0.018)
            if self.scenario == SimulatorScenario.IRREGULAR
            else 0.0
        )
        self._next_due += max(0.001, interval + jitter)
        delay = self._next_due - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        elapsed = time.monotonic() - self._started
        sample = self.generate_sample(elapsed)
        self._sequence += 1
        return sample

    def generate_sample(self, elapsed_s: float) -> BoardSample:
        """Generate one sample at an explicit elapsed time, useful for tests and previews."""
        x, y, weight, connected, flags = self._scenario_values(elapsed_s)
        now = time.monotonic()
        if not connected:
            return BoardSample(
                now,
                datetime.now(UTC).isoformat(),
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                self._sequence,
                False,
                tuple(flags),
                synthetic_data=True,
            )
        x = max(-1.2, min(1.2, x))
        y = max(-1.2, min(1.2, y))
        weight = max(0.0, weight - self._tare_offset)
        tl = weight * (1.0 - x) * (1.0 + y) / 4.0
        tr = weight * (1.0 + x) * (1.0 + y) / 4.0
        bl = weight * (1.0 - x) * (1.0 - y) / 4.0
        br = weight * (1.0 + x) * (1.0 - y) / 4.0
        return BoardSample(
            now,
            datetime.now(UTC).isoformat(),
            tl,
            tr,
            bl,
            br,
            weight,
            x,
            y,
            self._sequence,
            True,
            tuple(flags),
            "normalized",
            True,
        )

    def _scenario_values(self, t: float) -> tuple[float, float, float, bool, list[QualityFlag]]:
        noise = lambda scale: self._rng.gauss(0.0, scale)
        weight = self.body_mass_kg + noise(0.08)
        flags: list[QualityFlag] = []
        if self.scenario == SimulatorScenario.STABLE:
            return noise(0.008), noise(0.008), weight, True, flags
        if self.scenario == SimulatorScenario.SWAY:
            return (
                0.18 * math.sin(2 * math.pi * 0.18 * t) + noise(0.01),
                0.12 * math.sin(2 * math.pi * 0.13 * t + 0.6) + noise(0.01),
                weight,
                True,
                flags,
            )
        if self.scenario == SimulatorScenario.WEIGHT_SHIFT:
            return (
                0.65 * math.sin(2 * math.pi * 0.10 * t),
                0.35 * math.sin(2 * math.pi * 0.07 * t),
                weight,
                True,
                flags,
            )
        if self.scenario == SimulatorScenario.NOISE:
            return noise(0.16), noise(0.16), weight + noise(0.6), True, flags
        if self.scenario == SimulatorScenario.STEP_OFF and 3.0 <= t % 8.0 <= 5.0:
            return (
                0.0,
                0.0,
                max(0.0, noise(0.02)),
                True,
                [QualityFlag.STEP_OFF, QualityFlag.LOW_LOAD],
            )
        if self.scenario == SimulatorScenario.DISCONNECT and 3.0 <= t % 8.0 <= 4.0:
            return 0.0, 0.0, 0.0, False, [QualityFlag.NO_CONNECTION]
        if self.scenario == SimulatorScenario.ARTIFACT and 2.95 <= t % 6.0 <= 3.05:
            return 1.15, -1.15, weight + 25.0, True, [QualityFlag.COP_JUMP, QualityFlag.MASS_JUMP]
        return 0.12 * math.sin(t), 0.1 * math.cos(t * 0.7), weight, True, flags

    def get_device_info(self) -> dict[str, Any]:
        return {
            "backend": "simulator",
            "scenario": self.scenario.value,
            "synthetic_data": True,
            "cop_unit": "normalized",
        }

    def get_battery_level(self) -> float | None:
        return 100.0

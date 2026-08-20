"""Backend contract used by acquisition and GUI layers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models import BoardSample


class BaseBalanceBoard(ABC):
    """Abstract synchronous board interface; callers must read it outside the GUI thread."""

    @abstractmethod
    def connect(self, timeout_s: float = 10.0) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    def tare(self) -> None: ...

    @abstractmethod
    def start_stream(self) -> None: ...

    @abstractmethod
    def stop_stream(self) -> None: ...

    @abstractmethod
    def get_sample(self) -> BoardSample: ...

    @abstractmethod
    def get_device_info(self) -> dict[str, Any]: ...

    def get_battery_level(self) -> float | None:
        return None

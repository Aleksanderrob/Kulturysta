"""Runtime-inspected adapter for the separately maintained ``wbb-module`` package."""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Callable, Iterator, Mapping
from typing import Any

from app.models import BoardSample
from hardware.base_board import BaseBalanceBoard
from hardware.sample_normalizer import normalize_sample


class WiiBoardAdapter(BaseBalanceBoard):
    """Adapt the locally installed driver using a verified/configurable method map.

    The default map uses only the three API hints supplied with the project (``connect``,
    ``tare`` and ``stream``). Optional stop/disconnect methods are detected, never required.
    """

    def __init__(
        self,
        driver_factory: Callable[[], Any] | None = None,
        method_map: Mapping[str, str] | None = None,
        cop_unit: str = "unknown",
    ) -> None:
        self._factory = driver_factory
        self._driver: Any = None
        self._iterator: Iterator[Any] | None = None
        self._connected = False
        self._streaming = False
        self._sequence = 0
        self._cop_unit = cop_unit
        self._methods = {
            "connect": "connect",
            "tare": "tare",
            "stream": "stream",
            **(method_map or {}),
        }

    @staticmethod
    def inspect_installed_api() -> dict[str, Any]:
        """Return public API facts for diagnostics without connecting to hardware."""
        module = importlib.import_module("wbb")
        board_class = module.BalanceBoard
        methods = {
            name: str(inspect.signature(member))
            for name, member in inspect.getmembers(board_class, predicate=callable)
            if not name.startswith("_")
        }
        return {"module": module.__name__, "class": board_class.__name__, "methods": methods}

    def _create_driver(self) -> Any:
        if self._factory is not None:
            return self._factory()
        module = importlib.import_module("wbb")
        return module.BalanceBoard()

    def _method(self, operation: str, required: bool = True) -> Callable[..., Any] | None:
        name = self._methods.get(operation, operation)
        method = getattr(self._driver, name, None)
        if required and not callable(method):
            raise AttributeError(
                f"Sterownik wbb nie udostępnia wymaganej metody {name!r} ({operation})."
            )
        return method if callable(method) else None

    def connect(self, timeout_s: float = 10.0) -> None:
        self._driver = self._create_driver()
        method = self._method("connect")
        signature = inspect.signature(method)
        result = method(timeout_s=timeout_s) if "timeout_s" in signature.parameters else method()
        if result is False:
            raise ConnectionError("Sterownik wbb zgłosił nieudane połączenie.")
        self._connected = True

    def disconnect(self) -> None:
        self.stop_stream()
        for operation in ("disconnect", "close"):
            method = self._method(operation, required=False)
            if method:
                method()
                break
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def tare(self) -> None:
        self._method("tare")()

    def start_stream(self) -> None:
        if not self._connected:
            raise ConnectionError("Platforma nie jest połączona.")
        stream = self._method("stream")()
        self._iterator = iter(stream)
        self._streaming = True

    def stop_stream(self) -> None:
        if self._driver is not None:
            for operation in ("stop_stream", "stop"):
                method = self._method(operation, required=False)
                if method:
                    method()
                    break
        self._streaming = False
        self._iterator = None

    def get_sample(self) -> BoardSample:
        if not self._streaming or self._iterator is None:
            raise ConnectionError("Strumień platformy nie jest aktywny.")
        raw = next(self._iterator)
        sample = normalize_sample(raw, self._sequence, self._cop_unit)
        self._sequence += 1
        return sample

    def get_device_info(self) -> dict[str, Any]:
        info = {"backend": "wbb-module", "synthetic_data": False, "cop_unit": self._cop_unit}
        if self._driver is not None:
            method = self._method("get_device_info", required=False)
            if method:
                value = method()
                if isinstance(value, Mapping):
                    info.update(value)
        return info

    def get_battery_level(self) -> float | None:
        if self._driver is None:
            return None
        method = self._method("get_battery_level", required=False)
        return float(method()) if method else None

"""Qt worker that confines blocking board reads to a dedicated thread."""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QObject, Signal, Slot

from app.models import BoardSample
from hardware.base_board import BaseBalanceBoard


class AcquisitionWorker(QObject):
    sample_ready = Signal(object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, board: BaseBalanceBoard) -> None:
        super().__init__()
        self.board = board
        self._stop = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            self.board.start_stream()
            while not self._stop.is_set():
                sample: BoardSample = self.board.get_sample()
                self.sample_ready.emit(sample)
        except StopIteration:
            self.error.emit("Strumień danych został zatrzymany przez sterownik.")
        except Exception as exc:
            logging.getLogger(__name__).exception("Błąd wątku akwizycji")
            if not self._stop.is_set():
                self.error.emit(str(exc))
        finally:
            try:
                self.board.stop_stream()
            except Exception:
                logging.getLogger(__name__).exception("Nie udało się zatrzymać strumienia")
            self.finished.emit()

    @Slot()
    def stop(self) -> None:
        self._stop.set()

"""Kulturysta desktop application entry point."""

from __future__ import annotations

import logging
import platform
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app import __version__
from app.config import load_config
from app.logging_config import configure_logging
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> int:
    configure_logging()
    logger.info(
        "Start Kulturysta %s | Python %s | %s",
        __version__,
        platform.python_version(),
        platform.platform(),
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Kulturysta")
    window = MainWindow(load_config())
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(1200, window.close)
    result = app.exec()
    logger.info("Bezpieczne zamknięcie aplikacji")
    return result


if __name__ == "__main__":
    raise SystemExit(main())

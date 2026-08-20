"""Optional Qt system-sound feedback without bundled copyrighted audio."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


def play_target_cue(enabled: bool) -> None:
    if enabled:
        QApplication.beep()

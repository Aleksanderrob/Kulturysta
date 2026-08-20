"""Large-display star collector controlled by COP or arrow keys."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.models import BoardSample
from games.star_collector import StarCollector


class StarGameWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.game = StarCollector()
        self.setMinimumSize(600, 450)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#071A12"))

        def point(x: float, y: float) -> tuple[float, float]:
            return ((x + 1) / 2 * self.width(), (1 - y) / 2 * self.height())

        sx, sy = point(self.game.star_x, self.game.star_y)
        px, py = point(self.game.player_x, self.game.player_y)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FACC15"))
        painter.drawEllipse(int(sx - 18), int(sy - 18), 36, 36)
        painter.setBrush(QColor("#34D399"))
        painter.drawEllipse(int(px - 16), int(py - 16), 32, 32)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(20, 38, f"Gwiazdy: {self.game.score}")

    def update_cop(self, x: float, y: float) -> None:
        self.game.update(x, y)
        self.update()

    def keyPressEvent(self, event) -> None:
        step = 0.08
        x, y = self.game.player_x, self.game.player_y
        if event.key() == Qt.Key.Key_Left:
            x -= step
        elif event.key() == Qt.Key.Key_Right:
            x += step
        elif event.key() == Qt.Key.Key_Up:
            y += step
        elif event.key() == Qt.Key.Key_Down:
            y -= step
        else:
            return super().keyPressEvent(event)
        self.update_cop(x, y)


class DemoScreen(QWidget):
    def __init__(self, duration_s: float = 60.0, parent=None) -> None:
        super().__init__(parent)
        self.duration_s = duration_s
        self.active = False
        self._started = 0.0
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("DEMO — zbieraj gwiazdy przesuwając ciężar. Sterowanie awaryjne: strzałki.")
        )
        self.game_widget = StarGameWidget()
        layout.addWidget(self.game_widget, 1)
        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.start_button = QPushButton("Start / restart")
        self.stop_button = QPushButton("PRZERWIJ")
        self.stop_button.setObjectName("stopButton")
        self.timer_label = QLabel("60.0 s")
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.timer_label)
        controls.addStretch()
        self.start_button.clicked.connect(self.start_demo)
        self.stop_button.clicked.connect(self.stop_demo)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._tick)

    def start_demo(self) -> None:
        self.game_widget.game.restart()
        self.game_widget.setFocus()
        self.active = True
        self._started = time.monotonic()
        self.timer.start()
        self.game_widget.update()

    def stop_demo(self) -> None:
        self.active = False
        self.timer.stop()

    def on_sample(self, sample: BoardSample) -> None:
        if self.active and sample.cop_x is not None and sample.cop_y is not None:
            self.game_widget.update_cop(sample.cop_x, sample.cop_y)

    def _tick(self) -> None:
        remaining = max(0.0, self.duration_s - (time.monotonic() - self._started))
        self.timer_label.setText(f"{remaining:.1f} s")
        if remaining <= 0:
            self.stop_demo()

    def stop_safely(self) -> None:
        self.stop_demo()

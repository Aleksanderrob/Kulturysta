"""Responsive live COP plot with bounded path history and stable scaling."""

from __future__ import annotations

import math
from collections import deque

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class CopWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, max_points: int = 750) -> None:
        super().__init__(parent)
        self.setMinimumSize(420, 380)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._path: deque[tuple[float, float]] = deque(maxlen=max_points)
        self._x: float | None = None
        self._y: float | None = None
        self._unit = "normalized"
        self._target: tuple[float, float, float] | None = None
        self._loaded = False
        self._scale_mode = "fixed"
        self._range = 1.0

    def set_sample(
        self, x: float | None, y: float | None, unit: str = "normalized", loaded: bool = True
    ) -> None:
        if x is None or y is None or not math.isfinite(x) or not math.isfinite(y):
            self._x = self._y = None
            self._loaded = False
        else:
            self._x, self._y, self._unit, self._loaded = float(x), float(y), unit, loaded
            self._path.append((self._x, self._y))
            if self._scale_mode == "auto":
                required = max(abs(self._x), abs(self._y), 0.2) * 1.20
                if required > self._range:
                    self._range = required
                else:
                    self._range = max(0.2, self._range * 0.9995)
        self.update()

    def set_target(self, x: float, y: float, radius: float) -> None:
        self._target = (x, y, radius)
        self.update()

    def clear_target(self) -> None:
        self._target = None
        self.update()

    def clear_path(self) -> None:
        self._path.clear()
        self.update()

    def set_scale(self, mode: str, fixed_range: float = 1.0) -> None:
        self._scale_mode = mode
        self._range = max(0.01, float(fixed_range))

    def _plot_rect(self) -> QRectF:
        side = max(20.0, min(self.width() - 80.0, self.height() - 80.0))
        return QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

    def _point(self, x: float, y: float, rect: QRectF) -> QPointF:
        return QPointF(
            rect.center().x() + x / self._range * rect.width() / 2,
            rect.center().y() - y / self._range * rect.height() / 2,
        )

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#F7FAF8"))
        rect = self._plot_rect()
        painter.setPen(QPen(QColor("#B8C8BE"), 2))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(rect, 14, 14)
        painter.setPen(QPen(QColor("#C7D7CD"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(rect.left(), rect.center().y(), rect.right(), rect.center().y())
        painter.drawLine(rect.center().x(), rect.top(), rect.center().x(), rect.bottom())
        painter.setPen(QColor("#405548"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            QRectF(rect.left(), rect.bottom() + 8, rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "lewo  ←  ML  →  prawo",
        )
        painter.drawText(10, int(rect.top() + 15), "przód ↑")
        painter.drawText(10, int(rect.bottom()), "tył ↓")
        if self._target is not None:
            tx, ty, radius = self._target
            center = self._point(tx, ty, rect)
            diameter = radius / self._range * rect.width()
            painter.setPen(QPen(QColor("#16A34A"), 2))
            painter.setBrush(QColor(34, 197, 94, 35))
            painter.drawEllipse(center, diameter / 2, diameter / 2)
        if len(self._path) > 1:
            painter.setPen(QPen(QColor(30, 120, 74, 150), 2))
            path = QPainterPath(self._point(*self._path[0], rect))
            for point in list(self._path)[1:]:
                path.lineTo(self._point(*point, rect))
            painter.save()
            painter.setClipRect(rect)
            painter.drawPath(path)
            painter.restore()
        if self._x is not None and self._y is not None and self._loaded:
            outside = abs(self._x) > self._range or abs(self._y) > self._range
            shown_x = max(-self._range, min(self._range, self._x))
            shown_y = max(-self._range, min(self._range, self._y))
            current = self._point(shown_x, shown_y, rect)
            painter.setPen(QPen(QColor("#083D24"), 3))
            painter.setBrush(QColor("#22C55E") if not outside else QColor("#F97316"))
            painter.drawEllipse(current, 10, 10)
            if outside:
                painter.setPen(QColor("#B45309"))
                painter.drawText(
                    rect.adjusted(8, 8, -8, -8),
                    Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
                    "COP poza skalą",
                )
            painter.setPen(QColor("#243D2E"))
            painter.drawText(
                20, self.height() - 18, f"X: {self._x:.3f}  Y: {self._y:.3f} [{self._unit}]"
            )
        else:
            painter.setPen(QColor("#8B3A3A"))
            painter.setFont(QFont("Arial", 15, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "BRAK OBCIĄŻENIA / DANYCH")

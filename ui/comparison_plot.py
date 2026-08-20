"""Overlay stabilograms and show a neutral metric trend."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from storage.session_repository import SessionRepository


class SessionComparisonPlot(QWidget):
    def __init__(self, repository: SessionRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.records: list[dict[str, object]] = []
        self.paths: list[list[tuple[float, float]]] = []
        self.metric = "path_length"
        self.setMinimumHeight(250)

    def set_records(self, records: list[dict[str, object]]) -> None:
        self.records = records
        self.paths = [self.repository.load_stabilogram(record) for record in records]
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))
        left = QRectF(35, 35, self.width() * 0.55 - 50, self.height() - 65)
        right = QRectF(self.width() * 0.58, 35, self.width() * 0.38, self.height() - 65)
        self._frame(painter, left, "Nałożone stabilogramy")
        self._frame(painter, right, f"Trend: {self.metric}")
        if not self.records:
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "Zaznacz co najmniej dwie sesje"
            )
            return
        palette = [QColor("#16A34A"), QColor("#2563EB"), QColor("#F97316"), QColor("#9333EA")]
        all_points = [point for path in self.paths for point in path]
        if all_points:
            limit = max(max(abs(x), abs(y)) for x, y in all_points)
            limit = max(limit * 1.1, 0.01)
            for index, points in enumerate(self.paths):
                if not points:
                    continue
                painter.setPen(QPen(palette[index % len(palette)], 1.5))
                path = QPainterPath(self._cop_point(points[0], left, limit))
                for point in points[1:]:
                    path.lineTo(self._cop_point(point, left, limit))
                painter.save()
                painter.setClipRect(left)
                painter.drawPath(path)
                painter.restore()
        values = [record.get("metrics", {}).get(self.metric) for record in self.records]
        finite = [
            float(value)
            for value in values
            if isinstance(value, (int, float)) and math.isfinite(value)
        ]
        if finite:
            low, high = min(finite), max(finite)
            if high == low:
                high = low + 1.0
            trend_path = QPainterPath()
            for index, value in enumerate(values):
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    continue
                x = right.left() + (index / max(1, len(values) - 1)) * right.width()
                y = right.bottom() - ((value - low) / (high - low)) * right.height()
                (
                    trend_path.moveTo(x, y)
                    if trend_path.elementCount() == 0
                    else trend_path.lineTo(x, y)
                )
                painter.setBrush(palette[index % len(palette)])
                painter.drawEllipse(QPointF(x, y), 4, 4)
            painter.setPen(QPen(QColor("#334155"), 2))
            painter.drawPath(trend_path)

    @staticmethod
    def _frame(painter: QPainter, rect: QRectF, title: str) -> None:
        painter.setPen(QPen(QColor("#A7B8AD"), 1))
        painter.drawRect(rect)
        painter.setPen(QColor("#243D2E"))
        painter.drawText(rect.adjusted(0, -25, 0, 0), Qt.AlignmentFlag.AlignTop, title)

    @staticmethod
    def _cop_point(point: tuple[float, float], rect: QRectF, limit: float) -> QPointF:
        x, y = point
        return QPointF(
            rect.center().x() + x / limit * rect.width() / 2,
            rect.center().y() - y / limit * rect.height() / 2,
        )

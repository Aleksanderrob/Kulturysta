"""PDF report with vector COP and time-series plots."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.constants import DISCLAIMER
from app.models import BoardSample, SessionMetadata


class _LinePlot(Flowable):
    def __init__(
        self,
        series: list[list[tuple[float, float]]],
        labels: list[str],
        width: float = 170 * mm,
        height: float = 70 * mm,
    ) -> None:
        super().__init__()
        self.series, self.labels, self.width, self.height = series, labels, width, height

    def draw(self) -> None:
        canvas = self.canv
        margin = 12
        all_points = [point for serie in self.series for point in serie]
        if not all_points:
            canvas.drawString(margin, self.height / 2, "Brak danych do wykresu")
            return
        xs, ys = zip(*all_points)
        xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
        if xmax == xmin:
            xmax += 1
        if ymax == ymin:
            ymax += 1
        canvas.setStrokeColor(colors.grey)
        canvas.rect(margin, margin, self.width - 2 * margin, self.height - 2 * margin)
        palette = [
            colors.HexColor("#22C55E"),
            colors.HexColor("#2563EB"),
            colors.HexColor("#F97316"),
        ]
        for index, serie in enumerate(self.series):
            canvas.setStrokeColor(palette[index % len(palette)])
            path = canvas.beginPath()
            for point_index, (x, y) in enumerate(serie):
                px = margin + (x - xmin) / (xmax - xmin) * (self.width - 2 * margin)
                py = margin + (y - ymin) / (ymax - ymin) * (self.height - 2 * margin)
                path.moveTo(px, py) if point_index == 0 else path.lineTo(px, py)
            canvas.drawPath(path)
        canvas.setFillColor(colors.black)
        canvas.drawString(margin, 1, " / ".join(self.labels))


def _finite_points(
    samples: Iterable[BoardSample], x_name: str, y_name: str
) -> list[tuple[float, float]]:
    import math

    points = []
    for sample in samples:
        x, y = getattr(sample, x_name), getattr(sample, y_name)
        if x is not None and y is not None and math.isfinite(x) and math.isfinite(y):
            points.append((float(x), float(y)))
    return points


def export_pdf(
    metadata: SessionMetadata,
    samples: list[BoardSample],
    path: Path,
    include_personal_data: bool = False,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    story: list[object] = [
        Paragraph("Kulturysta — raport sesji", styles["Title"]),
        Paragraph(DISCLAIMER, styles["Heading3"]),
        Spacer(1, 5 * mm),
    ]
    logo_path = Path("assets/logo_placeholder.png")
    if logo_path.exists():
        story.insert(0, Image(str(logo_path), width=22 * mm, height=22 * mm))
    participant = metadata.participant.participant_id
    if include_personal_data and not metadata.participant.identifier_only:
        participant += f" — {metadata.participant.first_name} {metadata.participant.last_name}"
    details = [
        ["Sesja", metadata.session_id],
        ["Uczestnik", participant],
        ["Data", metadata.started_at],
        ["Protokół", metadata.config.protocol],
        ["Backend", metadata.backend],
        ["Dane syntetyczne", "tak" if metadata.synthetic_data else "nie"],
        ["Kalibracja", metadata.calibration.calibration_type],
        ["Filtr", metadata.config.filter_settings.kind],
        ["Jakość", metadata.quality_rating.value],
    ]
    table = Table(details, colWidths=[45 * mm, 120 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5EE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend(
        [
            table,
            Spacer(1, 6 * mm),
            Paragraph("Wykres COP X-Y", styles["Heading2"]),
            _LinePlot(
                [_finite_points(samples, "cop_x", "cop_y")], [f"COP [{metadata.config.cop_unit}]"]
            ),
        ]
    )
    t0 = samples[0].timestamp_monotonic if samples else 0.0
    x_time = [(s.timestamp_monotonic - t0, s.cop_x) for s in samples if s.cop_x is not None]
    y_time = [(s.timestamp_monotonic - t0, s.cop_y) for s in samples if s.cop_y is not None]
    mass_time = [
        (s.timestamp_monotonic - t0, s.total_weight_kg)
        for s in samples
        if s.total_weight_kg is not None
    ]
    story.extend(
        [
            Paragraph("COP w czasie", styles["Heading2"]),
            _LinePlot([x_time, y_time], ["COP X", "COP Y"]),
            Paragraph("Masa w czasie", styles["Heading2"]),
            _LinePlot([mass_time], ["Masa [kg]"]),
            PageBreak(),
            Paragraph("Wyniki", styles["Heading2"]),
        ]
    )
    metric_rows = [["Parametr", "Wartość"]] + [
        [key, "brak" if value is None else str(value)] for key, value in metadata.metrics.items()
    ]
    metrics_table = Table(metric_rows, colWidths=[85 * mm, 80 * mm], repeatRows=1)
    metrics_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEFE3")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(
        [
            metrics_table,
            Spacer(1, 5 * mm),
            Paragraph("Flagi jakości", styles["Heading2"]),
            Paragraph(
                ", ".join(flag.value for flag in metadata.quality_flags)
                or "Brak wykrytych ostrzeżeń.",
                styles["BodyText"],
            ),
            Spacer(1, 4 * mm),
            Paragraph(
                "Neutralne podsumowanie: raport przedstawia wyniki sesji i nie stanowi interpretacji klinicznej.",
                styles["BodyText"],
            ),
        ]
    )
    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    document.build(story)
    return path

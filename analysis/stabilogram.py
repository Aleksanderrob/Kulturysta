"""Plot-ready stabilogram extraction."""

from __future__ import annotations

from app.models import BoardSample


def stabilogram_points(
    samples: list[BoardSample], filtered: bool = True
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for sample in samples:
        x = (
            sample.filtered_cop_x
            if filtered and sample.filtered_cop_x is not None
            else sample.cop_x
        )
        y = (
            sample.filtered_cop_y
            if filtered and sample.filtered_cop_y is not None
            else sample.cop_y
        )
        if x is not None and y is not None:
            points.append((float(x), float(y)))
    return points

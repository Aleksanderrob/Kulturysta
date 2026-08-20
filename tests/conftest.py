from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.models import BoardSample


@pytest.fixture
def sample_factory():
    def factory(
        t: float, x: float = 0.0, y: float = 0.0, weight: float = 70.0, sequence: int = 0
    ) -> BoardSample:
        tl = weight * (1 - x) * (1 + y) / 4
        tr = weight * (1 + x) * (1 + y) / 4
        bl = weight * (1 - x) * (1 - y) / 4
        br = weight * (1 + x) * (1 - y) / 4
        return BoardSample(
            t,
            f"2026-01-01T00:00:{t:06.3f}Z",
            tl,
            tr,
            bl,
            br,
            weight,
            x,
            y,
            sequence,
            cop_unit="normalized",
            synthetic_data=True,
        )

    return factory

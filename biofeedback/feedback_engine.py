"""Continuous target/dwell feedback state."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class FeedbackState:
    inside: bool
    entered: bool
    exited: bool
    distance: float


class FeedbackEngine:
    def __init__(self, target_x: float = 0.0, target_y: float = 0.0, radius: float = 0.18) -> None:
        self.target_x, self.target_y, self.radius = target_x, target_y, radius
        self._inside = False

    def update(self, cop_x: float, cop_y: float) -> FeedbackState:
        distance = math.hypot(cop_x - self.target_x, cop_y - self.target_y)
        inside = distance <= self.radius
        state = FeedbackState(
            inside, inside and not self._inside, self._inside and not inside, distance
        )
        self._inside = inside
        return state

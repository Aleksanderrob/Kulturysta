"""Transparent, bounded difficulty adaptation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AdaptiveDifficulty:
    target_radius: float = 0.18
    minimum_radius: float = 0.05
    maximum_radius: float = 0.40
    history: list[float] = field(default_factory=list)

    def update(self, score_percent: float) -> float:
        self.history.append(float(score_percent))
        if score_percent < 50.0:
            self.target_radius = min(self.maximum_radius, self.target_radius * 1.10)
        elif len(self.history) >= 2 and self.history[-1] > 85.0 and self.history[-2] > 85.0:
            self.target_radius = max(self.minimum_radius, self.target_radius * 0.90)
        return self.target_radius

"""Pure state model for the star collector minigame."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass(slots=True)
class StarCollector:
    seed: int = 7
    player_x: float = 0.0
    player_y: float = 0.0
    star_x: float = 0.35
    star_y: float = 0.2
    score: int = 0
    hit_radius: float = 0.16
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def update(self, cop_x: float, cop_y: float) -> bool:
        self.player_x = max(-1.0, min(1.0, cop_x))
        self.player_y = max(-1.0, min(1.0, cop_y))
        if math.hypot(self.player_x - self.star_x, self.player_y - self.star_y) <= self.hit_radius:
            self.score += 1
            self.star_x = self._rng.uniform(-0.72, 0.72)
            self.star_y = self._rng.uniform(-0.72, 0.72)
            return True
        return False

    def restart(self) -> None:
        self.score = 0
        self.player_x = self.player_y = 0.0
        self.star_x, self.star_y = 0.35, 0.2

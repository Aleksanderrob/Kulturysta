"""Built-in training exercise definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Exercise:
    key: str
    label: str
    target_pattern: str


EXERCISES = [
    Exercise("center", "Utrzymanie COP w centrum", "center"),
    Exercise("left_right", "Przeniesienie ciężaru lewo/prawo", "horizontal"),
    Exercise("front_back", "Przeniesienie ciężaru przód/tył", "vertical"),
    Exercise("targets", "Osiąganie kolejnych celów", "sequence"),
    Exercise("moving", "Podążanie za poruszającym się celem", "moving"),
    Exercise("symmetry", "Symetria obciążenia lewa/prawa", "center"),
    Exercise("limits", "Granice stabilności w bezpiecznym zakresie", "radial"),
]

"""COP geometry helpers."""

from __future__ import annotations

from app.constants import BOARD_LENGTH_M, BOARD_WIDTH_M


def cop_from_forces(
    top_left: float,
    top_right: float,
    bottom_left: float,
    bottom_right: float,
    width_m: float = BOARD_WIDTH_M,
    length_m: float = BOARD_LENGTH_M,
) -> tuple[float, float]:
    """Calculate physical COP (metres) from four non-negative corner loads."""
    forces = (top_left, top_right, bottom_left, bottom_right)
    if any(value < 0 for value in forces):
        raise ValueError("Obciążenia czujników nie mogą być ujemne.")
    total = sum(forces)
    if total <= 0:
        raise ValueError("Suma obciążeń musi być dodatnia.")
    left = top_left + bottom_left
    right = top_right + bottom_right
    top = top_left + top_right
    bottom = bottom_left + bottom_right
    return (right - left) / total * width_m / 2.0, (top - bottom) / total * length_m / 2.0


def normalized_cop_from_forces(
    top_left: float, top_right: float, bottom_left: float, bottom_right: float
) -> tuple[float, float]:
    total = top_left + top_right + bottom_left + bottom_right
    if total <= 0:
        raise ValueError("Suma obciążeń musi być dodatnia.")
    return ((top_right + bottom_right) - (top_left + bottom_left)) / total, (
        (top_left + top_right) - (bottom_left + bottom_right)
    ) / total

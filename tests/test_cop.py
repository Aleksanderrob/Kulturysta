import pytest

from analysis.cop import cop_from_forces, normalized_cop_from_forces
from app.constants import BOARD_LENGTH_M, BOARD_WIDTH_M


def test_equal_forces_are_centered():
    assert cop_from_forces(10, 10, 10, 10) == pytest.approx((0.0, 0.0))
    assert normalized_cop_from_forces(10, 10, 10, 10) == pytest.approx((0.0, 0.0))


@pytest.mark.parametrize(
    ("forces", "expected"),
    [
        ((0, 10, 0, 10), (BOARD_WIDTH_M / 2, 0.0)),
        ((10, 0, 10, 0), (-BOARD_WIDTH_M / 2, 0.0)),
        ((10, 10, 0, 0), (0.0, BOARD_LENGTH_M / 2)),
        ((0, 0, 10, 10), (0.0, -BOARD_LENGTH_M / 2)),
    ],
)
def test_known_directions(forces, expected):
    assert cop_from_forces(*forces) == pytest.approx(expected)


def test_invalid_forces_are_rejected():
    with pytest.raises(ValueError):
        cop_from_forces(0, 0, 0, 0)
    with pytest.raises(ValueError):
        cop_from_forces(-1, 2, 2, 2)

import pytest

from utils import points_in_2dcircle, pos_to_xyz


@pytest.mark.parametrize("position", [[1, 2, 3], ["1", "2", "3"]])
def test_pos_to_xyz(position):

    x, y, z = pos_to_xyz(position)

    assert x == 1
    assert y == 2
    assert z == 3


def test_points_in_2dcircle():
    points = points_in_2dcircle(radius=2)

    assert points == {
        (0, 1),
        (-1, -1),
        (0, 0),
        (-1, 1),
        (1, 1),
        (2, 0),
        (1, -1),
        (0, -2),
        (-1, 0),
        (-2, 0),
        (0, 2),
        (1, 0),
        (0, -1),
    }

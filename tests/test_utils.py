import pytest

from utils import pos_to_xyz


@pytest.mark.parametrize("position", [[1, 2, 3], ["1", "2", "3"]])
def test_pos_to_xyz(position):

    x, y, z = pos_to_xyz(position)

    assert x == 1
    assert y == 2
    assert z == 3

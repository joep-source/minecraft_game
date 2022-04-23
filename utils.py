from typing import List, Tuple

X = 0
Y = 1
Z = 2


def pos_to_xyz(position: List) -> Tuple[int, int, int]:
    return int(position[X]), int(position[Y]), int(position[Z])

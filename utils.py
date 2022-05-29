import logging
import time
from itertools import product
from typing import List, Set, Tuple

import conf

X = 0
Y = 1
Z = 2
Z_2D = 1

logger = logging.getLogger(conf.LOGGER_FILE_NAME)


def pos_to_xyz(position: List) -> Tuple[int, int, int]:
    return int(position[X]), int(position[Y]), int(position[Z])


def points_in_2dcircle(radius: int, x_offset: int = 0, y_offset: int = 0) -> Set[Tuple[int, int]]:
    all_points: Set = set()
    for x, y in product(range(radius + 1), repeat=2):
        if x**2 + y**2 <= radius**2:
            coords = (
                (x_offset + x, y_offset + y),
                (x_offset + x, y_offset - y),
                (x_offset - x, y_offset + y),
                (x_offset - x, y_offset - y),
            )
            all_points = all_points.union(coords)
    return all_points


def setup_logger(logger, level: int = logging.DEBUG):
    logger.setLevel(level)

    file_handler = logging.FileHandler(conf.LOGGER_FILE_NAME)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(conf.LOGGER_FORMAT)
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_format = logging.Formatter(conf.LOGGER_FORMAT)
    stream_handler.setFormatter(stream_format)
    logger.addHandler(stream_handler)


def timeit(method):
    def timed(*args, **kw):
        time_start = time.time()
        result = method(*args, **kw)
        time_end = time.time()
        logger.debug(f"Function '{method.__name__}' executed in {time_end - time_start:.3f}s")
        return result

    return timed


setup_logger(logger)

import logging
import time
from typing import List, Tuple

import conf

X = 0
Y = 1
Z = 2

logger = logging.getLogger(conf.LOGGER_FILE_NAME)


def pos_to_xyz(position: List) -> Tuple[int, int, int]:
    return int(position[X]), int(position[Y]), int(position[Z])


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
        time.sleep(1)
        return result

    return timed

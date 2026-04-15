import logging
import sys


def set_formatter():
    """设置formatter"""
    fmt = "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    return logging.Formatter(fmt, datefmt=datefmt)


def set_stream_handler():
    return logging.StreamHandler(sys.stdout)


def get_logger(name: str = "app", level=logging.DEBUG):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    formatter = set_formatter()
    handler = set_stream_handler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(level)

    return logger


logger = get_logger()
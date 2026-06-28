# from .log import get_logger, logger
from .log_v2 import AppLogger


logger = AppLogger().get_logger()

__all__ = ["logger"]

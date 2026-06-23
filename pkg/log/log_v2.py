import sys

from loguru import logger

from pkg.config import cfg


class AppLogger:
    _initialized = False
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._setup_logger()
        self._initialized = True

    def _setup_logger(self):
        logger.remove()

        log_dir = cfg.service_log_dir
        log_dir.mkdir(parents=True, exist_ok=True)

        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <6}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        if cfg.service_log_output in ("STDOUT", "BOTH"):
            logger.add(
                sys.stdout,
                format=console_format,
                level=cfg.service_log_level,
                colorize=cfg.service_log_colorize,
                backtrace=cfg.service_log_backtrace,
                diagnose=cfg.service_log_diagnose,
            )
        if cfg.service_log_output in ("FILE", "BOTH"):
            logger.add(
                log_dir / "app.log",
                serialize=True,
                level=cfg.service_log_level,
                retention=cfg.service_log_retention_days,
                compression="gz",
                enqueue=True,  # 异步队列，避免阻塞
                encoding="utf-8",
            )
        logger.info("Logger initialized.")

    def get_logger(self):
        return logger

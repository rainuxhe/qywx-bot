from pathlib import Path
from typing import Literal

from .base import BaseMixin


class ServiceMixin(BaseMixin):
    @property
    def service_host(self) -> str:
        return self._get_conf("service", "host", default="127.0.0.1")

    @property
    def service_port(self) -> int:
        return self._get_conf("service", "port", default=8000)

    @property
    def service_log_level(self) -> Literal["DEBUG", "INFO", "WARNING", "ERROR"]:
        """获取服务日志级别."""
        log_level = self._get_conf("service", "log", "level", default="info").upper()
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            log_level = "INFO"  # 默认级别为 INFO
        return log_level

    @property
    def service_log_dir(self) -> Path:
        """获取日志目录，始终返回基于项目根目录的 Path."""
        log_dir_str: str = self._get_conf("service", "log", "dir", default="logs")
        p = Path(log_dir_str)
        if not p.is_absolute():
            p = Path(__file__).parents[2] / log_dir_str
        return p

    @property
    def service_log_output(self) -> Literal["STDOUT", "FILE", "BOTH"]:
        """获取服务日志输出方式."""
        log_output = self._get_conf("service", "log", "output", default="stdout").upper()
        if log_output not in ("STDOUT", "FILE", "BOTH"):
            log_output = "STDOUT"  # 默认为 stdout 输出
        return log_output

    @property
    def service_log_retention_days(self) -> int:
        """获取日志轮转天数."""
        log_retention_days: int = self._get_conf("service", "log", "retention_days", default=7)
        if not isinstance(log_retention_days, int) or log_retention_days <= 0:
            log_retention_days = 7  # 默认为 7 天
        return log_retention_days

    @property
    def service_log_colorize(self) -> bool:
        log_colorize = self._get_conf("service", "log", "colorize", default=True)
        if not isinstance(log_colorize, bool):
            log_colorize = False  # 默认为 False
        return log_colorize

    @property
    def service_log_backtrace(self) -> bool:
        log_backtrace = self._get_conf("service", "log", "backtrace", default=True)
        if not isinstance(log_backtrace, bool):
            log_backtrace = True  # 默认为 True
        return log_backtrace

    @property
    def service_log_diagnose(self) -> bool:
        log_diagnose = self._get_conf("service", "log", "diagnose", default=True)
        if not isinstance(log_diagnose, bool):
            log_diagnose = True  # 默认为 True
        return log_diagnose

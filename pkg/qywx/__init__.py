"""This module will be deprecate, please use internal.qywx instead."""

from .qywx_client import QywxClient


qywx_client = QywxClient()

__all__ = ["qywx_client"]

from .base import BaseMixin


class QywxMixin(BaseMixin):
    @property
    def qywx_bot_id(self) -> str:
        return self._get_conf(f"qywx", "v2", "bot_id", default="")

    @property
    def qywx_secret(self) -> str:
        return self._get_conf(f"qywx", "v2", "secret", default="")

    @property
    def qywx_bot_name(self) -> str:
        return self._get_conf(f"qywx", "v2", "bot_name", default="")

    @property
    def qywx_wss_addr(self) -> str:
        return self._get_conf(f"qywx", "v2", "wss_addr", default="")

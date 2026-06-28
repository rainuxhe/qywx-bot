from pathlib import Path
import tomllib

from .agent_mixin import AgentMixin
from .postgres_mixin import PostgresMixin
from .qywx_mixin import QywxMixin
from .service_mixin import ServiceMixin
from .thirdparties_mixin import ThirdPartiesMixin


class Config(QywxMixin, ServiceMixin, AgentMixin, PostgresMixin, ThirdPartiesMixin):
    def __init__(self) -> None:
        self._config_file = Path(__file__).parent.parent.parent / "conf" / "config.toml"
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if self._config:
            return self._config

        try:
            with open(self._config_file, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}") from e

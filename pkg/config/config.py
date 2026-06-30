from pathlib import Path
import tomllib

from pydantic import BaseModel, ValidationError

from .agent import AgentConfig
from .postgres import DatabaseConfig
from .qywx import QywxConfig
from .service import ServiceConfig
from .thirdparties import ThirdPartiesConfig


class Config(BaseModel):
    service: ServiceConfig
    database: DatabaseConfig
    qywx: QywxConfig
    agent: AgentConfig
    thirdparties: ThirdPartiesConfig


def get_config() -> Config:
    """Get the global configuration instance."""
    config_file = Path(__file__).parent.parent.parent / "conf" / "config.toml"

    with open(config_file, "rb") as f:
        raw_config = tomllib.load(f)

    try:
        return Config.model_validate(raw_config)
    except ValidationError as e:
        raise RuntimeError(f"Failed to validate config: {e}") from e

from typing import Annotated

from pydantic import BaseModel, Field


class Dida365Config(BaseModel):
    enabled: Annotated[bool, Field(default=False, description="是否启用Dida365服务")]
    url: Annotated[str, Field(default="", description="Dida365 mcp url")]
    token: Annotated[str, Field(default="", description="Dida365 mcp token")]


class BochaConfig(BaseModel):
    enabled: Annotated[bool, Field(default=False, description="是否启用BoCha服务")]
    url: Annotated[str, Field(default="", description="BoCha url")]
    token: Annotated[str, Field(default="", description="BoCha token")]


class ThirdPartiesConfig(BaseModel):
    dida365: Dida365Config
    bocha: BochaConfig

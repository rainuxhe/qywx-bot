from typing import Annotated

from pydantic import BaseModel, Field


class QywxConfig(BaseModel):
    bot_id: Annotated[str, Field(..., description="企业微信机器人ID")]
    secret: Annotated[str, Field(..., description="企业微信机器人密钥")]
    bot_name: Annotated[str, Field(..., description="企业微信机器人名称")]
    wss_addr: Annotated[str, Field(..., description="企业微信WebSocket地址")]

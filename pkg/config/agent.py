from typing import Annotated

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    base_url: Annotated[str, Field(..., description="Agent base URL")]
    api_key: Annotated[str, Field(..., description="Agent API key")]
    model: Annotated[str, Field(..., description="Agent model name")]

from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import quote_plus

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool, tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from pydantic import Field, validate_call

from pkg.config import cfg


_PG_CHECKPOINTER: AsyncPostgresSaver = None  # type: ignore


# @validate_call
@lru_cache()
def get_llm(
    temperature: Annotated[float, Field(ge=0, le=1)] = 0.2,
    max_tokens: Annotated[int, Field(gt=0)] = 4096,
    reasoning_effort: Annotated[
        Literal["low", "medium", "high", "extreme"],
        Field(description="Reasoning effort level"),
    ] = "medium",
    model: Annotated[
        Literal["deepseek-v4-flash", "deepseek-v4-pro"],
        Field(description="LLM model to use"),
    ] = "deepseek-v4-flash",
) -> ChatAnthropic:
    return ChatAnthropic(
        model=model,  # type: ignore
        base_url=cfg.agent_base_url,
        api_key=cfg.agent_api_key,  # type: ignore
        temperature=temperature,
        max_tokens=max_tokens,  # type: ignore
        # streaming=True,
        # reasoning={"effort": "medium", "summary": "auto"},
        effort=reasoning_effort,
    )


class MCPServers:
    def __init__(self):
        # self._client_didatick: MultiServerMCPClient = None  # type: ignore
        # self._didatick_tools: list[BaseTool] = []
        self._client_composition: MultiServerMCPClient = None  # type: ignore
        self._composition_tools: list[BaseTool] = []

    async def _init_composition_mcp_tools(self) -> None:
        if self._client_composition and self._composition_tools:
            return

        self._client_composition = MultiServerMCPClient(
            {
                "composition": {
                    "url": f"http://127.0.0.1:{cfg.service_port}/api/mcp/composition",
                    "transport": "streamable_http",
                }
            }
        )
        self._composition_tools = await self._client_composition.get_tools()

    async def get_composition_tools(self) -> list[BaseTool]:
        if not self._composition_tools:
            await self._init_composition_mcp_tools()

        return self._composition_tools

    # async def _init_aididatick_mcp(self) -> None:
    #     if self._client_didatick and self._didatick_tools:
    #         return

    #     self._client_didatick = MultiServerMCPClient(
    #         {
    #             "didatick": {
    #                 "transport": "streamable_http",
    #                 "url": cfg.thirdparties_dida365_url,
    #                 "headers": {
    #                     "Authorization": f"Bearer {cfg.thirdparties_dida365_token}",
    #                 },
    #             }
    #         }
    #     )
    #     self._didatick_tools = await self._client_didatick.get_tools()

    # async def get_didatick_tools(self) -> list[BaseTool]:
    #     if not self._didatick_tools:
    #         await self._init_aididatick_mcp()
    #     return self._didatick_tools


async def init_checkpointer(pg_pool: AsyncConnectionPool, is_setup: bool = False) -> None:
    global _PG_CHECKPOINTER
    if not _PG_CHECKPOINTER:
        _PG_CHECKPOINTER = AsyncPostgresSaver(conn=pg_pool)

    if is_setup:
        conn_string = f"postgresql://{quote_plus(cfg.postgres_user)}:{quote_plus(cfg.postgres_password)}@{cfg.postgres_host}:{cfg.postgres_port}/{cfg.postgres_dbname}"
        async with AsyncPostgresSaver.from_conn_string(conn_string) as temp_saver:
            await temp_saver.setup()


async def get_checkpointer() -> AsyncPostgresSaver:
    global _PG_CHECKPOINTER
    if not _PG_CHECKPOINTER:
        pg_pool = await get_pg_pool()
        await init_checkpointer(pg_pool)
    return _PG_CHECKPOINTER

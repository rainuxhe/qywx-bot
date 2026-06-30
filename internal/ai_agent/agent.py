from pathlib import Path
from typing import List

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from langchain.agents.middleware import (
    ToolRetryMiddleware,
)
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from pkg.config import cfg
from pkg.exceptions.common import TimeoutException
from pkg.log import logger

from .common import MCPServers, get_checkpointer, get_llm
from .middlewares import ToolCallMiddleware


class AIAgent:
    _initialized = False
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._llm: ChatAnthropic = None  # type: ignore
        self._agent: CompiledStateGraph = None  # type: ignore
        self._tools: list[BaseTool] = []
        self._checkpointer: AsyncPostgresSaver = None  # type: ignore
        self._mcp_servers = MCPServers()
        self._sub_agents: List[SubAgent | CompiledSubAgent] = []

        self._initialized = True

    async def _init_deep_agent(self):
        if self._agent:
            return

        if not self._llm:
            self._llm = get_llm(model=cfg.agent.model)

        if not self._tools:
            await self._init_tools()

        checkpointer = await get_checkpointer()

        project_root_path = Path(__file__).parents[2]
        temp_dir = str((project_root_path / "temp").absolute())
        workspace_dir = str((project_root_path / "workspace").absolute())

        self._agent = create_deep_agent(
            model=self._llm,
            tools=self._tools,
            checkpointer=checkpointer,
            system_prompt=(
                f"你是一位名为{cfg.qywx.bot_name}的企业微信机器人, 请协助回答或处理用户的问题。回答的内容要准确、简洁。 语气风格要温和有礼、平易近人。"
            ),
            middleware=[
                ToolRetryMiddleware(
                    max_retries=2,
                    retry_on=(TimeoutException,),
                    on_failure="continue",
                ),
                # HumanInTheLoopMiddleware(
                #     interrupt_on={
                #         "execute_shell_command": {
                #             "allowed_decisions": ["approve", "reject"],
                #             "when": _interrupt_when_shell_command,  # type: ignore
                #         }
                #     }
                # ),
                ToolCallMiddleware(),
            ],
        )

    async def _init_tools(self) -> None:
        if self._tools:
            return

        mcp_tools = await self._mcp_servers.get_composition_tools()

        self._tools.extend(mcp_tools)

    async def _init_sub_agents(self) -> None:
        # TODO
        pass

    def _extract_message(self, message: object) -> str:
        if not message or not hasattr(message, "content"):
            return ""

        content = message.content  # type: ignore
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [
                block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
            ]
            return "".join(texts)
        return ""

    async def ainvoke(self, query: str, config: RunnableConfig) -> str:
        if not self._agent:
            await self._init_deep_agent()

        try:
            resp = await self._agent.ainvoke(
                input={"messages": [HumanMessage(content=query)]},
                config=config,
                version="v2",
            )
            return self._extract_message(resp.value["messages"][-1]) or "Sorry, sometimes life is a bit unpredictable."
        except Exception as e:
            logger.error(f"调用智能体时出错: {e}", exc_info=True)
            return "抱歉，处理您的请求时出现了错误。"

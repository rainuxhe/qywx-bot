from pathlib import Path
from typing import Any, List

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ToolRetryMiddleware,
)
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.types import Command

from pkg.config import cfg
from pkg.exceptions.common import TimeoutException
from pkg.log import logger

from .common import MCPServers, get_checkpointer, get_llm
from .middlewares import ToolCallMiddleware
from .tools import agent_tools


# --- Human-in-the-Loop 辅助函数 ---

_APPROVE_KEYWORDS: frozenset[str] = frozenset(
    {"yes", "accept", "approve", "ok", "是", "允许", "同意", "批准", "确认", "好", "可以", "行", "y"}
)


def _parse_decision(query: str) -> str:
    """从用户消息中解析决策类型。"""
    return "approve" if query.strip().lower() in _APPROVE_KEYWORDS else "reject"


def _build_resume_command(decision_type: str, actions_count: int) -> Command:
    """构建恢复执行的 Command。"""
    item: dict[str, str] = {"type": decision_type}
    if decision_type == "reject":
        item["message"] = "User rejected this action"
    return Command(resume={"decisions": [item for _ in range(actions_count)]})


def _format_interrupt_question(interrupt: Any) -> str:  # noqa: ANN401
    """将中断数据格式化为用户可读的审批提示。"""
    action_requests = interrupt.value.get("action_requests", [])
    review_configs = interrupt.value.get("review_configs", [])
    allowed = (
        review_configs[0].get("allowed_decisions", ["approve", "reject"]) if review_configs else ["approve", "reject"]
    )

    lines: list[str] = []
    for req in action_requests:
        lines.append(f"Do you approve me to execute this action?\n\n- name: {req['name']}\n- args: `{req['args']}`\n")
    lines.append(f"Input your decision: {', '.join(allowed)}")
    return "\n".join(lines)


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
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "execute_shell_command": {
                            "allowed_decisions": ["approve", "reject"],
                        }
                    }
                ),
                ToolRetryMiddleware(
                    max_retries=2,
                    retry_on=(TimeoutException,),
                    on_failure="continue",
                ),
                ToolCallMiddleware(),
            ],
        )

    async def _init_tools(self) -> None:
        if self._tools:
            return

        mcp_tools = await self._mcp_servers.get_composition_tools()
        self._tools.extend(mcp_tools)
        self._tools.extend(agent_tools)

    async def _init_sub_agents(self) -> None:
        # TODO
        pass

    async def _has_pending_interrupt(self, config: RunnableConfig) -> bool:
        """检查当前会话是否有待处理的中断。"""
        state = await self._agent.aget_state(config)
        return bool(state.next)

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
            # 优先处理中断恢复
            if await self._has_pending_interrupt(config):
                state = await self._agent.aget_state(config)
                actions_count = len(state.interrupts[0].value["action_requests"])
                decision = _parse_decision(query)
                cmd = _build_resume_command(decision, actions_count)
                await self._agent.ainvoke(cmd, config=config, version="v2")
                # 恢复后取最新消息
                state = await self._agent.aget_state(config)
                if state.values and "messages" in state.values:
                    return (
                        self._extract_message(state.values["messages"][-1])
                        or "Sorry, sometimes life is a bit unpredictable."
                    )
                return "Oops, something went wrong."

            # 正常对话
            resp = await self._agent.ainvoke(
                input={"messages": [HumanMessage(content=query)]},
                config=config,
                version="v2",
            )
            # 检查是否产生中断
            if resp.interrupts:
                return _format_interrupt_question(resp.interrupts[0])
            return self._extract_message(resp.value["messages"][-1]) or "Sorry, sometimes life is a bit unpredictable."
        except Exception as e:
            logger.error(f"调用智能体时出错: {e}", exc_info=True)
            return "抱歉，处理您的请求时出现了错误。"

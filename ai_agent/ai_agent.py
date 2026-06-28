from uuid import uuid4

from deepagents import create_deep_agent

# from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from pkg.config import cfg
from pkg.log import logger

from .tools import agent_tools


class AIAgent:
    # logger = get_logger("ai_agent")
    def __init__(self):
        self.model: ChatAnthropic = None  # type: ignore
        self._mcp_server_url = f"http://127.0.0.1:{cfg.service_port}/api/mcp/composition"
        self._checkpointer_cm = None
        self._checkpointer = None
        self._store_cm = None
        self._store = None
        self._current_user_id: str | None = None
        self._send_message_callback = None
        self._tools: list[BaseTool] = []

    async def _load_tools(self) -> None:
        if self._tools:
            return

        mcp_client = MultiServerMCPClient(
            {
                "datetime": {
                    "url": f"http://127.0.0.1:{cfg.service_port}/api/mcp/composition",
                    "transport": "streamable_http",
                }
            }
        )
        mcp_tools = await mcp_client.get_tools()
        self._tools.extend(mcp_tools)
        self._tools.extend(agent_tools)

    def set_send_message_callback(self, callback):
        """设置发送消息的回调"""
        self._send_message_callback = callback
        init_confirmation_callback(callback)

    def set_current_user(self, user_id: str):
        """设置当前用户 ID"""
        self._current_user_id = user_id

    def _get_current_user(self) -> str | None:
        """获取当前用户 ID"""
        return self._current_user_id

    async def start(self):
        if not self.model:
            self.model = ChatAnthropic(
                model=cfg.agent_model,  # type: ignore
                base_url=cfg.agent_base_url,
                api_key=cfg.agent_api_key,
                temperature=0.2,
                max_tokens=4096,  # type: ignore
                effort="medium",
            )

        conn_string = cfg.get_postgres_dsn()
        logger.debug(f"Connecting to Postgres for checkpointer: {conn_string}")

        self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(conn_string)
        self._checkpointer = await self._checkpointer_cm.__aenter__()
        await self._checkpointer.setup()

        # self._store_cm = AsyncPostgresStore.from_conn_string(conn_string)  # 暂不用store
        # self._store = await self._store_cm.__aenter__()
        # await self._store.setup()

        logger.info("AIAgent started with Postgres checkpointer and store")

    async def shutdown(self):
        self.model = None  # type: ignore

        if self._checkpointer_cm is not None:
            try:
                await self._checkpointer_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error while closing checkpointer: {e}")

        # if self._store_cm is not None:
        #     try:
        #         await self._store_cm.__aexit__(None, None, None)
        #     except Exception as e:
        #         logger.warning(f"Error while closing store: {e}")

        self._checkpointer = None
        self._store = None
        self._checkpointer_cm = None
        self._store_cm = None

        logger.info("AIAgent resources have been cleaned up.")

    async def _create_root_agent(self, session: ClientSession):
        tools = await load_mcp_tools(session)
        # 添加 shell 工具
        shell_tool = create_shell_tool(self._get_current_user)
        tools.append(shell_tool)

        system_prompt = (
            f"你是一个企业微信机器人, 名字叫{cfg.qywx_bot_name}, 可以使用 tools 协助用户处理各种问题，并用温柔和善积极的语气回答问题。"
            "回答的格式应该符合markdown规范。"
            "tools 的调用注意以下几点:"
            "- 日期时间相关的tool名一般都带有'datetime'"
        )

        root_agent = create_deep_agent(
            model=self.model,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=self._checkpointer,
            store=self._store,
        )
        return root_agent

    async def astream(self, input: str, thread_id: str = ""):
        """WARN: 企业微信流式输出有问题, 暂不使用该方法"""
        if not thread_id:
            thread_id = str(uuid4())

        logger.debug(f"Connecting to mcp server: {self._mcp_server_url}, thread_id: {thread_id}")
        async with streamable_http_client(self._mcp_server_url) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()

                root_agent = await self._create_root_agent(session)

                async for chunk in root_agent.astream(
                    input={"messages": [HumanMessage(content=input)]},
                    config={"configurable": {"thread_id": thread_id}},
                ):
                    # 从 chunk 字典中提取 AIMessage 的 content
                    if isinstance(chunk, dict):
                        messages = chunk.get("model", {}).get("messages", [])
                        if not messages:
                            continue
                        for msg in messages:
                            if hasattr(msg, "content") and msg.content:
                                yield str(msg.content)
                    elif hasattr(chunk, "content"):
                        yield str(chunk.content)  # type: ignore
                    else:
                        yield str(chunk)

    async def ainvoke(self, input: str, thread_id: str = ""):
        if not thread_id:
            thread_id = str(uuid4())

        logger.debug(f"Connecting to mcp server: {self._mcp_server_url}, thread_id: {thread_id}")
        async with streamable_http_client(self._mcp_server_url) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()

                root_agent = await self._create_root_agent(session)
                resp = await root_agent.ainvoke(
                    input={"messages": [HumanMessage(content=input)]},
                    config={"configurable": {"thread_id": thread_id}},
                    version="v2",
                )
                # return resp["messages"][-1].content
                return self._extract_text(resp.value["messages"][-1]) or "Sorry, sometimes life is a bit unpredictable."

    def _extract_text(self, message) -> str:
        if not message or not hasattr(message, "content"):
            return ""
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [
                block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
            ]
            return "".join(texts)
        return ""

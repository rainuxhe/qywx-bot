from uuid import uuid4
from deepagents import create_deep_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from pkg.config import cfg
from pkg.log import get_logger
from .shell_tool import create_shell_tool, init_confirmation_callback, confirm_command


class AIAgent:
    logger = get_logger("ai_agent")
    def __init__(self):
        self.model: ChatOpenAI = None  # type: ignore
        self._mcp_server_url = f"http://127.0.0.1:{cfg.service_port}/mcp/"
        self._checkpointer_cm = None
        self._checkpointer = None
        self._store_cm = None
        self._store = None
        self._current_user_id: str | None = None
        self._send_message_callback = None

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
            self.model = ChatOpenAI(
                base_url=cfg.agent_base_url,
                api_key=cfg.agent_api_key,  # type: ignore
                model=cfg.agent_model,
            )

        conn_string = cfg.get_postgres_dsn()
        self.logger.debug(f"Connecting to Postgres for checkpointer: {conn_string}")

        self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(conn_string)
        self._checkpointer = await self._checkpointer_cm.__aenter__()
        await self._checkpointer.setup()

        self._store_cm = AsyncPostgresStore.from_conn_string(conn_string)
        self._store = await self._store_cm.__aenter__()
        await self._store.setup()

        self.logger.info("AIAgent started with Postgres checkpointer and store")

    async def shutdown(self):
        self.model = None  # type: ignore

        if self._checkpointer_cm is not None:
            try:
                await self._checkpointer_cm.__aexit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"Error while closing checkpointer: {e}")

        if self._store_cm is not None:
            try:
                await self._store_cm.__aexit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"Error while closing store: {e}")

        self._checkpointer = None
        self._store = None
        self._checkpointer_cm = None
        self._store_cm = None

        self.logger.info("AIAgent resources have been cleaned up.")

    async def _create_root_agent(self, session: ClientSession):
        tools = await load_mcp_tools(session)
        # 添加 shell 工具
        shell_tool = create_shell_tool(self._get_current_user)
        tools.append(shell_tool)
        root_agent = create_deep_agent(
            model=self.model,
            tools=tools,
            system_prompt=f"你是一个智能助手，名字叫{cfg.qywx_bot_name}, 可以协助用户处理各种问题，并用温和积极的语气回答问题。回答的格式应该符合markdown规范。你可以使用 execute_shell_command 工具来执行 shell 命令。危险命令需要用户确认才能执行。",
            checkpointer=self._checkpointer,
            store=self._store,
        )
        return root_agent

    async def astream(self, input: str, thread_id: str = ""):
        if not thread_id:
            thread_id = str(uuid4())

        self.logger.debug(f"Connecting to mcp server: {self._mcp_server_url}, thread_id: {thread_id}")
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

        self.logger.debug(f"Connecting to mcp server: {self._mcp_server_url}, thread_id: {thread_id}")
        async with streamable_http_client(self._mcp_server_url) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                await session.initialize()

                root_agent = await self._create_root_agent(session)
                resp = await root_agent.ainvoke(
                    input={"messages": [HumanMessage(content=input)]},
                    config={"configurable": {"thread_id": thread_id}},
                )
                return resp["messages"][-1].content
                
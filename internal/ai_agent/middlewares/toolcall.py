from collections.abc import Awaitable, Callable
from typing import Any, Callable

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from pkg.log import logger


class ToolCallMiddleware(AgentMiddleware):
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        logger.debug(f"Executing tool: {request.tool_call['name']} with args: {request.tool_call['args']}")
        try:
            result = handler(request)
            logger.debug(f"Tool '{request.tool_call['name']}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool: {e}", exc_info=True)
            raise e

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        logger.debug(
            f"Executing tool asynchronously: {request.tool_call['name']} with args: {request.tool_call['args']}"
        )
        try:
            result = await handler(request)
            logger.debug(f"Tool '{request.tool_call['name']}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool asynchronously: {e}", exc_info=True)
            raise e

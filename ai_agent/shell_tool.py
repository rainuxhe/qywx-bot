"""
Shell 命令执行工具，带 Human-in-the-loop 确认
"""
import asyncio
import re
import shlex
import subprocess
from typing import Awaitable, Callable, Dict, Optional, Tuple
from uuid import uuid4
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


# 危险命令模式 - 这些命令需要用户确认
DANGEROUS_PATTERNS = [
    r"^rm\s",
    r"\brm\s",
    r"^mv\s",
    r"\bmv\s",
    r"^cp\s",
    r"\bcp\s",
    r"^>\s*",
    r">>\s*",
    r"\bmkdir\s",
    r"\btouch\s",
    r"\bsed\s.*-i",
    r"\bchmod\s",
    r"\bchown\s",
    r"\bdd\s",
    r"\bmkfs\s",
    r"\bmount\s",
    r"\bumount\s",
    r"\bsystemctl\s+(start|stop|restart|reload|disable|enable)",
    r"\bservice\s+\w+\s+(start|stop|restart|reload)",
    r"\bkill\s",
    r"\bpkill\s",
    r"\bkillall\s",
    r":\(\)\{:\|:\&\};\:",
    r"\bshred\s",
    r"\bwget\s.*\|\s*bash",
    r"\bcurl\s.*\|\s*bash",
    r"\bgit\s+(push|reset|rebase|merge)",
    r"\bapt-get?\s+(install|remove|purge|upgrade|dist-upgrade)",
    r"\byum\s+(install|remove|update|upgrade)",
    r"\bpip\s+(uninstall|install)",
    r"\bnpm\s+(uninstall|install)",
]


# 等待确认的任务
pending_confirmations: Dict[str, asyncio.Future[bool]] = {}

# 发送确认消息的回调
_send_confirmation_callback: Optional[Callable[[str, str], Awaitable[None]]] = None


def init_confirmation_callback(callback: Callable[[str, str], Awaitable[None]]):
    """初始化发送确认消息的回调"""
    global _send_confirmation_callback
    _send_confirmation_callback = callback


async def confirm_command(confirmation_id: str, approved: bool):
    """处理用户的确认/拒绝"""
    future = pending_confirmations.pop(confirmation_id, None)
    if future and not future.done():
        future.set_result(approved)


def is_dangerous_command(cmd: str) -> Tuple[bool, str]:
    """检查命令是否危险

    Returns:
        (is_dangerous, reason)
    """
    cmd_lower = cmd.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True, f"命令匹配危险模式: {pattern}"
    return False, ""


async def execute_shell_command_internal(cmd: str) -> str:
    """执行 shell 命令（内部函数）"""
    try:
        args = shlex.split(cmd)
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        if stderr:
            output += "\n[stderr]\n" + stderr.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            output += f"\n[exit code: {proc.returncode}]"
        return output
    except Exception as e:
        return f"Error: {str(e)}"


class ShellCommandInput(BaseModel):
    command: str = Field(description="The shell command to execute")
    force: bool = Field(default=False, description="If true, skip confirmation (use with caution)")


async def execute_shell_command(command: str, force: bool = False, user_id: Optional[str] = None) -> str:
    """
    Execute a shell command. Dangerous commands require user confirmation.
    """
    dangerous, reason = is_dangerous_command(command)

    if dangerous and not force:
        if not _send_confirmation_callback or not user_id:
            return f"Error: Cannot request confirmation. {reason}\nCommand: {command}"

        # 创建确认 ID
        confirmation_id = str(uuid4())[:8]

        # 发送确认消息给用户
        confirm_msg = (
            f"⚠️ **危险操作确认**\n\n"
            f"命令: `{command}`\n"
            f"原因: {reason}\n\n"
            f"请确认是否执行此命令？\n"
            f"回复 `确认 {confirmation_id}` 或 `拒绝 {confirmation_id}`"
        )

        await _send_confirmation_callback(user_id, confirm_msg)

        # 等待用户确认
        future = asyncio.get_event_loop().create_future()
        pending_confirmations[confirmation_id] = future

        try:
            approved = await asyncio.wait_for(future, timeout=300)
            if not approved:
                return "命令已被用户拒绝。"
        except asyncio.TimeoutError:
            pending_confirmations.pop(confirmation_id, None)
            return "确认超时，命令未执行。"

    return await execute_shell_command_internal(command)


def create_shell_tool(user_id_getter: Callable[[], Optional[str]]) -> StructuredTool:
    """创建 shell 工具"""

    async def _tool_func(command: str, force: bool = False) -> str:
        user_id = user_id_getter()
        return await execute_shell_command(command, force, user_id)

    return StructuredTool(
        name="execute_shell_command",
        description="Execute a shell command. Dangerous commands (rm, mv, etc.) require user confirmation.",
        args_schema=ShellCommandInput,
        func=None,
        coroutine=_tool_func,
    )

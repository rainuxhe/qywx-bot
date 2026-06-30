import asyncio
from typing import Annotated

from langchain_core.tools import tool
from pydantic import Field

from pkg.log import logger


@tool
async def execute_shell_command(
    command: Annotated[str, Field(description="Shell command to execute")],
    readonly: Annotated[str, Field(description="Whether the command is read-only")],
    timeout: Annotated[
        int,
        Field(default=10, description="Command execution timeout in seconds"),
    ],
) -> str:
    """Execute shell command locally

    Returns:
        str, command execution result
    """
    logger.debug(f"Executing shell command: {command}, readonly: {readonly}, timeout: {timeout} seconds")
    if not command:
        return "command is empty"

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()
        if stdout_str:
            return f"Stdout: {stdout_str}"
        elif stderr_str:
            return f"Stderr: {stderr_str}"
        else:
            return "Command executed successfully with no output"
    except asyncio.TimeoutError:
        if proc and not proc.returncode:
            try:
                proc.terminate()
                await proc.wait()
            except:
                pass
        return f"Execute '{command}' timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Error executing shell command: {e}", exc_info=True)
        return f"Error executing command '{command}': {str(e)}"

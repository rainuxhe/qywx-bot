from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from datetime import datetime, timedelta
from typing import Literal

mcp = FastMCP(
    name="datetime_server",
    instructions="Utilize the tools to answer questions about date and time.",
    host="127.0.0.1",
    port=8000,
    streamable_http_path="/",
)

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_current_datetime() -> str:
    """Get the current date and time in ISO format."""
    return datetime.now().isoformat()

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def time_shift(base_time: str, is_sub: bool, unit: Literal["seconds", "minutes", "hours", "days", "weeks"], amount: int) -> str:
    """Shift a date and time by a specified amount.
    
    Args:
        base_time: The base date and time in ISO format.
        is_sub: Whether to subtract (True) or add (False) the time.
        unit: The unit of time to shift (seconds, minutes, hours, days, weeks).
        amount: The amount of time to shift.

    Returns:
        The shifted date and time in ISO format.
    """
    dt = datetime.fromisoformat(base_time)
    delta_args = {unit: amount}
    if is_sub:
        dt -= timedelta(**delta_args)
    else:
        dt += timedelta(**delta_args)
    return dt.isoformat()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
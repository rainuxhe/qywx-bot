from datetime import datetime, timedelta
from typing import Annotated, Literal, Set
from zoneinfo import ZoneInfo, available_timezones

from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field


mcp = FastMCP(
    name="datetime_server",
    instructions="A server for datetime related operations",
)
mcp.add_middleware(
    ErrorHandlingMiddleware(
        include_traceback=True,
        transform_errors=True,
    )
)


class BasicTimeInfo(BaseModel):
    dt: Annotated[str, Field(description="ISO format of the date-time string")]
    timestamp: Annotated[int, Field(description="Unix timestamp")]
    week: Annotated[int, Field(description="ISO 8601 week number")]
    weekday: Annotated[int, Field(description="ISO 8601 week day number")]


class DateTimeStamp(BaseModel):
    dt: Annotated[str, Field(description="ISO format of the date-time string")]
    ts: Annotated[int, Field(description="Unix timestamp")]
    ts_millis: Annotated[int, Field(description="Unix timestamp in milliseconds")]
    ts_micro: Annotated[int, Field(description="Unix timestamp in microseconds")]
    ts_nano: Annotated[int, Field(description="Unix timestamp in nanoseconds")]


class DatetimeDiff(BaseModel):
    seconds: Annotated[int, Field(description="Seconds difference")]
    # milliseconds: Annotated[int, Field(description="Milliseconds difference")]
    # microseconds: Annotated[int, Field(description="Microseconds difference")]
    # nanoseconds: Annotated[int, Field(description="Nanoseconds difference")]
    minutes: Annotated[int, Field(description="Minutes difference")]
    hours: Annotated[int, Field(description="Hours difference")]
    days: Annotated[int, Field(description="Days difference")]
    # months: Annotated[int, Field(description="Months difference")]
    # years: Annotated[int, Field(description="Years difference")]


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_time_info(
    dt_str: Annotated[
        str,
        Field(description="时间字符串, 格式: %Y-%m-%dT%H:%M:%S%z", default=""),
    ] = "",
) -> BasicTimeInfo:
    """根据输入的时间字符串获取基本时间信息。如果未提供时间字符串, 则默认使用当前北京时间"""
    if not dt_str:
        dt_t = datetime.now().astimezone(tz=ZoneInfo("Asia/Shanghai"))
    else:
        dt_t = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S%z")
    # return datetime.now(timezone.utc).astimezone(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    # now = datetime.now().astimezone(tz=ZoneInfo("UTC"))
    return BasicTimeInfo(
        dt=dt_t.strftime("%Y-%m-%dT%H:%M:%S%z"),
        timestamp=int(dt_t.timestamp()),
        week=dt_t.isocalendar().week,
        weekday=dt_t.isocalendar().weekday,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def timezone_convert(utc_datetime: str, target_timezone: str) -> str:
    """将UTC时间转换为指定时区的时间

    Args:
        utc_datetime: ISO格式的UTC时间字符串
        target_timezone: 目标时区，例如 "Asia/Shanghai"

    Returns:
        转换后的时间字符串, 格式为 ISO 8601，例如 "2024-01-01T08:00:00+08:00"
    """
    try:
        dt = datetime.fromisoformat(utc_datetime)
        tz = ZoneInfo(target_timezone)
        local_dt = dt.astimezone(tz)
        return local_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        return "Error converting time. Please ensure the input UTC datetime and target timezone format are correct."


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_timezones(
    filter_str: Annotated[str, Field(description="Filter string for timezones", default="")] = "",
) -> Set[str]:
    """List timezones that match the filter string.

    Returns:
        A set of timezones that match the filter string.
    """
    all_timezones = available_timezones()
    if filter_str:
        filtered_timezones = {tz for tz in all_timezones if filter_str.lower() in tz.lower()}
        return filtered_timezones
    return all_timezones


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def datetime_offset(
    utc_datetime: Annotated[str, Field(description="ISO格式的UTC时间字符串")],
    unit: Annotated[
        Literal["seconds", "minutes", "hours", "days", "weeks", "milliseconds"],
        Field(description="时间单位"),
    ] = "seconds",
    offset: Annotated[float, Field(description="偏移量，float，可以为负数")] = 0,
) -> str:
    """对UTC时间进行偏移计算

    Returns:
        计算后的时间字符串, 格式为 ISO 8601，例如 "2024-01-01T00:01:40+00:00"
    """
    try:
        dt = datetime.fromisoformat(utc_datetime)
        match unit:
            case "seconds":
                delta = timedelta(seconds=offset)
            case "minutes":
                delta = timedelta(minutes=offset)
            case "hours":
                delta = timedelta(hours=offset)
            case "days":
                delta = timedelta(days=offset)
            case "weeks":
                delta = timedelta(weeks=offset)
            case "milliseconds":
                delta = timedelta(milliseconds=offset)
            case _:
                return (
                    "Invalid time unit. Please use 'seconds', 'minutes', 'hours', 'days', 'weeks', or 'milliseconds'."
                )

        new_dt = dt + delta
        return new_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        return "Error calculating datetime offset. Please ensure the input UTC datetime format is correct and the offset is a valid integer."


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def timestamp_convert(dt_str: str) -> DateTimeStamp:
    """ISO格式的日期时间字符串与Unix时间戳互相转换

    Args:
        dt_str: str, ISO格式的日期时间字符串 "%Y-%m-%dT%H:%M:%S%z", 或者Unix时间戳(秒,毫秒,微秒,纳秒)
    """
    if dt_str.isdigit():
        if len(dt_str) == 10:  # second
            dt_t = datetime.fromtimestamp(int(dt_str))
        elif len(dt_str) == 13:  # millisecond
            dt_t = datetime.fromtimestamp(int(dt_str) / 1000)
        elif len(dt_str) == 16:  # microsecond
            dt_t = datetime.fromtimestamp(int(dt_str) / 1e6)
        elif len(dt_str) == 19:  # nanosecond
            dt_t = datetime.fromtimestamp(int(dt_str) / 1e9)
    else:
        try:
            dt_t = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError as e:
            raise ValueError(f"Invalid ISO format datetime string: {dt_str}") from e

    return DateTimeStamp(
        dt=dt_t.strftime("%Y-%m-%dT%H:%M:%S%z"),
        ts=int(dt_t.timestamp()),
        ts_millis=int(dt_t.timestamp() * 1000),
        ts_micro=int(dt_t.timestamp() * 1e6),
        ts_nano=int(dt_t.timestamp() * 1e9),
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def datetime_diff(dt_str1: str, dt_str2: str) -> DatetimeDiff:
    """计算两个ISO格式日期时间字符串的时间差

    Args:
        dt_str1: str, ISO格式的日期时间字符串 "%Y-%m-%dT%H:%M:%S%z"
        dt_str2: str, ISO格式的日期时间字符串 "%Y-%m-%dT%H:%M:%S%z"
    """
    dt1 = datetime.strptime(dt_str1, "%Y-%m-%dT%H:%M:%S%z")
    dt2 = datetime.strptime(dt_str2, "%Y-%m-%dT%H:%M:%S%z")
    return DatetimeDiff(
        seconds=int((dt1 - dt2).total_seconds()),
        minutes=int((dt1 - dt2).total_seconds() / 60),
        hours=int((dt1 - dt2).total_seconds() / 3600),
        days=int((dt1 - dt2).total_seconds() / 86400),
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=30010)

from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.transforms.search import RegexSearchTransform

from pkg.log import logger

from .datatime_server import mcp as datetime_mcp_server
from .proxy_server import proxy as proxy_mcp_server


composition_mcp = FastMCP(
    name="composition_server",
    instructions="Combine multi mcp server into one server",
    transforms=[RegexSearchTransform()],
)

# Mount
composition_mcp.mount(datetime_mcp_server, namespace="datetime")
composition_mcp.mount(proxy_mcp_server)

composition_mcp.add_middleware(  # 1st in, last out
    ErrorHandlingMiddleware(
        include_traceback=True,
        transform_errors=True,
    )
)
composition_mcp.add_middleware(LoggingMiddleware(logger=logger, include_payloads=True))  # type: ignore

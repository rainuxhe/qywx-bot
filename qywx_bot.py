from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastmcp.utilities.lifespan import combine_lifespans
import uvicorn

# from ai_agent import aiops
# from internal.ai_agent import AIAgent
from internal.ai_agent.common import init_checkpointer
from internal.mcp_servers.composition_server import composition_mcp

# from ai_agent.mcp_servers.datetime_server import mcp as datetime_mcp
from internal.mcp_servers.datatime_server import mcp as datetime_mcp
from internal.qywx import qywx_client

# from pkg.qywx import qywx_client
from pkg.config import cfg
from pkg.database import get_pg_pool
from pkg.log import logger
from pkg.utils import http_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await aiops.start()
    try:
        pg_pool = await get_pg_pool()
        await init_checkpointer(pg_pool, is_setup=True)

        await qywx_client.start()

        yield
        await qywx_client.shutdown()
    finally:
        if http_client:
            await http_client.aclose()
        if pg_pool:
            await pg_pool.close()


def create_app() -> FastAPI:
    datetime_mcp_app = datetime_mcp.http_app(path="/")
    composition_mcp_app = composition_mcp.http_app(path="/")

    app = FastAPI(
        lifespan=combine_lifespans(
            lifespan,
            datetime_mcp_app.lifespan,
            composition_mcp_app.lifespan,
        )
    )
    app.mount("/api/mcp/datetime", datetime_mcp_app)
    app.mount("/api/mcp/composition", composition_mcp_app)  # endpoints: /api/mcp/composition/*

    return app


class LoguruHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的 loguru 级别
        level = logger.level(record.levelname).name
        # 转发消息，保留异常信息
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


app = create_app()


if __name__ == "__main__":
    for log_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        log = logging.getLogger(log_name)
        log.handlers = []  # 清除原有 handler
        log.addHandler(LoguruHandler())  # 添加 loguru 转发器
        log.propagate = False  # 关键：禁止向上传播，避免重复
    uvicorn.run("qywx_bot:app", host=cfg.service.host, port=cfg.service.port, log_config=None)

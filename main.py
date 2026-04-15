from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from pkg.qywx import qywx_client
from pkg.config import cfg
from ai_agent.mcp_servers.datetime_server import mcp as datetime_mcp
from ai_agent import aiops

@asynccontextmanager
async def lifespan(app: FastAPI):
    await aiops.start()
    await qywx_client.start()
    
    # 先获取 MCP app（这会创建 session_manager）
    mcp_app = datetime_mcp.streamable_http_app()
    
    # 在 FastAPI lifespan 中启动 MCP session manager
    async with datetime_mcp.session_manager.run():
        # 挂载 MCP app
        app.mount("/mcp", mcp_app)
        yield
    
    await aiops.shutdown()
    await qywx_client.shutdown()


app = FastAPI(
    lifespan=lifespan
)


if __name__ == "__main__":
    uvicorn.run("main:app", host=cfg.service_host, port=cfg.service_port)

from fastmcp.server import create_proxy

from pkg.config import cfg


config = {"mcpServers": {}}

if cfg.thirdparties.dida365.enabled:
    config["mcpServers"]["dida365"] = {  # type: ignore
        "url": cfg.thirdparties.dida365.url,
        "transport": "streamable-http",
        "headers": {
            "Authorization": f"Bearer {cfg.thirdparties.dida365.token}",
        },
    }

proxy = create_proxy(config)

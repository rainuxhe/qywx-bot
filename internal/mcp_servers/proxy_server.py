from fastmcp.server import create_proxy

from pkg.config import cfg


config = {"mcpServers": {}}

if cfg.thirdparties_dida365_enabled:
    config["mcpServers"]["dida365"] = {  # type: ignore
        "url": cfg.thirdparties_dida365_url,
        "transport": "streamable-http",
        "headers": {
            "Authorization": f"Bearer {cfg.thirdparties_dida365_token}",
        },
    }

proxy = create_proxy(config)

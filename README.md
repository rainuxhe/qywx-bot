# QYWX Bot 🤖

企业微信 AI 智能助手机器人，基于 **FastAPI + deepagents** 框架构建，通过企业微信 WebSocket 协议实时收发消息，结合大语言模型提供智能对话服务。

## 功能特性

- **企业微信接入** — 通过 WebSocket 协议连接企业微信，实时接收和处理消息
- **AI 智能对话** — 集成 deepagents 框架，支持多轮对话与会话状态持久化
- **MCP 工具扩展** — 基于 MCP（Model Context Protocol）标准协议扩展工具能力（如日期时间查询）
- **Shell 命令执行** — 支持在对话中执行 Shell 命令，危险命令需用户确认（Human-in-the-loop）
- **PostgreSQL 持久化** — 会话状态与记忆持久化存储，支持长对话上下文
- **流式输出** — 支持 AI 响应流式输出

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| AI Agent | deepagents + langchain-openai |
| LLM 接入 | OpenAI 兼容 API（支持火山引擎等） |
| 工具协议 | MCP（Model Context Protocol） |
| 企业微信 SDK | wecom-aibot-python-sdk |
| 会话存储 | PostgreSQL + langgraph-checkpoint-postgres |
| 项目工具 | uv / ruff / isort |

## 快速开始

### 前置要求

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip
- PostgreSQL 数据库（用于会话持久化）
- 企业微信机器人应用（已创建并获取凭证）
- LLM API 密钥（如火山引擎、OpenAI 等）

### 1. 克隆项目

```bash
git clone git@git.rainux.cn:AIAgent/qywx-bot.git
cd qywx-bot
```

### 2. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 3. 配置

```bash
cp conf/config.toml.example conf/config.toml
```

编辑 `conf/config.toml`，根据实际情况填写配置：

```toml
[service]
host = "127.0.0.1"
port = 8000
env = "dev"  # dev | prod

[agent]
base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"  # LLM API 地址
api_key = "your-api-key-here"                                   # API 密钥
model = "doubao-seed-2-0-lite-260215"                          # 模型名称

[qywx.v2]
bot_id = "your-bot-id-here"       # 企业微信机器人 ID
secret = "your-secret-here"       # 机器人密钥
bot_name = "智能助手"              # 机器人名称（会出现在 AI 的系统提示中）
wss_addr = "wss://openws.work.weixin.qq.com"  # WebSocket 地址

[database.postgres]
host = "127.0.0.1"
port = 5432
user = "your-db-user"
password = "your-db-password"
dbname = "your-db-name"
pool_max_size = 10
pool_min_size = 4
```

### 4. 运行

```bash
uv run python main.py
```

或：

```bash
python main.py
```

服务启动后会自动连接企业微信 WebSocket 服务，开始接收和处理消息。

## 项目结构

```
qywx-bot/
├── main.py                          # FastAPI 应用入口 & HTTP 服务启动
├── pyproject.toml                   # 项目元数据、依赖与代码风格配置
├── README.md
├── .python-version                  # Python 版本声明
├── uv.lock                          # uv 依赖锁定文件
├── conf/
│   └── config.toml.example          # 配置模板
├── ai_agent/
│   ├── __init__.py                  # 导出 AIAgent 单例
│   ├── ai_agent.py                  # AI Agent 核心：模型初始化、MCP 集成、对话流
│   ├── shell_tool.py                # Shell 命令执行工具（含危险命令确认机制）
│   └── mcp_servers/
│       └── datetime_server.py       # MCP 日期时间服务
└── pkg/
    ├── config/
    │   ├── __init__.py              # 导出全局配置对象 cfg
    │   ├── base.py                  # BaseMixin：配置属性基类
    │   ├── config.py                # Config：TOML 配置加载
    │   ├── agent_mixin.py           # AI Agent 相关配置属性
    │   ├── postgres_mixin.py        # PostgreSQL 连接配置 + DSN 生成
    │   ├── qywx_mixin.py            # 企业微信相关配置属性
    │   └── service_mixin.py         # 服务运行相关配置属性
    ├── log/
    │   ├── __init__.py              # 导出日志工具
    │   └── log.py                   # 日志配置与格式化输出
    └── qywx/
        ├── __init__.py              # 导出 QywxClient 单例
        └── qywx_client.py           # 企业微信 WebSocket 客户端，消息收发
```

## 配置详解

### 服务配置 `[service]`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `host` | `127.0.0.1` | 服务监听地址 |
| `port` | `8000` | 服务监听端口 |
| `env` | `dev` | 运行环境：`dev` / `prod` |

### Agent 配置 `[agent]`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `base_url` | — | LLM API 地址（OpenAI 兼容格式） |
| `api_key` | — | API 密钥 |
| `model` | — | 模型名称，如 `doubao-seed-2-0-lite-260215` |

### 企业微信配置 `[qywx.v2]`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `bot_id` | — | 企业微信机器人 Bot ID |
| `secret` | — | 机器人密钥 |
| `bot_name` | `智能助手` | 机器人名称，用于 AI 系统提示 |
| `wss_addr` | `wss://openws.work.weixin.qq.com` | WebSocket 连接地址 |

### 数据库配置 `[database.postgres]`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `host` | `127.0.0.1` | PostgreSQL 主机地址 |
| `port` | `5432` | PostgreSQL 端口 |
| `user` | — | 数据库用户 |
| `password` | — | 数据库密码 |
| `dbname` | — | 数据库名称 |
| `pool_max_size` | `10` | 连接池最大连接数 |
| `pool_min_size` | `4` | 连接池最小连接数 |

## 开发指南

### 代码风格

项目使用 [ruff](https://docs.astral.sh/ruff/) 进行代码检查与格式化，使用 [isort](https://pycqa.github.io/isort/) 管理导入顺序。

```bash
# 代码检查
uv run ruff check .

# 代码格式化
uv run ruff format .

# 导入排序
uv run isort .
```

配置详情见 `pyproject.toml` 中的 `[tool.ruff]` 和 `[tool.isort]` 部分。

### 添加新的 MCP 工具

1. 在 `ai_agent/mcp_servers/` 下创建新的 MCP 服务器文件
2. 实现 MCP 工具函数
3. 在 `main.py` 的 `lifespan` 中挂载新的 MCP app
4. 在 `ai_agent.py` 的 `_create_root_agent` 中加载工具

### 数据库

项目使用 PostgreSQL 存储会话状态（checkpointer）和记忆数据（store），依赖 langgraph 的持久化机制。首次启动时会自动建表。

## License

MIT

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ServiceLogConfig(BaseModel):
    level: Annotated[Literal["DEBUG", "INFO", "WARNING", "ERROR"], Field(default="INFO", description="日志级别")]
    dir: Annotated[str, Field(default="logs", description="日志文件目录")]
    output: Annotated[Literal["STDOUT", "FILE", "BOTH"], Field(default="STDOUT", description="日志输出方式")]
    retention_days: Annotated[int, Field(default=7, gt=0, le=30, description="日志文件轮转天数")]
    colorize: Annotated[bool, Field(default=True, description="是否启用颜色日志输出")]
    backtrace: Annotated[bool, Field(default=True, description="是否启用堆栈跟踪日志输出")]
    diagnose: Annotated[bool, Field(default=True, description="是否启用诊断日志输出")]


class ServiceConfig(BaseModel):
    host: Annotated[str, Field(default="127.0.0.1", description="服务监听地址")]
    port: Annotated[int, Field(default=8080, description="服务监听端口")]
    env: Annotated[Literal["dev", "prod"], Field(default="dev", description="服务环境")]
    log: ServiceLogConfig

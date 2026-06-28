from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, TypedDict

from pkg.log import logger

from .base import ChatArgparser, ChatCommand


class CommandInfo(TypedDict):
    description: str
    cmdcls: type[ChatCommand]
    is_visible: bool


_loaded_chat_commands: Dict[str, CommandInfo] = {}


class HelpCommand(ChatCommand):
    """内置的帮助命令, 用于展示所有可用命令的帮助信息"""

    main_name: str = "/help"
    description: str = "Show help message for all commands"
    is_visible: bool = True

    def create_parser(self) -> ChatArgparser:
        """HelpCommand 不需要参数, 直接返回一个空的ChatArgparser实例"""
        return ChatArgparser(prog="help", description="Show help message for all commands")

    async def run(self) -> str:
        """执行帮助命令, 返回所有可用命令的帮助信息"""
        if not _loaded_chat_commands:
            load_chat_commands()

        help_message = "Available commands: Use '--help' to get each command usage\n\n"
        index = 1
        for main_name, info in _loaded_chat_commands.items():
            if info["is_visible"]:
                help_message += f"{index}. **{main_name}**: {info['description']}\n"
                index += 1
        return help_message


def load_chat_commands() -> Dict[str, CommandInfo]:
    """加载所有命令类"""
    if _loaded_chat_commands:
        return _loaded_chat_commands

    pkg_path = "internal.commands"
    pkg = importlib.import_module(pkg_path)
    logger.info(f"Loading chat commands from package: {pkg_path}")

    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        # 如果以后各个命令类比较复杂, 可以把命令类放在一个单独的模块中, 加载的时候只加载模块
        # 目前命令类比较简单, 就直接放在internal.cmd包下, 加载的时候直接加载模块中的类
        # if not ispkg:
        #     continue
        if ispkg:
            continue
        skipped_modules = {"base", "__init__"}
        if any(name.endswith(skiped) for skiped in skipped_modules):
            continue
        module = importlib.import_module(name)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, ChatCommand) and attr is not ChatCommand:
                main_name = getattr(attr, "main_name", None)
                description = getattr(attr, "description", None)
                is_enable = getattr(attr, "is_enable", False)
                is_visible = getattr(attr, "is_visible", True)
                if not main_name or not description:
                    continue
                if not is_enable:
                    continue
                main_name = main_name.strip()
                description = description.strip()
                if main_name.startswith("/") and main_name not in _loaded_chat_commands:
                    _loaded_chat_commands[main_name] = {
                        "description": description,
                        "cmdcls": attr,
                        "is_visible": is_visible,
                    }

    # 手动注册HelpCommand, 确保/help命令始终可用
    if "/help" not in _loaded_chat_commands:
        _loaded_chat_commands["/help"] = {
            "description": HelpCommand.description,
            "cmdcls": HelpCommand,
            "is_visible": True,
        }

    return _loaded_chat_commands

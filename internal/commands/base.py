import argparse
from abc import ABC, abstractmethod
from io import StringIO


class ChatArgparser(argparse.ArgumentParser):
    """自定义的ArgumentParser, 用于解析聊天命令的参数, 重写error和exit方法, 捕获解析错误并返回错误信息, 而不是直接退出程序"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_error_triggered = False
        self.error_message = ""
        self.help_text = ""

    def print_help(self, file=None):
        """重写print_help方法, 捕获帮助信息, 以便在解析错误时返回给用户"""
        help_buffer = StringIO()
        super().print_help(help_buffer)
        self.help_text = help_buffer.getvalue()

    def error(self, message):
        """重写ArgumentParser的error方法: 不退出进程, 捕获解析错误并记录错误信息"""
        self.parse_error_triggered = True
        self.error_message = message

        # 抛出异常后, 中断后续的参数解析流程
        raise argparse.ArgumentError(None, message)

    def exit(self, status=0, message=None):
        """重写ArgumentParser的exit方法: 不退出进程, 捕获退出调用并记录错误信息"""
        self.parse_error_triggered = True
        if self.help_text:
            self.error_message = f"Help requested:\n\n```shell\n{self.help_text}\n"
        elif message:
            self.error_message = message
        else:
            self.error_message = "Exit triggered without message"

        raise argparse.ArgumentError(None, self.error_message)


class ChatCommand(ABC):
    """聊天命令的抽象基类, 定义了命令的基本结构和接口"""
    def __init__(self, user_message: str):
        self.user_message = user_message

    @abstractmethod
    def create_parser(self) -> ChatArgparser:
        """创建并返回一个ChatArgparser实例, 定义命令的参数结构"""
        ...

    @abstractmethod
    async def run(self) -> str:
        """执行命令的异步方法, 返回命令执行结果"""
        ...
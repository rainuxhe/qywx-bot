import argparse
import shlex

from internal.commands.base import ChatArgparser, ChatCommand


class DemoCommand(ChatCommand):
    main_name: str = "/demo"
    description: str = "Demo command for testing"
    is_enable: bool = True
    is_visible: bool = True

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.arg_parser = self.create_parser()

    async def run(self) -> str:
        try:
            cmd_args = shlex.split(self.user_message)[1:]  # 去掉命令本身
        except ValueError as e:
            return f"shlex 参数解析错误: {str(e)}"

        try:
            parsed_args = self.arg_parser.parse_args(cmd_args)
            return f"Hello, {parsed_args.name}! You are {parsed_args.age} years old."
        except argparse.ArgumentError as e:
            error_msg = str(e)
            if self.arg_parser.help_text:
                return error_msg
            # if error_msg.startswith("Help requested:"):
            #     return error_msg
            return f"parser 参数解析错误: {str(e)}"

    def create_parser(self) -> ChatArgparser:
        parser = ChatArgparser(prog="demo", description=self.description)

        parser.add_argument(
            "--name",
            type=str,
            help="Name of the user",
        )
        parser.add_argument(
            "--age",
            type=int,
            help="Age of the user",
        )
        return parser
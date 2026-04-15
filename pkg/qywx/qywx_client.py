import re
from pkg.config import cfg
from pkg.log import get_logger
from aibot import WSClient, WSClientOptions, generate_req_id, WsFrameHeaders
from ai_agent import aiops
from ai_agent.shell_tool import confirm_command
import logging

class QywxClient:
    """企业微信客户端, 通过websockets连接企业微信服务器, 接收消息并处理"""
    logger = get_logger("qywx_client", logging.INFO)

    def __init__(self) -> None:
        self.ws_client: WSClient = None  # type: ignore

    async def _send_message_callback(self, user_id: str, text: str):
        """发送消息的回调函数，供 shell tool 使用"""
        await self.send_text_message(user_id, text)

    async def send_text_message(self, user_id: str, text: str):
        """主动发送文本消息给用户

        Args:
            user_id: 企业微信用户ID
            text: 消息内容
        """
        if not self.ws_client:
            raise RuntimeError("QywxClient not started, call start() first")

        await self.ws_client.send_message(user_id, {
            "msgtype": "text",
            "text": {"content": text},
        })

    async def _on_authenticated(self):
        """处理认证成功事件"""
        self.logger.info("Authenticated with Qywx server")

    async def _on_event_enter_chat(self, frame: WsFrameHeaders):
        """处理用户进入聊天事件"""
        self.logger.debug("Received event: enter_chat")
        await self.ws_client.reply_welcome(frame, {
            "msgtype": "text",
            "text": {"content": f"您好！我是智能助手{cfg.qywx_bot_name}，有什么可以帮您的吗？"},
        })

    async def _on_message_text(self, frame: WsFrameHeaders):
        """处理文本消息事件"""
        self.logger.debug("Received text message")
        msg_id = frame.get("body", {}).get("msgid", "")
        user_id = frame.get("body", {}).get("from", {}).get("userid", "")
        content = frame.get("body", {}).get("text", {}).get("content", "")
        self.logger.debug(f"Message content: {content}, from user: {user_id}, msg_id: {msg_id}")

        # 先设置当前用户
        aiops.set_current_user(user_id)

        # 检查是否是确认/拒绝消息
        confirm_match = re.match(r"^(确认|拒绝)\s+([a-zA-Z0-9]+)$", content.strip())
        if confirm_match:
            action, confirmation_id = confirm_match.groups()
            approved = (action == "确认")
            await confirm_command(confirmation_id, approved)
            response_msg = "已确认执行命令。" if approved else "已拒绝执行命令。"
            stream_id = generate_req_id('stream')
            await self.ws_client.reply_stream(frame, stream_id, response_msg, True)
            return

        # 正常处理 AI 消息
        stream_id = generate_req_id('stream')

        await self.ws_client.reply_stream(frame, stream_id, "小脑瓜努力思考中...", False)

        resp = await aiops.ainvoke(input=content, thread_id=msg_id)
        await self.ws_client.reply_stream(frame, stream_id, resp, True)

    async def start(self):
        self.logger.info("Starting QywxClient...")
        if not self.ws_client:
            self.ws_client = WSClient(
                WSClientOptions(
                    bot_id=cfg.qywx_bot_id,
                    secret=cfg.qywx_secret,
                    logger=self.logger,
                )
            )

        self.ws_client.on("authenticated", self._on_authenticated)
        self.ws_client.on("event.enter_chat", self._on_event_enter_chat)
        self.ws_client.on("message.text", self._on_message_text)

        await self.ws_client.connect()

        # 设置回调给 AI agent
        aiops.set_send_message_callback(self._send_message_callback)

    async def shutdown(self):
        self.logger.info("Shutting down QywxClient...")
        if self.ws_client and self.ws_client.is_connected:
            self.ws_client.disconnect()

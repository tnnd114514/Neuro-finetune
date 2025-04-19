"""
QQBot + 自定义类OpenAI API 智能聊天机器人
需安装依赖：pip install qqbot openai
"""

# ====================== 必须修改的配置 ======================
# QQ机器人配置（从QQ开放平台获取）
QQ_APP_ID = "102768510"      # 替换为你的AppID
QQ_BOT_TOKEN = "RhuD1K6WVkgBbYDpdReLcFwZmokJoyLH"    # 替换为机器人Token

# 自定义类OpenAI API配置
CUSTOM_API_KEY = "sk-lCsmD3pXeLBV7MbA9IkhY0vRbYEb6BJQlEiFU3JaHyoheeOB"  # 替换为服务商提供的API密钥
CUSTOM_API_URL = "https://api.chatanywhere.tech/v1"  # 替换为实际API端点
CUSTOM_MODEL = "gpt-3.5-turbo"    # 如deepseek-chat、glm-4等

# 代理配置（按需设置）
PROXY_URL = "http://127.0.0.1:7890"  # 国内访问需要代理则修改，否则设为None
# ===========================================================

from openai import OpenAI
import qqbot
from qqbot.core.util.yaml_util import YamlUtil
import asyncio

class CustomAIBot:
    def __init__(self):
        # 初始化QQ机器人
        self.token = qqbot.Token(QQ_APP_ID, QQ_BOT_TOKEN)
        self.message_api = qqbot.AsyncMessageAPI(self.token, False)
        
        # 配置自定义AI客户端
        self.ai_client = OpenAI(
            api_key=CUSTOM_API_KEY,
            base_url=CUSTOM_API_URL,  # 关键修改：指定自定义API端点
            http_client=httpx.Client(proxies=PROXY_URL) if PROXY_URL else None
        )

    async def _handle_message(self, event, message: qqbot.Message):
        """处理收到的QQ消息"""
        try:
            if message.author.id == self.token.get_app_id():
                return

            # 清理消息内容
            content = message.content.replace(f"<@!{self.token.get_app_id()}>", "").strip()
            
            if content:
                print(f"收到消息: {content}")
                
                # 调用自定义API
                response = self.ai_client.chat.completions.create(
                    model=CUSTOM_MODEL,
                    messages=[{"role": "user", "content": content}],
                    temperature=0.7
                )
                
                # 发送原始回复
                await self.message_api.post_message(
                    channel_id=message.channel_id,
                    content=response.choices[0].message.content,
                    msg_id=message.id
                )
                
        except Exception as e:
            error_msg = f"⚠️ 服务异常: {str(e)}"
            await self.message_api.post_message(
                channel_id=message.channel_id,
                content=error_msg,
                msg_id=message.id
            )

    def run(self):
        """启动机器人"""
        qqbot_handler = qqbot.Handler(
            qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, self._handle_message
        )
        qqbot.async_listen_events(self.token, False, qqbot_handler)

if __name__ == "__main__":
    bot = CustomAIBot()
    asyncio.get_event_loop().run_until_complete(bot.run())

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

# 网络代理配置（国内服务器需要）
PROXY_CONFIG = { "None"  # Clash默认端口，按实际修改
}
# ===========================================================

import httpx
from openai import OpenAI
from qq_botpy import Bot, AsyncMessageAPI
from qq_botpy.message import Message, MessageSetting
from qq_botpy.exception import ServerError

class CustomAIBot:
    def __init__(self):
        # 初始化QQ机器人
        self.bot = Bot(appid=QQ_APP_ID, token=QQ_BOT_TOKEN)
        
        # 配置自定义AI客户端
        self.ai_client = OpenAI(
            api_key=CUSTOM_API_KEY,
            base_url=CUSTOM_API_URL,
            http_client=httpx.Client(proxies=PROXY_CONFIG) if PROXY_CONFIG else None
        )
        
        # 注册消息处理器
        @self.bot.on_at_message
        async def message_handler(message: Message):
            await self._process_message(message)

    async def _process_message(self, message: Message):
        """处理@消息"""
        try:
            # 清理消息内容（移除@提及）
            clean_content = message.content.replace(f"<@!{self.bot.app_id}>", "").strip()
            
            if not clean_content:
                return
                
            print(f"[收到消息] {message.author.username}: {clean_content}")
            
            # 调用AI接口
            response = self.ai_client.chat.completions.create(
                model=CUSTOM_MODEL,
                messages=[{"role": "user", "content": clean_content}],
                temperature=0.7,
                max_tokens=1024
            )
            
            # 发送回复
            reply_content = response.choices.message.content
            await message.reply(
                content=reply_content,
                message_setting=MessageSetting(update_mention=False)
            )
            print(f"[已回复] {reply_content[:50]}...")  # 打印前50字符
            
        except ServerError as e:
            print(f"[QQ API错误] {str(e)}")
        except Exception as e:
            error_msg = f"⚠️ 服务异常: {str(e)}"
            await message.reply(content=error_msg)
            print(f"[系统错误] {str(e)}")

    def run(self):
        """启动机器人"""
        self.bot.run()

if __name__ == "__main__":
    bot_instance = CustomAIBot()
    bot_instance.run()
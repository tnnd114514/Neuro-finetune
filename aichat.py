# -*- coding: utf-8 -*-
import os
import asyncio
from openai import AsyncOpenAI
import json
import time
from typing import List, Dict

# ===================== 用户自定义配置区域 ===================== #
# 类OpenAI API配置（需自行申请）
OPENAI_CLASS_APIS = [
    {   # 千帆API示例
        "name": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "sk-2378af2a79be4903aa7dd861765086c7" 
        "model": "qwen-plus-latest"  # 明确指定模型 # 百度智能云获取
    },
    {   # DeepSeek示例
        "name": "deepseek",
        "base_url": "https://api.chatanywhere.tech/v1,
        "api_key": "sk-lCsmD3pXeLBV7MbA9IkhY0vRbYEb6BJQlEiFU3JaHyoheeOB"
        "model": "deepseek"
    }
]

# Ollama本地模型配置（无需密钥）
OLLAMA_MODELS = [
    {"name": "deepseek-r1:8b", "base_url": "http://121.43.148.249:11434"},
    {"name": "deepseek-r1:32b", "base_url": "http://123.114.208.42:11434"},
    {"name": "qwen:0.5b", "base_url": "http://222.95.140.221:11434"},
    {"name": "deepseek-r1:7b", "base_url": "http://122.96.100.79:11434"},
    {"name": "deepseek-r1:70b", "base_url": "http://183.61.5.17:11434"},
    {"name": "deepseek-r1:1.5b", "base_url": "http://125.122.34.216:11434"},
    {"name": "Qwen2.5-VL:7b", "base_url": "http://218.255.138.150:11434"},
    {"name": "cwchang/llama3-taide-lx-8b-chat-alpha1:latest", "base_url": "http://218.255.138.150:11434"},
    {"name": "deepseek-r1:7b", "base_url": "http://118.201.252.28:11434"},
    {"name": "qwen2.5:72b", "base_url": "http://91.219.165.104:11434"},
    {"name": "gemma3:27b", "base_url": "http://142.132.157.27:11434"},
    # 添加其他11个本地模型...
]

# 总结用OpenAI API配置
SUMMARY_API = {
    "base_url": "https://api.moonshot.cn/v1",  # 或替换为其他兼容API
    "api_key": "sk-iVZ3N2WBXyUGJLOLbJXgVbZbRcIwrNAXPKlUpZOF4IKrdzSB",
    "model": "moonshot-v1-128k"
    "timeout": 60  # 增大总结超时时间
}

# ============================================================ #

async def call_openai_api(client_config: Dict, prompt: str) -> Dict:
    """调用类OpenAI API服务（增强版）"""
    try:
        client = AsyncOpenAI(
            base_url=client_config["base_url"],
            api_key=client_config["api_key"],
            timeout=client_config.get("timeout", 30),
            http_client=AsyncHTTPClient(proxies=PROXY_SETTINGS)
        )
        response = await client.chat.completions.create(
            model=client_config["model"],  # 使用明确指定的模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return {
            "model": client_config["name"],
            "content": response.choices.message.content,
            "success": True
        }
    except Exception as e:
        return {"model": client_config["name"], "content": str(e), "success": False}

async def call_ollama_api(model_config: Dict, prompt: str) -> Dict:
    """调用本地/远程Ollama API（稳定性增强版）"""
    try:
        client = AsyncOpenAI(
            base_url=model_config["base_url"],
            timeout=60,
            http_client=AsyncHTTPClient(proxies=PROXY_SETTINGS)
        )
        response = await client.chat.completions.create(
            model=model_config["name"],  # 直接使用完整模型名
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return {
            "model": model_config["name"],
            "content": response.choices.message.content,
            "success": True
        }
    except Exception as e:
        return {"model": model_config["name"], "content": str(e), "success": False}

def format_responses(responses: List[Dict]) -> str:
    """格式化输出（添加错误标识）"""
    output = []
    for resp in responses:
        status = "✅" if resp["success"] else "❌"
        output.append(f"[{resp['model']}] {status}:")
        output.append(resp["content"] + "&#92;n")
    return "&#92;n".join(output)

async def main():
    user_question = input("请输入您的问题：")
    
    # 创建异步任务（添加10%随机延迟防止封禁）
    tasks = []
    for config in OPENAI_CLASS_APIS:
        tasks.append(call_openai_api(config, user_question))
        await asyncio.sleep(0.1)  # 添加调用间隔
    
    for config in OLLAMA_MODELS:
        tasks.append(call_ollama_api(config, user_question))
        await asyncio.sleep(0.1)
    
    # 执行调用并计时
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    print(f"&#92;n✅ 完成{len(results)}个API调用，耗时{time.time()-start_time:.2f}秒")
    
    # 生成汇总报告
    aggregated = format_responses(results)
    
    # 生成最终总结（添加重试机制）
    max_retries = 3
    final_summary = ""
    for attempt in range(max_retries):
        try:
            client = AsyncOpenAI(
                base_url=SUMMARY_API["base_url"],
                api_key=SUMMARY_API["api_key"],
                timeout=SUMMARY_API["timeout"],
                http_client=AsyncHTTPClient(proxies=PROXY_SETTINGS)
            )
            summary = await client.chat.completions.create(
                model=SUMMARY_API["model"],
                messages=[
                    {"role": "system", "content": "你是一个专业的内容分析师"},
                    {"role": "user", "content": f"问题：{user_question}&#92;n&#92;n模型输出：&#92;n{aggregated}&#92;n请总结主要观点（500字内）："}
                ],
                max_tokens=600,
                temperature=0.3
            )
            final_summary = summary.choices.message.content
            break
        except Exception as e:
            if attempt == max_retries - 1:
                final_summary = f"总结失败：{str(e)}"
            await asyncio.sleep(2 ** attempt)  # 指数退避
    
    # 格式化输出
    print("&#92;n" + "="*60)
    print(f"📝 最终总结（{len(final_summary)}字）")
    print("="*60)
    print(final_summary)
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
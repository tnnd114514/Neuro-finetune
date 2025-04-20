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
        "name": "qwen-plus-latest",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "sk-2378af2a79be4903aa7dd861765086c7"  # 百度智能云获取
    },
    {   # DeepSeek示例
        "name": "deepseek",
        "base_url": "https://api.chatanywhere.tech/v1,
        "api_key": "sk-lCsmD3pXeLBV7MbA9IkhY0vRbYEb6BJQlEiFU3JaHyoheeOB"
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
}
# ============================================================ #

async def call_openai_api(client_config: Dict, prompt: str) -> Dict:
    """调用类OpenAI API服务"""
    try:
        client = AsyncOpenAI(
            base_url=client_config["base_url"],
            api_key=client_config["api_key"],
            timeout=30
        )
        response = await client.chat.completions.create(
            model=client_config.get("model", "default"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return {
            "model": client_config["name"],
            "content": response.choices[0].message.content,
            "success": True
        }
    except Exception as e:
        return {"model": client_config["name"], "content": str(e), "success": False}

async def call_ollama_api(model_config: Dict, prompt: str) -> Dict:
    """调用本地Ollama API（无密钥版）"""
    try:
        client = AsyncOpenAI(base_url=model_config["base_url"], timeout=60)
        response = await client.chat.completions.create(
            model=model_config["name"].split('-')[0].lower(),  # 模型名称映射
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return {
            "model": model_config["name"],
            "content": response.choices[0].message.content,
            "success": True
        }
    except Exception as e:
        return {"model": model_config["name"], "content": str(e), "success": False}

def format_responses(responses: List[Dict]) -> str:
    """格式化所有模型输出"""
    output = []
    for resp in responses:
        output.append(f"[{resp['model']}]：")
        output.append(resp["content"] if resp["success"] else f"错误：{resp['content']}")
        output.append("&#92;n")  # 模型间空行分隔
    return "&#92;n".join(output)

async def main():
    user_question = input("请输入您的问题：")
    
    # 创建并行调用任务
    tasks = []
    for config in OPENAI_CLASS_APIS:
        tasks.append(call_openai_api(config, user_question))
    for config in OLLAMA_MODELS:
        tasks.append(call_ollama_api(config, user_question))
    
    # 并行执行所有API调用
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    print(f"&#92;n所有API调用完成，总耗时：{time.time()-start_time:.2f}秒")
    
    # 生成汇总文本
    aggregated = format_responses(results)
    
    # 生成最终总结
    summary_prompt = f"""原始问题：{user_question}&#92;n&#92;n以下是16个模型的回答：&#92;n{aggregated}&#92;n请用500字内总结主要观点，标注共识与分歧："""
    
    try:
        client = AsyncOpenAI(
            base_url=SUMMARY_API["base_url"],
            api_key=SUMMARY_API["api_key"]
        )
        summary = await client.chat.completions.create(
            model=SUMMARY_API["model"],
            messages=[
                {"role": "system", "content": "你是一个专业的内容分析师"},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )
        final_summary = summary.choices[0].message.content
    except Exception as e:
        final_summary = f"总结失败：{str(e)}"
    
    # 输出结果
    print("&#92;n" + "="*50)
    print(f"最终总结（{len(final_summary)}字）：")
    print("="*50)
    print(final_summary)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
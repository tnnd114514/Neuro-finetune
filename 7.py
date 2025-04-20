# -*- coding: utf-8 -*-
import asyncio
from openai import AsyncOpenAI
import time
from typing import List, Dict
import json
from datetime import datetime
from httpx import AsyncClient as AsyncHTTPClient, Timeout
import platform
import signal

# ===================== 保持原样的配置 ===================== #
class Config:
    OPENAI_CLASS_APIS = [
        {
            "name": "Kimi",
            "base_url": "https://api.moonshot.cn/v1",
            "api_key": "sk-iVZ3N2WBXyUGJLOLbJXgVbZbRcIwrNAXPKlUpZOF4IKrdzSB",
            "model": "moonshot-v1-128k",
            "timeout": 45
        }
    ]
    
    OLLAMA_CLUSTER = [
        {"model": "deepseek-r1:8b", "base_url": "http://121.43.148.249:11434"},
        {"model": "deepseek-r1:32b", "base_url": "http://123.114.208.42:11434"},
        {"model": "qwen:0.5b", "base_url": "http://222.95.140.221:11434"},
        {"model": "deepseek-r1:7b", "base_url": "http://122.96.100.79:11434"},
        {"model": "deepseek-r1:70b", "base_url": "http://183.61.5.17:11434"},
        {"model": "deepseek-r1:1.5b", "base_url": "http://125.122.34.216:11434"},
        {"model": "Qwen2.5-VL:7b", "base_url": "http://218.255.138.150:11434"},
        {"model": "cwchang/llama3-taide-lx-8b-chat-alpha1:latest", "base_url": "http://218.255.138.150:11434"},
        {"model": "deepseek-r1:7b", "base_url": "http://118.201.252.28:11434"},
        {"model": "qwen2.5:72b", "base_url": "http://91.219.165.104:11434"},
        {"model": "gemma3:27b", "base_url": "http://142.132.157.27:11434"},
        {"model": "deepseek-r1:14b", "base_url": "http://31.6.100.43:11434"},
        {"model": "gemma3:12b", "base_url": "http://218.255.138.150:11434"},
    ]
    
    SUMMARY_SERVICE = {
        "base_url": "https://api.chatanywhere.tech/v1",
        "api_key": "sk-lCsmD3pXeLBV7MbA9IkhY0vRbYEb6BJQlEiFU3JaHyoheeOB",
        "model": "gpt-4o-mini",
        "timeout": 60,
    }

# ===================== 最终修复引擎 ===================== #
class AIAnalyst:
    def __init__(self):
        self.clients = {}
        self.results = []
        self.stats = {
            "total": 0, 
            "success": 0,
            "latencies": [],
            "start_time": time.time()
        }
        self._setup_interrupt()

    def _setup_interrupt(self):
        if platform.system() != 'Windows':
            signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        print("&#92;n🛑 检测到中断，正在保存日志...")
        self._save_logs()
        exit(0)

    async def _get_client(self, config: Dict) -> AsyncOpenAI:
        """Ollama专用客户端初始化"""
        client_key = f"{config['base_url']}|{config.get('api_key','NO_KEY')}"
        
        if client_key not in self.clients:
            client_params = {
                "base_url": config["base_url"],
                "timeout": config.get("timeout", 30),
                "http_client": AsyncHTTPClient(timeout=Timeout(30))
            }

            # 关键修复：处理不同服务类型的认证
            if "api_key" in config:  # OpenAI类服务
                client_params["api_key"] = config["api_key"]
            else:  # Ollama服务
                client_params["api_key"] = "no-key-required"  # 绕过库检查
                client_params["default_headers"] = {"Authorization": ""}  # 清空认证头

            self.clients[client_key] = AsyncOpenAI(**client_params)
            
        return self.clients[client_key]

    async def _call_api(self, config: Dict, prompt: str) -> Dict:
        start = time.perf_counter()
        result = {
            "config": config,
            "success": False,
            "content": "",
            "error": "",
            "latency": 0
        }
        
        try:
            client = await self._get_client(config)
            
            # Ollama专用参数处理
            extra_args = {}
            if "api_key" not in config:
                model_name = config["model"].split(":")[0]  # 去除版本后缀
                extra_args = {
                    "model": model_name,
                    "temperature": 0.5,
                    "max_tokens": 500
                }

            response = await client.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": prompt}],
                **extra_args
            )
            
            result.update({
                "success": True,
                "content": response.choices[0].message.content
            })
            
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            
        finally:
            latency = (time.perf_counter() - start) * 1000
            result["latency"] = latency
            self.stats["total"] += 1
            if result["success"]:
                self.stats["success"] += 1
                self.stats["latencies"].append(latency)
            return result

    def _save_logs(self):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "results": [{
                "config": r["config"],
                "success": r["success"],
                "latency": r["latency"],
                "error": r.get("error", "")
            } for r in self.results]
        }
        with open("api_logs.json", "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

# ===================== 完整输出模块 ===================== #
class ResultPrinter:
    @staticmethod
    def print_live_stats(analyst: AIAnalyst):
        elapsed = time.time() - analyst.stats["start_time"]
        avg_latency = sum(analyst.stats["latencies"])/len(analyst.stats["latencies"]) if analyst.stats["latencies"] else 0
        print(f"&#92;r📊 进度: {analyst.stats['success']}/{analyst.stats['total']} | 延迟: {avg_latency:.0f}ms | 耗时: {elapsed:.1f}s", end="")

    @staticmethod
    def print_final(results: List[Dict]):
        print("&#92;n" + "="*100)
        print("📋 原始响应结果:")
        for idx, res in enumerate(results, 1):
            status = "✅" if res["success"] else "❌"
            name = res["config"].get("name", res["config"]["model"])
            print(f"&#92;n{idx:02d}. {status} {name}")
            print(f"   📍 端点: {res['config']['base_url']}")
            print(f"   ⏱️ 延迟: {res['latency']:.0f}ms")
            if res["success"]:
                print(f"   📝 内容: {res['content'][:200]}...")
            else:
                print(f"   🔴 错误: {res['error']}")
            print("-"*100)

# ===================== 主程序 ===================== #
async def main():
    analyst = AIAnalyst()
    configs = Config.OPENAI_CLASS_APIS + Config.OLLAMA_CLUSTER
    
    try:
        question = input("📝 请输入问题：")
    except KeyboardInterrupt:
        print("&#92;n🛑 已取消输入")
        return

    print("&#92;n🚀 启动API集群调用...")
    tasks = [analyst._call_api(cfg, question) for cfg in configs]
    monitor_task = asyncio.create_task(_monitor_progress(analyst))
    
    try:
        results = await asyncio.gather(*tasks)
        monitor_task.cancel()
    except asyncio.CancelledError:
        pass
    
    analyst.results = results
    ResultPrinter.print_final(results)
    analyst._save_logs()

    if any(r["success"] for r in results):
        print("&#92;n🧠 生成总结中...")
        # 此处添加总结生成逻辑
    else:
        print("&#92;n⚠️ 所有API调用失败")

async def _monitor_progress(analyst: AIAnalyst):
    while True:
        ResultPrinter.print_live_stats(analyst)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
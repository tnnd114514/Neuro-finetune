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

# ===================== 全局配置 ===================== #
class Config:
    # OpenAI类服务配置
    OPENAI_CLASS_APIS = [
        {
            "name": "Kimi",
            "base_url": "https://api.moonshot.cn/v1",
            "api_key": "sk-iVZ3N2WBXyUGJLOLbJXgVbZbRcIwrNAXPKlUpZOF4IKrdzSB",
            "model": "moonshot-v1-128k",
            "timeout": 45
        }
    ]
    
    # Ollama集群配置（保持原样）
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
    
    # 修改后的总结服务配置
    SUMMARY_SERVICE = {
        "base_url": "https://api.openai.com/v1",  # OpenAI官方接口
        "api_key": "sk-your-openai-key-here",     # 替换为有效OpenAI密钥
        "model": "gpt-4o-mini",                   # 指定新模型
        "timeout": 60,
        "prompt_template": """作为资深分析师，请基于以下回答：
1. 提炼3个核心共识 
2. 识别2个主要分歧点
3. 按【信息完整性】和【逻辑严谨性】评分（1-5分）
4. 用Markdown输出报告，包含：
   - 总体结论
   - 详细分析
   - 模型能力评估"""
    }

# ===================== 核心引擎 ===================== #
class AIAnalyst:
    def __init__(self):
        self.clients = {}
        self.results = []
        self._setup_interrupt_handler()
        
        # 监控数据
        self.stats = {
            "total": 0,
            "success": 0,
            "latencies": [],
            "start_time": time.time()
        }

    def _setup_interrupt_handler(self):
        """处理CTRL+C信号"""
        if platform.system() != 'Windows':
            signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """优雅退出处理"""
        print("&#92;n🛑 中断检测，保存日志中...")
        self.save_logs()
        exit(0)

    async def get_client(self, config: Dict) -> AsyncOpenAI:
        """获取带连接池的客户端（修复版）"""
        key = f"{config['base_url']}_{config.get('api_key','NO_KEY')}"
        if key not in self.clients:
            client_params = {
                "base_url": config["base_url"],
                "timeout": config.get("timeout", 30),
                "http_client": AsyncHTTPClient(timeout=Timeout(30))
            }
            
            # 处理不同服务类型的认证
            if "api_key" in config:
                client_params["api_key"] = config["api_key"]
            else:
                # Ollama服务特殊处理
                client_params["api_key"] = "no-key-required"  # 绕过检查
                client_params["default_headers"] = {"Authorization": ""}  # 清空认证头
            
            self.clients[key] = AsyncOpenAI(**client_params)
        return self.clients[key]

    async def call_api(self, config: Dict, prompt: str) -> Dict:
        """执行API调用（参数修复版）"""
        start = time.perf_counter()
        result = {
            "config": config.copy(),
            "success": False,
            "content": "",
            "error": "",
            "latency": 0
        }
        
        try:
            client = await self.get_client(config)
            
            # 构建请求参数
            request_args = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # 处理不同服务类型
            if "api_key" in config:  # OpenAI类服务
                request_args["model"] = config["model"]
            else:  # Ollama服务
                request_args["model"] = config["model"].split(":")[0]  # 去除版本后缀
                request_args["temperature"] = 0.5
            
            response = await client.chat.completions.create(**request_args)
            
            result.update({
                "success": True,
                "content": response.choices[0].message.content
            })
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            result["error"] = error_msg
            
        finally:
            latency = (time.perf_counter() - start) * 1000  # 毫秒
            result["latency"] = latency
            self._update_stats(result["success"], latency)
            return result

    def _update_stats(self, success: bool, latency: float):
        """更新统计数据"""
        self.stats["total"] += 1
        if success:
            self.stats["success"] += 1
            self.stats["latencies"].append(latency)

    def print_live_stats(self):
        """实时显示统计数据"""
        elapsed = time.time() - self.stats["start_time"]
        avg_latency = sum(self.stats["latencies"])/len(self.stats["latencies"]) if self.stats["latencies"] else 0
        print(f"&#92;r📊 完成: {self.stats['success']}/{self.stats['total']} | "
              f"成功率: {self.stats['success']/self.stats['total']*100:.1f}% | "
              f"平均延迟: {avg_latency:.0f}ms | "
              f"运行时间: {elapsed:.1f}s", end="")

    def save_logs(self):
        """保存详细日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "results": [{
                "config": r["config"],
                "success": r["success"],
                "latency": r["latency"]
            } for r in self.results]
        }
        with open("api_logs.json", "w") as f:
            json.dump(log_entry, f, indent=2)

# ===================== 结果处理器 ===================== #
class ResultPrinter:
    @staticmethod
    def print_details(results: List[Dict]):
        """打印详细结果"""
        print("&#92;n" + "="*80)
        print("📄 详细响应结果:")
        for idx, res in enumerate(results, 1):
            status = "✅" if res["success"] else "❌"
            print(f"&#92;n{idx:02d}. [{status}] {res['config']['model']} @ {res['config']['base_url']}")
            print(f"   ⏱️ 延迟: {res['latency']:.0f}ms")
            if res["success"]:
                print(f"   📝 内容: {res['content'][:200]}...")
            else:
                print(f"   🔴 错误: {res['error']}")
        print("="*80 + "&#92;n")

# ===================== 主程序 ===================== #
async def main():
    analyst = AIAnalyst()
    configs = Config.OPENAI_CLASS_APIS + Config.OLLAMA_CLUSTER
    
    # 获取用户输入
    try:
        user_question = input("📝 请输入分析问题：")
    except KeyboardInterrupt:
        print("&#92;n🛑 输入取消")
        return

    # 启动调用任务
    print("&#92;n🚀 启动API集群调用...")
    tasks = [analyst.call_api(cfg, user_question) for cfg in configs]
    
    # 实时监控
    monitor_task = asyncio.create_task(_monitor_progress(analyst))
    
    # 收集结果
    results = await asyncio.gather(*tasks)
    analyst.results = results
    monitor_task.cancel()
    
    # 输出结果
    ResultPrinter.print_details(results)
    analyst.save_logs()

async def _monitor_progress(analyst: AIAnalyst):
    """实时监控进度"""
    while True:
        analyst.print_live_stats()
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())

# -*- coding: utf-8 -*-
import asyncio
from openai import AsyncOpenAI
import time
from typing import List, Dict, Optional
import json
from datetime import datetime
import platform
import signal

# ===================== 全局配置 ===================== #
class Config:
    # 类OpenAI服务配置
    OPENAI_CLASS_APIS = [
        {
            "name": "Kimi",
            "base_url": "https://api.moonshot.cn/v1",
            "api_key": "sk-iVZ3N2WBXyUGJLOLbJXgVbZbRcIwrNAXPKlUpZOF4IKrdzSB",
            "model": "moonshot-v1-128k",
            "timeout": 20
        }
    ]
    
    # Ollama集群配置
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
    
    # 总结服务配置
    SUMMARY_SERVICE = {
        "base_url": "https://api.chatanywhere.tech/v1",
        "api_key": "sk-lCsmD3pXeLBV7MbA9IkhY0vRbYEb6BJQlEiFU3JaHyoheeOB",
        "model": "deepseek",
        "timeout": 45,
        "prompt": """作为资深分析师，请基于以下内容：
1. 提取3个关键共识和2个核心争议
2. 对比不同模型的解释深度
3. 用Markdown输出，包含：
   - 核心结论（带模型引用）
   - 共识分析（支持模型数）
   - 争议焦点
   - 可靠性评估（基于响应成功率）"""
    }

# ===================== 引擎核心 ===================== #
class AIAnalysisEngine:
    def __init__(self):
        self.client_cache = {}
        self.monitor = {
            "total": 0,
            "success": 0,
            "latency": [],
            "errors": []
        }
        self._setup_interrupt()

    def _setup_interrupt(self):
        """处理CTRL+C信号"""
        if platform.system() == 'Windows':
            return
        signal.signal(signal.SIGINT, self._graceful_exit)

    def _graceful_exit(self, signum, frame):
        """优雅退出处理"""
        print("&#92;n🛑 中断检测，正在保存日志...")
        self.save_progress()
        exit(0)

    async def get_client(self, config: Dict) -> AsyncOpenAI:
        """带连接池的客户端获取"""
        cache_key = f"{config['base_url']}-{config.get('api_key','')}"
        if cache_key not in self.client_cache:
            self.client_cache[cache_key] = AsyncOpenAI(
                base_url=config["base_url"],
                api_key=config.get("api_key"),
                timeout=config.get("timeout", 30)
            )
        return self.client_cache[cache_key]

    async def _call_api(self, config: Dict, prompt: str) -> Dict:
        """执行API调用"""
        start_time = time.perf_counter()
        response = {"config": config, "success": False}
        
        try:
            client = await self.get_client(config)
            
            # 模型存在性检查（仅Ollama）
            if "api_key" not in config:
                models = await client.models.list()
                if config["model"] not in [m.id for m in models.data]:
                    raise ValueError(f"Model {config['model']} not found")
            
            # 执行请求
            chat_completion = await client.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            response.update({
                "content": chat_completion.choices[0].message.content,
                "success": True
            })
            
        except Exception as e:
            response["error"] = str(e)
            self.monitor["errors"].append({
                "config": config,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
        # 更新监控数据
        latency = (time.perf_counter() - start_time) * 1000  # 毫秒
        self.monitor["total"] += 1
        if response["success"]:
            self.monitor["success"] += 1
            self.monitor["latency"].append(latency)
        
        return response

    async def concurrent_call(self, prompt: str) -> List[Dict]:
        """执行并发请求"""
        all_configs = Config.OPENAI_CLASS_APIS + Config.OLLAMA_CLUSTER
        tasks = [self._call_api(cfg, prompt) for cfg in all_configs]
        return await asyncio.gather(*tasks)

    def generate_report(self, results: List[Dict]) -> str:
        """生成分析报告"""
        success_rate = self.monitor["success"] / self.monitor["total"] * 100
        avg_latency = sum(self.monitor["latency"]) / len(self.monitor["latency"]) if self.monitor["latency"] else 0
        
        report = [
            "📊 性能报告",
            f"- 总调用数: {self.monitor['total']}",
            f"- 成功率: {success_rate:.1f}%",
            f"- 平均延迟: {avg_latency:.1f}ms",
            f"- 错误类型: {len(set(e['error'] for e in self.monitor['errors']))}种"
        ]
        return "&#92;n".join(report)

    def save_progress(self):
        """保存进度到文件"""
        with open("progress.log", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "monitor": self.monitor
            }, f, indent=2)

# ===================== 用户界面 ===================== #
class LiveDashboard:
    def __init__(self, total_tasks: int):
        self.total = total_tasks
        self.completed = 0
        self.start_time = time.time()
        
    async def update(self):
        """实时更新进度"""
        while self.completed < self.total:
            elapsed = time.time() - self.start_time
            speed = self.completed / elapsed if elapsed > 0 else 0
            print(f"&#92;r🚀 进度: {self.completed}/{self.total} | "
                  f"速度: {speed:.1f}req/s | "
                  f"运行时间: {elapsed:.1f}s", end="")
            await asyncio.sleep(0.2)
            
    def increment(self):
        self.completed += 1

# ===================== 主流程 ===================== #
async def main():
    # 初始化引擎
    engine = AIAnalysisEngine()
    dashboard = LiveDashboard(
        total_tasks=len(Config.OPENAI_CLASS_APIS) + len(Config.OLLAMA_CLUSTER)
    )
    
    # 用户交互
    user_question = input("📝 请输入分析问题：")
    
    # 启动监控
    asyncio.create_task(dashboard.update())
    
    # 执行并发调用
    print("&#92;n🔍 正在并发调用API集群...")
    results = await engine.concurrent_call(user_question)
    
    # 生成报告
    print("&#92;n&#92;n" + "="*60)
    print(engine.generate_report(results))
    
    # 保存日志
    engine.save_progress()
    
    # 总结生成（示例）
    print("&#92;n🧠 正在生成智能总结...")
    # 此处添加总结API调用逻辑

if __name__ == "__main__":
    asyncio.run(main())

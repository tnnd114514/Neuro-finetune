# -*- coding: utf-8 -*-
import asyncio
from openai import AsyncOpenAI
import time
from typing import List, Dict
import json
from datetime import datetime
from httpx import AsyncHTTPClient, Timeout
import platform
import signal

# =======================================================================
#                         全局配置区域 (需根据实际情况修改)
# =======================================================================
class Config:
    # 类OpenAI服务配置（千帆、DeepSeek等）
    OPENAI_CLASS_APIS = [
        {
            "name": "Kimi智能助手",
            "base_url": "https://api.moonshot.cn/v1",
            "api_key": "sk-iVZ3N2WBXyUGJLOLbJXgVbZbRcIwrNAXPKlUpZOF4IKrdzSB",
            "model": "moonshot-v1-128k",
            "timeout": 45
        },
        {
            "name": "DeepSeek通用版",
            "base_url": "https://api.chatanywhere.tech/v1",
            "api_key": "sk-lCsmD3pXeLBV7MbA9IkhY0vRbYEb6BJQlEiFU3JaHyoheeOB",
            "model": "deepseek-chat",
            "timeout": 30
        }
    ]
    
    # Ollama多服务器集群配置
    OLLAMA_CLUSTER = [
        {"model": "deepseek-r1:8b", "base_url": "http://121.43.148.249:11434"},
        {"model": "deepseek-r1:32b", "base_url": "http://123.114.208.42:11434"},
        {"model": "qwen:0.5b", "base_url": "http://222.95.140.221:11434"},
        {"model": "deepseek-r1:7b", "base_url": "http://122.96.100.79:11434"},
        {"model": "deepseek-r1:70b", "base_url": "http://183.61.5.17:11434"},
        {"model": "deepseek-r1:1.5b", "base_url": "http://125.122.34.216:11434"},
        {"model": "Qwen2.5-VL:7b", "base_url": "http://218.255.138.150:11434"},
        {"model": "llama3-taide-lx-8b-chat-alpha1", "base_url": "http://218.255.138.150:11434"},
        {"model": "deepseek-r1:7b", "base_url": "http://118.201.252.28:11434"},
        {"model": "qwen2.5:72b", "base_url": "http://91.219.165.104:11434"},
        {"model": "gemma3:27b", "base_url": "http://142.132.157.27:11434"},
        {"model": "deepseek-r1:14b", "base_url": "http://31.6.100.43:11434"},
        {"model": "gemma3:12b", "base_url": "http://218.255.138.150:11434"},
    ]
    
    # 总结生成服务配置
    SUMMARY_SERVICE = {
        "base_url": "https://api.moonshot.cn/v1",
        "api_key": "sk-iVZ3N2WBXyUGJLOLbJXgVbZbRcIwrNAXPKlUpZOF4IKrdzSB",
        "model": "moonshot-v1-128k",
        "timeout": 60,
        "prompt_template": """作为资深分析师，请基于以下内容：
1. 提取3个核心共识和2个主要分歧点
2. 对比不同模型的解释深度
3. 用Markdown格式输出报告，包含：
   - 核心结论（标注支持模型数量）
   - 共识分析
   - 争议焦点
   - 可靠性评估（基于响应成功率）"""
    }

# =======================================================================
#                           核心引擎实现
# =======================================================================
class AIAnalyst:
    def __init__(self):
        self.clients = {}  # 客户端连接池
        self.results = []  # 存储所有结果
        self._setup_interrupt_handler()
        
        # 性能监控指标
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies": [],
            "start_time": time.time()
        }

    def _setup_interrupt_handler(self):
        """注册信号处理器实现优雅退出"""
        if platform.system() != 'Windows':
            signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """处理CTRL+C信号"""
        print("&#92;n🛑 检测到中断信号，正在保存日志...")
        self._save_operation_logs()
        exit(0)

    async def _get_client(self, config: Dict) -> AsyncOpenAI:
        """获取或创建异步客户端实例"""
        client_key = f"{config['base_url']}|{config.get('api_key', 'no_key')}"
        
        if client_key not in self.clients:
            self.clients[client_key] = AsyncOpenAI(
                base_url=config["base_url"],
                api_key=config.get("api_key"),
                timeout=config.get("timeout", 30),
                http_client=AsyncHTTPClient(
                    timeout=Timeout(config.get("timeout", 30)),
                    limits=httpx.Limits(max_connections=100)
                )
            )
        return self.clients[client_key]

    async def _execute_api_request(self, config: Dict, prompt: str) -> Dict:
        """执行单个API请求"""
        start_time = time.perf_counter()
        result_template = {
            "config": config,
            "success": False,
            "content": "",
            "error": "",
            "latency_ms": 0
        }
        
        try:
            client = await self._get_client(config)
            
            # 对Ollama服务进行模型可用性检查
            if "api_key" not in config:
                available_models = await client.models.list()
                if config["model"] not in [m.id for m in available_models.data]:
                    raise ValueError(f"模型 {config['model']} 未找到")
            
            # 执行实际请求
            response = await client.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            result_template.update({
                "success": True,
                "content": response.choices[0].message.content
            })
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            result_template["error"] = error_msg
            self.stats["failed_requests"] += 1
        finally:
            # 更新性能指标
            latency = (time.perf_counter() - start_time) * 1000  # 转换为毫秒
            result_template["latency_ms"] = latency
            self.stats["total_requests"] += 1
            if result_template["success"]:
                self.stats["successful_requests"] += 1
                self.stats["latencies"].append(latency)
                
            return result_template

    def _save_operation_logs(self):
        """保存操作日志到文件"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": self.stats,
            "request_details": [{
                "config": r["config"],
                "success": r["success"],
                "latency": r["latency_ms"],
                "error": r.get("error", "")
            } for r in self.results]
        }
        with open("operation_logs.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    async def _generate_summary_report(self, prompt: str) -> str:
        """生成汇总报告"""
        try:
            summary_client = await self._get_client(Config.SUMMARY_SERVICE)
            response = await summary_client.chat.completions.create(
                model=Config.SUMMARY_SERVICE["model"],
                messages=[
                    {"role": "system", "content": Config.SUMMARY_SERVICE["prompt_template"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"总结生成失败: {str(e)}"

# =======================================================================
#                           用户界面模块
# =======================================================================
class ResultVisualizer:
    @staticmethod
    def display_realtime_progress(analyst: AIAnalyst):
        """实时显示调用进度"""
        elapsed = time.time() - analyst.stats["start_time"]
        avg_latency = sum(analyst.stats["latencies"])/len(analyst.stats["latencies"]) if analyst.stats["latencies"] else 0
        print(f"&#92;r📈 实时状态 | 成功: {analyst.stats['successful_requests']} 失败: {analyst.stats['failed_requests']} | "
              f"平均延迟: {avg_latency:.1f}ms | 运行时间: {elapsed:.1f}s", end="")

    @staticmethod
    def display_final_results(results: List[Dict]):
        """显示最终结果"""
        print("&#92;n" + "="*100)
        print("📋 详细响应结果:")
        for idx, res in enumerate(results, 1):
            status = "✅" if res["success"] else "❌"
            print(f"&#92;n{idx:02d}. [{status}] {res['config'].get('name', res['config']['model'])}")
            print(f"   📌 端点: {res['config']['base_url']}")
            print(f"   ⏱️ 延迟: {res['latency_ms']:.1f}ms")
            
            if res["success"]:
                print(f"   📝 内容: {res['content'][:250]}...")
            else:
                print(f"   🔴 错误: {res['error']}")
            print("-"*100)

# =======================================================================
#                           主程序入口
# =======================================================================
async def main():
    analyst = AIAnalyst()
    configs = Config.OPENAI_CLASS_APIS + Config.OLLAMA_CLUSTER
    
    try:
        # 获取用户输入
        user_prompt = input("📝 请输入您要分析的问题：")
    except KeyboardInterrupt:
        print("&#92;n🛑 用户取消输入")
        return

    # 启动异步监控任务
    monitor_task = asyncio.create_task(_monitor_progress(analyst))
    
    # 执行所有API调用
    print("&#92;n🚀 开始并发调用API集群...")
    tasks = [analyst._execute_api_request(cfg, user_prompt) for cfg in configs]
    results = await asyncio.gather(*tasks)
    analyst.results = results
    
    # 清理监控任务
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass

    # 显示结果
    ResultVisualizer.display_final_results(results)
    analyst._save_operation_logs()

    # 生成总结报告
    if any(res["success"] for res in results):
        print("&#92;n🧠 正在生成综合分析报告...")
        summary = await analyst._generate_summary_report(user_prompt)
        print("&#92;n" + "="*100)
        print(summary)
        print("="*100 + "&#92;n")
    else:
        print("&#92;n⚠️ 所有API调用失败，无法生成总结报告")

async def _monitor_progress(analyst: AIAnalyst):
    """实时监控任务"""
    while True:
        ResultVisualizer.display_realtime_progress(analyst)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())

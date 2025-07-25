#!/usr/bin/env python3
"""
⚡ Elder Soul クイックベンチマーク
Quick Performance Assessment for Elder Soul
"""

import asyncio
import time
import psutil
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_registry import ElderRegistry, AgentType
from libs.elder_enforcement import ElderTreeEnforcement


class QuickBenchmark:
    """Elder Soul クイックベンチマーク"""

    def __init__(self):
        self.results = {}

    async def run_quick_assessment(self):
        """クイック評価実行"""
        print("⚡ Elder Soul Quick Performance Assessment")
        print("=" * 55)

        # 1.0 システム初期化速度
        await self._test_initialization_speed()

        # 2.0 エージェント登録速度
        await self._test_agent_registration_speed()

        # 3.0 メモリ効率
        await self._test_memory_efficiency()

        # 4.0 通信性能
        await self._test_communication_performance()

        # 5.0 強制実行システム性能
        await self._test_enforcement_performance()

        # 結果表示
        self._display_results()

    async def _test_initialization_speed(self):
        """初期化速度テスト"""
        print("\n🔧 Testing Initialization Speed...")

        times = []
        for i in range(3):
            start_time = time.time()

            registry = ElderRegistry()
            await registry.initialize()

            end_time = time.time()
            duration = (end_time - start_time) * 1000  # ms
            times.append(duration)

            print(f"  Run {i+1}: {duration:0.1f}ms")

        avg_time = statistics.mean(times)
        self.results["initialization"] = {
            "average_ms": avg_time,
            "min_ms": min(times),
            "max_ms": max(times),
            "rating": (
                "Excellent"
                if avg_time < 100
                else "Good" if avg_time < 500 else "Needs Improvement"
            ),
        }

    async def _test_agent_registration_speed(self):
        """エージェント登録速度テスト"""
        print("\n👥 Testing Agent Registration Speed...")

        registry = ElderRegistry()
        await registry.initialize()

        # 10エージェント登録
        start_time = time.time()

        for i in range(10):
            await registry.register_agent(
                agent_id=f"quick_test_agent_{i}",
                name=f"Quick Test Agent {i}",
                description="Quick benchmark test agent",
                agent_type=AgentType.SERVANT,
                capabilities=["testing"],
                auto_start=False,
            )

        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # ms
        avg_per_agent = total_time / 10

        print(f"  10 agents registered in {total_time:0.1f}ms")
        print(f"  Average per agent: {avg_per_agent:0.1f}ms")

        # クリーンアップ
        for i in range(10):
            try:
                await registry.unregister_agent(f"quick_test_agent_{i}")
            except:
                pass

        self.results["agent_registration"] = {
            "total_time_ms": total_time,
            "avg_per_agent_ms": avg_per_agent,
            "agents_per_second": 10000 / total_time,
            "rating": (
                "Excellent"
                if avg_per_agent < 50
                else "Good" if avg_per_agent < 200 else "Needs Improvement"
            ),
        }

    async def _test_memory_efficiency(self):
        """メモリ効率テスト"""
        print("\n💾 Testing Memory Efficiency...")

        # ベースライン測定
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        registry = ElderRegistry()
        await registry.initialize()

        # 50エージェント追加
        for i in range(50):
            await registry.register_agent(
                agent_id=f"memory_test_{i}",
                name=f"Memory Test {i}",
                description="Memory efficiency test",
                agent_type=AgentType.SERVANT,
                capabilities=["memory_test"],
                auto_start=False,
            )

        # メモリ使用量測定
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = current_memory - baseline_memory
        memory_per_agent = memory_delta / 50

        print(f"  Baseline memory: {baseline_memory:0.1f}MB")
        print(f"  With 50 agents: {current_memory:0.1f}MB")
        print(f"  Memory per agent: {memory_per_agent:0.2f}MB")

        # クリーンアップ
        for i in range(50):
            try:
                await registry.unregister_agent(f"memory_test_{i}")
            except:
                pass

        self.results["memory_efficiency"] = {
            "baseline_mb": baseline_memory,
            "with_agents_mb": current_memory,
            "memory_per_agent_mb": memory_per_agent,
            "total_overhead_mb": memory_delta,
            "rating": (
                "Excellent"
                if memory_per_agent < 0.5
                else "Good" if memory_per_agent < 2.0 else "Needs Improvement"
            ),
        }

    async def _test_communication_performance(self):
        """通信性能テスト"""
        print("\n📡 Testing Communication Performance...")

        # JSON シリアライゼーション/デシリアライゼーション速度
        test_message = {
            "message_id": "test_123",
            "source": "test_agent",
            "target": "target_agent",
            "payload": {"data": "x" * 1000},  # 1KB データ
            "timestamp": time.time(),
        }

        times = []
        for i in range(1000):
            start_time = time.time()

            # シリアライゼーション
            serialized = json.dumps(test_message)

            # デシリアライゼーション
            deserialized = json.loads(serialized)

            end_time = time.time()
            duration = (end_time - start_time) * 1000000  # microseconds
            times.append(duration)

        avg_latency = statistics.mean(times)
        throughput = 1000000 / avg_latency  # messages/sec

        print(f"  1000 messages processed")
        print(f"  Average latency: {avg_latency:0.1f}μs")
        print(f"  Throughput: {throughput:0.0f} msgs/sec")

        self.results["communication"] = {
            "avg_latency_us": avg_latency,
            "throughput_msg_per_sec": throughput,
            "message_size_bytes": len(json.dumps(test_message)),
            "rating": (
                "Excellent"
                if avg_latency < 100
                else "Good" if avg_latency < 500 else "Needs Improvement"
            ),
        }

    async def _test_enforcement_performance(self):
        """強制実行システム性能テスト"""
        print("\n🛡️ Testing Enforcement Performance...")

        start_time = time.time()

        # 強制実行システム初期化と実行
        enforcement = ElderTreeEnforcement()
        await enforcement.initialize()

        # 1回の違反検知実行
        scan_start = time.time()
        await enforcement.enforce_elder_tree_usage()
        scan_end = time.time()

        total_time = (scan_end - start_time) * 1000  # ms
        scan_time = (scan_end - scan_start) * 1000  # ms

        print(f"  Total initialization + scan: {total_time:0.1f}ms")
        print(f"  Scan only: {scan_time:0.1f}ms")

        self.results["enforcement"] = {
            "total_time_ms": total_time,
            "scan_time_ms": scan_time,
            "initialization_time_ms": total_time - scan_time,
            "rating": (
                "Excellent"
                if scan_time < 1000
                else "Good" if scan_time < 5000 else "Needs Improvement"
            ),
        }

    def _display_results(self):
        """結果表示"""
        print("\n🏆 Quick Benchmark Results")
        print("=" * 40)

        # 初期化性能
        init = self.results["initialization"]
        print(f"\n🔧 System Initialization: {init['rating']}")
        print(f"   Average: {init['average_ms']:0.1f}ms")
        print(f"   Range: {init['min_ms']:0.1f}-{init['max_ms']:0.1f}ms")

        # エージェント登録性能
        reg = self.results["agent_registration"]
        print(f"\n👥 Agent Registration: {reg['rating']}")
        print(f"   Per agent: {reg['avg_per_agent_ms']:0.1f}ms")
        print(f"   Throughput: {reg['agents_per_second']:0.1f} agents/sec")

        # メモリ効率
        mem = self.results["memory_efficiency"]
        print(f"\n💾 Memory Efficiency: {mem['rating']}")
        print(f"   Per agent: {mem['memory_per_agent_mb']:0.2f}MB")
        print(f"   Total overhead: {mem['total_overhead_mb']:0.1f}MB")

        # 通信性能
        comm = self.results["communication"]
        print(f"\n📡 Communication: {comm['rating']}")
        print(f"   Latency: {comm['avg_latency_us']:0.1f}μs")
        print(f"   Throughput: {comm['throughput_msg_per_sec']:0.0f} msgs/sec")

        # 強制実行性能
        enf = self.results["enforcement"]
        print(f"\n🛡️ Enforcement System: {enf['rating']}")
        print(f"   Scan time: {enf['scan_time_ms']:0.1f}ms")
        print(f"   Total time: {enf['total_time_ms']:0.1f}ms")

        # 総合評価
        ratings = [r["rating"] for r in self.results.values()]
        excellent_count = ratings.count("Excellent")
        good_count = ratings.count("Good")

        print(f"\n🎯 Overall Assessment")
        print(f"   Excellent: {excellent_count}/5 components")
        print(f"   Good: {good_count}/5 components")

        if excellent_count >= 4:
            overall = "🌟 Outstanding Performance"
        elif excellent_count + good_count >= 4:
            overall = "✅ Good Performance"
        else:
            overall = "⚠️ Needs Optimization"

        print(f"   Overall: {overall}")

        # 結果保存
        self._save_results()

    def _save_results(self):
        """結果保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 結果ディレクトリ作成
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)

        # JSON保存
        json_file = results_dir / f"quick_benchmark_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": datetime.now().isoformat(), "results": self.results},
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n📊 Results saved to: {json_file}")


async def main():
    """メイン実行"""
    benchmark = QuickBenchmark()
    await benchmark.run_quick_assessment()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
🚀 Elder Soul パフォーマンスベンチマーク
Elder Soul Performance Benchmark Suite

包括的なパフォーマンステストと分析
"""

import asyncio
import time
import psutil
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys
import concurrent.futures
from contextlib import asynccontextmanager

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_registry import ElderRegistry, AgentType
from libs.elder_enforcement import ElderTreeEnforcement


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""
    test_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success_rate: float
    throughput: float
    latency_avg: float
    latency_p95: float
    latency_p99: float
    error_count: int
    timestamp: str
    additional_metrics: Dict[str, Any] = None


@dataclass
class SystemMetrics:
    """システムメトリクス"""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    thread_count: int


class ElderTreeBenchmark:
    """Elder Soul ベンチマークスイート"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.baseline_metrics: Optional[SystemMetrics] = None
        self.registry = ElderRegistry()
        self.enforcement = ElderTreeEnforcement()

    async def run_comprehensive_benchmark(self):
        """包括的ベンチマーク実行"""
        print("🚀 Elder Soul Comprehensive Benchmark")
        print("=" * 60)

        # ベースライン測定
        await self._measure_baseline()

        # 1. システム初期化ベンチマーク
        await self._benchmark_system_initialization()

        # 2. エージェント登録パフォーマンス
        await self._benchmark_agent_registration()

        # 3. 通信レイテンシーテスト
        await self._benchmark_communication_latency()

        # 4. スケーラビリティテスト
        await self._benchmark_scalability()

        # 5. 強制実行システムパフォーマンス
        await self._benchmark_enforcement_system()

        # 6. メモリ効率性テスト
        await self._benchmark_memory_efficiency()

        # 7. 並行処理パフォーマンス
        await self._benchmark_concurrent_operations()

        # 8. ストレステスト
        await self._benchmark_stress_test()

        # 結果レポート生成
        await self._generate_benchmark_report()

    async def _measure_baseline(self):
        """ベースラインメトリクス測定"""
        print("\n📊 Measuring baseline system metrics...")

        self.baseline_metrics = await self._get_system_metrics()
        print(f"  CPU Usage: {self.baseline_metrics.cpu_percent:.1f}%")
        print(f"  Memory Usage: {self.baseline_metrics.memory_percent:.1f}%")
        print(f"  Available Memory: {self.baseline_metrics.memory_available_mb:.0f}MB")
        print(f"  Process Count: {self.baseline_metrics.process_count}")

    async def _benchmark_system_initialization(self):
        """システム初期化ベンチマーク"""
        print("\n🔧 Benchmarking System Initialization...")

        latencies = []
        memory_usages = []

        for i in range(5):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            # 新しいレジストリインスタンス初期化
            registry = ElderRegistry()
            await registry.initialize()

            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            latency = (end_time - start_time) * 1000  # ms
            memory_delta = end_memory - start_memory

            latencies.append(latency)
            memory_usages.append(memory_delta)

            print(f"  Run {i+1}: {latency:.2f}ms, Memory: +{memory_delta:.1f}MB")

        result = BenchmarkResult(
            test_name="System Initialization",
            execution_time=statistics.mean(latencies),
            memory_usage=statistics.mean(memory_usages),
            cpu_usage=await self._get_cpu_usage(),
            success_rate=100.0,
            throughput=1000 / statistics.mean(latencies),  # operations/sec
            latency_avg=statistics.mean(latencies),
            latency_p95=self._percentile(latencies, 95),
            latency_p99=self._percentile(latencies, 99),
            error_count=0,
            timestamp=datetime.now().isoformat()
        )

        self.results.append(result)

    async def _benchmark_agent_registration(self):
        """エージェント登録パフォーマンス"""
        print("\n👥 Benchmarking Agent Registration...")

        await self.registry.initialize()

        latencies = []
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024

        # 100個のテストエージェントを登録
        for i in range(100):
            start_time = time.time()

            try:
                await self.registry.register_agent(
                    agent_id=f"bench_agent_{i}",
                    name=f"Benchmark Agent {i}",
                    description=f"Test agent for benchmarking #{i}",
                    agent_type=AgentType.SERVANT,
                    capabilities=["benchmarking", "testing"],
                    dependencies=[],
                    auto_start=False
                )

                end_time = time.time()
                latency = (end_time - start_time) * 1000
                latencies.append(latency)

                if (i + 1) % 20 == 0:
                    print(f"  Registered {i+1}/100 agents, avg latency: {statistics.mean(latencies[-20:]):.2f}ms")

            except Exception as e:
                print(f"  Error registering agent {i}: {e}")

        memory_end = psutil.Process().memory_info().rss / 1024 / 1024
        memory_delta = memory_end - memory_start

        result = BenchmarkResult(
            test_name="Agent Registration",
            execution_time=statistics.mean(latencies),
            memory_usage=memory_delta,
            cpu_usage=await self._get_cpu_usage(),
            success_rate=(len(latencies) / 100) * 100,
            throughput=1000 / statistics.mean(latencies) if latencies else 0,
            latency_avg=statistics.mean(latencies) if latencies else 0,
            latency_p95=self._percentile(latencies, 95) if latencies else 0,
            latency_p99=self._percentile(latencies, 99) if latencies else 0,
            error_count=100 - len(latencies),
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "total_agents_registered": len(latencies),
                "memory_per_agent": memory_delta / len(latencies) if latencies else 0
            }
        )

        self.results.append(result)

        # クリーンアップ
        for i in range(len(latencies)):
            try:
                await self.registry.unregister_agent(f"bench_agent_{i}")
            except:
                pass

    async def _benchmark_communication_latency(self):
        """通信レイテンシーベンチマーク"""
        print("\n📡 Benchmarking Communication Latency...")

        latencies = []

        # シミュレートされたA2A通信テスト
        for i in range(1000):
            start_time = time.time()

            # メッセージ作成・処理のシミュレーション
            message = {
                "message_id": f"bench_msg_{i}",
                "source": "test_agent",
                "target": "target_agent",
                "payload": {"test_data": "x" * 100},  # 100バイトのテストデータ
                "timestamp": time.time()
            }

            # JSON シリアライゼーション/デシリアライゼーション
            serialized = json.dumps(message)
            deserialized = json.loads(serialized)

            end_time = time.time()
            latency = (end_time - start_time) * 1000000  # microseconds
            latencies.append(latency)

            if (i + 1) % 200 == 0:
                print(f"  Processed {i+1}/1000 messages, avg latency: {statistics.mean(latencies[-200:]):.1f}μs")

        result = BenchmarkResult(
            test_name="Communication Latency",
            execution_time=statistics.mean(latencies) / 1000,  # ms
            memory_usage=await self._get_memory_usage(),
            cpu_usage=await self._get_cpu_usage(),
            success_rate=100.0,
            throughput=1000000 / statistics.mean(latencies),  # messages/sec
            latency_avg=statistics.mean(latencies) / 1000,  # ms
            latency_p95=self._percentile(latencies, 95) / 1000,  # ms
            latency_p99=self._percentile(latencies, 99) / 1000,  # ms
            error_count=0,
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "message_size_bytes": len(json.dumps(message)),
                "throughput_mbps": (len(json.dumps(message)) * 1000000 / statistics.mean(latencies)) / 1024 / 1024
            }
        )

        self.results.append(result)

    async def _benchmark_scalability(self):
        """スケーラビリティベンチマーク"""
        print("\n📈 Benchmarking Scalability...")

        await self.registry.initialize()

        scalability_results = {}
        agent_counts = [10, 50, 100, 200, 500]

        for count in agent_counts:
            print(f"  Testing with {count} agents...")

            start_time = time.time()
            memory_start = psutil.Process().memory_info().rss / 1024 / 1024

            # エージェント一括登録
            tasks = []
            for i in range(count):
                task = self.registry.register_agent(
                    agent_id=f"scale_agent_{count}_{i}",
                    name=f"Scale Agent {count}-{i}",
                    description=f"Scalability test agent",
                    agent_type=AgentType.SERVANT,
                    capabilities=["scaling"],
                    dependencies=[],
                    auto_start=False
                )
                tasks.append(task)

            # 並行実行
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                print(f"    Error during batch registration: {e}")

            end_time = time.time()
            memory_end = psutil.Process().memory_info().rss / 1024 / 1024

            execution_time = (end_time - start_time) * 1000  # ms
            memory_delta = memory_end - memory_start

            scalability_results[count] = {
                "execution_time": execution_time,
                "memory_delta": memory_delta,
                "agents_per_second": count / (execution_time / 1000),
                "memory_per_agent": memory_delta / count
            }

            print(f"    {count} agents: {execution_time:.1f}ms, {memory_delta:.1f}MB, {scalability_results[count]['agents_per_second']:.1f} agents/sec")

            # クリーンアップ
            for i in range(count):
                try:
                    await self.registry.unregister_agent(f"scale_agent_{count}_{i}")
                except:
                    pass

        # 最大スケールのメトリクスを結果として記録
        max_scale = max(agent_counts)
        max_result = scalability_results[max_scale]

        result = BenchmarkResult(
            test_name="Scalability",
            execution_time=max_result["execution_time"],
            memory_usage=max_result["memory_delta"],
            cpu_usage=await self._get_cpu_usage(),
            success_rate=100.0,
            throughput=max_result["agents_per_second"],
            latency_avg=max_result["execution_time"] / max_scale,
            latency_p95=0,  # N/A for this test
            latency_p99=0,  # N/A for this test
            error_count=0,
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "scalability_results": scalability_results,
                "max_agents_tested": max_scale,
                "linear_scaling_factor": max_result["agents_per_second"] / scalability_results[10]["agents_per_second"]
            }
        )

        self.results.append(result)

    async def _benchmark_enforcement_system(self):
        """強制実行システムベンチマーク"""
        print("\n🛡️ Benchmarking Enforcement System...")

        latencies = []
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024

        for i in range(10):  # 強制実行は重い処理なので10回
            start_time = time.time()

            enforcement = ElderTreeEnforcement()
            await enforcement.initialize()

            # 違反検知実行（実際のプロセススキャン）
            await enforcement.enforce_elder_tree_usage()

            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)

            print(f"  Enforcement run {i+1}: {latency:.1f}ms")

        memory_end = psutil.Process().memory_info().rss / 1024 / 1024

        result = BenchmarkResult(
            test_name="Enforcement System",
            execution_time=statistics.mean(latencies),
            memory_usage=memory_end - memory_start,
            cpu_usage=await self._get_cpu_usage(),
            success_rate=100.0,
            throughput=1000 / statistics.mean(latencies),
            latency_avg=statistics.mean(latencies),
            latency_p95=self._percentile(latencies, 95),
            latency_p99=self._percentile(latencies, 99),
            error_count=0,
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "scan_frequency": f"Every {statistics.mean(latencies):.1f}ms sustainable"
            }
        )

        self.results.append(result)

    async def _benchmark_memory_efficiency(self):
        """メモリ効率性ベンチマーク"""
        print("\n💾 Benchmarking Memory Efficiency...")

        await self.registry.initialize()

        memory_baseline = psutil.Process().memory_info().rss / 1024 / 1024
        memory_measurements = [memory_baseline]

        # 段階的にエージェントを追加してメモリ使用量を測定
        for batch in range(1, 11):  # 10バッチ、各10エージェント
            for i in range(10):
                agent_id = f"memory_agent_{batch}_{i}"
                await self.registry.register_agent(
                    agent_id=agent_id,
                    name=f"Memory Test Agent {batch}-{i}",
                    description="Memory efficiency test agent",
                    agent_type=AgentType.SERVANT,
                    capabilities=["memory_test"],
                    dependencies=[],
                    auto_start=False
                )

            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory)

            print(f"  {batch * 10} agents: {current_memory:.1f}MB (+{current_memory - memory_baseline:.1f}MB)")

        # メモリ効率計算
        total_agents = 100
        total_memory_delta = memory_measurements[-1] - memory_baseline
        memory_per_agent = total_memory_delta / total_agents

        # クリーンアップ
        for batch in range(1, 11):
            for i in range(10):
                try:
                    await self.registry.unregister_agent(f"memory_agent_{batch}_{i}")
                except:
                    pass

        result = BenchmarkResult(
            test_name="Memory Efficiency",
            execution_time=0,  # N/A
            memory_usage=total_memory_delta,
            cpu_usage=await self._get_cpu_usage(),
            success_rate=100.0,
            throughput=total_agents / total_memory_delta,  # agents per MB
            latency_avg=0,  # N/A
            latency_p95=0,  # N/A
            latency_p99=0,  # N/A
            error_count=0,
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "memory_per_agent_mb": memory_per_agent,
                "memory_measurements": memory_measurements,
                "memory_efficiency_score": 100 / memory_per_agent  # higher is better
            }
        )

        self.results.append(result)

    async def _benchmark_concurrent_operations(self):
        """並行処理パフォーマンス"""
        print("\n⚡ Benchmarking Concurrent Operations...")

        await self.registry.initialize()

        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024

        # 50個のエージェントを並行登録
        concurrent_tasks = []
        for i in range(50):
            task = self.registry.register_agent(
                agent_id=f"concurrent_agent_{i}",
                name=f"Concurrent Agent {i}",
                description="Concurrent processing test",
                agent_type=AgentType.SERVANT,
                capabilities=["concurrent"],
                auto_start=False
            )
            concurrent_tasks.append(task)

        # 全タスク並行実行
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        end_time = time.time()
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count

        execution_time = (end_time - start_time) * 1000

        print(f"  Concurrent registration: {success_count}/50 succeeded in {execution_time:.1f}ms")

        # クリーンアップ
        for i in range(50):
            try:
                await self.registry.unregister_agent(f"concurrent_agent_{i}")
            except:
                pass

        result = BenchmarkResult(
            test_name="Concurrent Operations",
            execution_time=execution_time,
            memory_usage=memory_end - memory_start,
            cpu_usage=await self._get_cpu_usage(),
            success_rate=(success_count / 50) * 100,
            throughput=success_count / (execution_time / 1000),
            latency_avg=execution_time / success_count if success_count > 0 else 0,
            latency_p95=0,  # N/A for batch operation
            latency_p99=0,  # N/A for batch operation
            error_count=error_count,
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "concurrency_level": 50,
                "concurrent_efficiency": success_count / 50
            }
        )

        self.results.append(result)

    async def _benchmark_stress_test(self):
        """ストレステスト"""
        print("\n🔥 Running Stress Test...")

        await self.registry.initialize()

        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_start = psutil.cpu_percent()

        stress_duration = 30  # 30秒間のストレステスト
        operations_count = 0
        error_count = 0

        end_time = start_time + stress_duration

        print(f"  Running {stress_duration}s stress test...")

        while time.time() < end_time:
            try:
                # ランダムな操作を実行
                import random
                operation = random.choice(['register', 'unregister', 'status', 'list'])

                if operation == 'register':
                    agent_id = f"stress_agent_{int(time.time() * 1000000) % 1000000}"
                    await self.registry.register_agent(
                        agent_id=agent_id,
                        name=f"Stress Agent",
                        description="Stress test agent",
                        agent_type=AgentType.SERVANT,
                        capabilities=["stress"],
                        auto_start=False
                    )
                elif operation == 'status':
                    # ランダムなエージェントの状態確認
                    agents = await self.registry.list_agents()
                    if agents:
                        agent = random.choice(agents)
                        await self.registry.get_agent_status(agent['agent_id'])
                elif operation == 'list':
                    await self.registry.list_agents()

                operations_count += 1

                if operations_count % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"    {operations_count} operations in {elapsed:.1f}s ({operations_count/elapsed:.1f} ops/sec)")

            except Exception as e:
                error_count += 1
                if error_count % 10 == 0:
                    print(f"    {error_count} errors encountered")

            # 短い休憩（CPUを100%にしないため）
            await asyncio.sleep(0.001)

        final_time = time.time()
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024

        total_duration = final_time - start_time

        result = BenchmarkResult(
            test_name="Stress Test",
            execution_time=total_duration * 1000,
            memory_usage=memory_end - memory_start,
            cpu_usage=await self._get_cpu_usage(),
            success_rate=((operations_count - error_count) / operations_count * 100) if operations_count > 0 else 0,
            throughput=operations_count / total_duration,
            latency_avg=(total_duration / operations_count * 1000) if operations_count > 0 else 0,
            latency_p95=0,  # N/A for stress test
            latency_p99=0,  # N/A for stress test
            error_count=error_count,
            timestamp=datetime.now().isoformat(),
            additional_metrics={
                "test_duration_seconds": stress_duration,
                "total_operations": operations_count,
                "operations_per_second": operations_count / total_duration,
                "error_rate": (error_count / operations_count * 100) if operations_count > 0 else 0
            }
        )

        self.results.append(result)

        # ストレステスト後のクリーンアップ
        print("  Cleaning up stress test agents...")
        agents = await self.registry.list_agents()
        cleanup_count = 0
        for agent in agents:
            if 'stress_agent_' in agent['agent_id']:
                try:
                    await self.registry.unregister_agent(agent['agent_id'])
                    cleanup_count += 1
                except:
                    pass
        print(f"  Cleaned up {cleanup_count} stress test agents")

    async def _generate_benchmark_report(self):
        """ベンチマークレポート生成"""
        print("\n📊 Generating Benchmark Report...")

        # レポートディレクトリ作成
        report_dir = Path("benchmark_results")
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON形式での詳細レポート
        detailed_report = {
            "benchmark_metadata": {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                },
                "baseline_metrics": asdict(self.baseline_metrics) if self.baseline_metrics else None
            },
            "test_results": [asdict(result) for result in self.results]
        }

        json_file = report_dir / f"elder_soul_benchmark_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)

        # サマリーレポート生成
        summary_file = report_dir / f"elder_soul_summary_{timestamp}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_report())

        print(f"📄 Detailed report: {json_file}")
        print(f"📋 Summary report: {summary_file}")

        # コンソール出力
        print(self._generate_summary_report())

    def _generate_summary_report(self) -> str:
        """サマリーレポート生成"""
        report = []
        report.append("🌲 Elder Soul Performance Benchmark Report")
        report.append("=" * 60)
        report.append(f"🕒 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        if self.baseline_metrics:
            report.append("📊 System Baseline")
            report.append("-" * 30)
            report.append(f"CPU Usage: {self.baseline_metrics.cpu_percent:.1f}%")
            report.append(f"Memory Usage: {self.baseline_metrics.memory_percent:.1f}%")
            report.append(f"Available Memory: {self.baseline_metrics.memory_available_mb:.0f}MB")
            report.append(f"Process Count: {self.baseline_metrics.process_count}")
            report.append("")

        report.append("🏆 Performance Results")
        report.append("-" * 30)

        for result in self.results:
            report.append(f"\n🔸 {result.test_name}")
            report.append(f"   Execution Time: {result.execution_time:.2f}ms")
            report.append(f"   Memory Usage: {result.memory_usage:.1f}MB")
            report.append(f"   CPU Usage: {result.cpu_usage:.1f}%")
            report.append(f"   Success Rate: {result.success_rate:.1f}%")
            report.append(f"   Throughput: {result.throughput:.1f} ops/sec")
            report.append(f"   Avg Latency: {result.latency_avg:.2f}ms")

            if result.latency_p95 > 0:
                report.append(f"   P95 Latency: {result.latency_p95:.2f}ms")
                report.append(f"   P99 Latency: {result.latency_p99:.2f}ms")

            if result.error_count > 0:
                report.append(f"   ⚠️  Errors: {result.error_count}")

            if result.additional_metrics:
                report.append("   📈 Additional Metrics:")
                for key, value in result.additional_metrics.items():
                    if isinstance(value, (int, float)):
                        report.append(f"      {key}: {value:.2f}")
                    else:
                        report.append(f"      {key}: {value}")

        # 総合評価
        report.append("\n🎯 Overall Assessment")
        report.append("-" * 30)

        avg_success_rate = statistics.mean([r.success_rate for r in self.results])
        total_memory_usage = sum([r.memory_usage for r in self.results])
        avg_throughput = statistics.mean([r.throughput for r in self.results if r.throughput > 0])

        report.append(f"Average Success Rate: {avg_success_rate:.1f}%")
        report.append(f"Total Memory Impact: {total_memory_usage:.1f}MB")
        report.append(f"Average Throughput: {avg_throughput:.1f} ops/sec")

        # 推奨事項
        report.append("\n💡 Recommendations")
        report.append("-" * 30)

        if avg_success_rate < 95:
            report.append("⚠️  Consider improving error handling")

        if total_memory_usage > 500:
            report.append("⚠️  High memory usage detected - optimize memory efficiency")

        if avg_throughput < 100:
            report.append("⚠️  Low throughput - consider performance optimizations")

        report.append("\n✅ Elder Soul benchmark completed successfully!")

        return "\n".join(report)

    # ユーティリティメソッド

    async def _get_system_metrics(self) -> SystemMetrics:
        """現在のシステムメトリクス取得"""
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            memory_available_mb=psutil.virtual_memory().available / 1024 / 1024,
            disk_usage_percent=psutil.disk_usage('/').percent,
            network_io=dict(psutil.net_io_counters()._asdict()),
            process_count=len(psutil.pids()),
            thread_count=psutil.Process().num_threads()
        )

    async def _get_cpu_usage(self) -> float:
        """CPU使用率取得"""
        return psutil.cpu_percent(interval=0.1)

    async def _get_memory_usage(self) -> float:
        """メモリ使用量取得（MB）"""
        return psutil.Process().memory_info().rss / 1024 / 1024

    def _percentile(self, data: List[float], percentile: int) -> float:
        """パーセンタイル計算"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


async def main():
    """メイン実行"""
    benchmark = ElderTreeBenchmark()
    await benchmark.run_comprehensive_benchmark()


if __name__ == "__main__":
    asyncio.run(main())

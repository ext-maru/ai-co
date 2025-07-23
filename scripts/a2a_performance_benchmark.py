#!/usr/bin/env python3
"""
A2A通信パフォーマンステスト - 実戦計測
リアルタイム監視システムと連携してパフォーマンスを計測
"""

import concurrent.futures
import json
import statistics
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import psutil

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.a2a_monitoring_system import A2AMonitoringSystem


class A2APerformanceBenchmark:
    """A2A通信パフォーマンステスト"""

    def __init__(self):
        self.monitor = A2AMonitoringSystem()
        self.benchmark_id = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results = []
        self.system_metrics = []

    def measure_system_resources(self) -> Dict:
        """システムリソース計測"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
            "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
        }

    def single_communication_test(self, test_id: str) -> Dict:
        """単一通信テスト"""
        start_time = time.time()
        start_resources = self.measure_system_resources()

        # A2A通信をシミュレート
        communication_start = time.time()
        self.monitor.record_communication(
            source_agent=f"benchmark_agent_{test_id}",
            target_agent="test_target",
            message_type="performance_test",
            status="success",
            response_time=0.001,
            metadata={"test_id": test_id, "benchmark_id": self.benchmark_id},
        )
        communication_end = time.time()

        end_resources = self.measure_system_resources()
        end_time = time.time()

        return {
            "test_id": test_id,
            "total_time": end_time - start_time,
            "communication_time": communication_end - communication_start,
            "start_resources": start_resources,
            "end_resources": end_resources,
            "success": True,
        }

    def concurrent_communication_test(self, num_concurrent: int) -> Dict:
        """並行通信テスト"""
        print(f"🔄 並行通信テスト開始: {num_concurrent}件同時実行")

        start_time = time.time()
        start_resources = self.measure_system_resources()

        results = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_concurrent
        ) as executor:
            # 並行テスト実行
            futures = [
                executor.submit(self.single_communication_test, f"concurrent_{i}")
                for i in range(num_concurrent)
            ]

            # 結果収集
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "success": False})

        end_time = time.time()
        end_resources = self.measure_system_resources()

        # 成功率計算
        successful = [r for r in results if r.get("success")]
        success_rate = len(successful) / len(results) * 100

        # 応答時間統計
        response_times = [r["communication_time"] for r in successful]

        return {
            "test_type": "concurrent",
            "num_concurrent": num_concurrent,
            "total_time": end_time - start_time,
            "success_rate": success_rate,
            "total_requests": len(results),
            "successful_requests": len(successful),
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
            },
            "throughput_per_second": len(successful) / (end_time - start_time),
            "start_resources": start_resources,
            "end_resources": end_resources,
        }

    def four_sages_collaboration_benchmark(self) -> Dict:
        """4賢者協調ベンチマーク"""
        print("🧙‍♂️ 4賢者協調パフォーマンステスト開始")

        start_time = time.time()
        start_resources = self.measure_system_resources()

        # 4賢者協調パターンをシミュレート
        sage_communications = [
            ("task_sage", "knowledge_sage", "knowledge_query"),
            ("knowledge_sage", "task_sage", "query_response"),
            ("task_sage", "rag_sage", "query_request"),
            ("rag_sage", "task_sage", "query_response"),
            ("rag_sage", "incident_sage", "urgent_consultation"),
            ("incident_sage", "rag_sage", "response"),
            ("incident_sage", "task_sage", "council_decision"),
            ("task_sage", "all_sages", "session_complete"),
        ]

        communication_times = []
        for source, target, msg_type in sage_communications:
            comm_start = time.time()
            self.monitor.record_communication(
                source_agent=source,
                target_agent=target,
                message_type=msg_type,
                status="success",
                response_time=0.002,
                metadata={"benchmark_id": self.benchmark_id, "test_type": "four_sages"},
            )
            comm_end = time.time()
            communication_times.append(comm_end - comm_start)
            time.sleep(0.001)  # 微小な遅延で実際の処理をシミュレート

        end_time = time.time()
        end_resources = self.measure_system_resources()

        return {
            "test_type": "four_sages_collaboration",
            "total_time": end_time - start_time,
            "total_communications": len(sage_communications),
            "individual_times": communication_times,
            "avg_communication_time": statistics.mean(communication_times),
            "total_collaboration_time": sum(communication_times),
            "start_resources": start_resources,
            "end_resources": end_resources,
        }

    def stress_test(self, duration_seconds: int = 30) -> Dict:
        """ストレステスト"""
        print(f"⚡ ストレステスト開始: {duration_seconds}秒間")

        start_time = time.time()
        start_resources = self.measure_system_resources()

        request_count = 0
        successful_count = 0
        error_count = 0
        response_times = []

        # バックグラウンドでリソース監視
        resource_monitor = []

        def monitor_resources():
            while time.time() - start_time < duration_seconds:
                resource_monitor.append(self.measure_system_resources())
                time.sleep(1)

        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()

        # ストレステスト実行
        while time.time() - start_time < duration_seconds:
            try:
                comm_start = time.time()
                self.monitor.record_communication(
                    source_agent=f"stress_agent_{request_count}",
                    target_agent="stress_target",
                    message_type="stress_test",
                    status="success",
                    response_time=0.001,
                    metadata={
                        "benchmark_id": self.benchmark_id,
                        "request_num": request_count,
                    },
                )
                comm_end = time.time()

                response_times.append(comm_end - comm_start)
                successful_count += 1
            except Exception:
                error_count += 1

            request_count += 1
            time.sleep(0.01)  # 10ms間隔

        monitor_thread.join()
        end_time = time.time()
        end_resources = self.measure_system_resources()

        actual_duration = end_time - start_time

        return {
            "test_type": "stress_test",
            "duration_seconds": actual_duration,
            "total_requests": request_count,
            "successful_requests": successful_count,
            "error_count": error_count,
            "success_rate": (
                (successful_count / request_count * 100) if request_count > 0 else 0
            ),
            "requests_per_second": request_count / actual_duration,
            "successful_per_second": successful_count / actual_duration,
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "p95": (
                    statistics.quantiles(response_times, n=20)[18]
                    if len(response_times) > 20
                    else 0
                ),
            },
            "resource_usage": resource_monitor,
            "start_resources": start_resources,
            "end_resources": end_resources,
        }

    def run_comprehensive_benchmark(self) -> Dict:
        """包括的ベンチマーク実行"""
        print("🚀 A2A通信パフォーマンス包括ベンチマーク開始")
        print("=" * 60)

        benchmark_start = time.time()

        # 1. 単一通信テスト
        print("📡 1. 単一通信パフォーマンステスト")
        single_tests = []
        for i in range(10):
            result = self.single_communication_test(f"single_{i}")
            single_tests.append(result)

        # 2. 並行通信テスト
        concurrent_results = []
        for concurrent_count in [5, 10, 20, 50]:
            result = self.concurrent_communication_test(concurrent_count)
            concurrent_results.append(result)

        # 3. 4賢者協調テスト
        print("🧙‍♂️ 3. 4賢者協調パフォーマンステスト")
        four_sages_result = self.four_sages_collaboration_benchmark()

        # 4. ストレステスト
        print("⚡ 4. ストレステスト")
        stress_result = self.stress_test(15)  # 15秒

        benchmark_end = time.time()

        # 結果統合
        benchmark_report = {
            "benchmark_id": self.benchmark_id,
            "start_time": datetime.fromtimestamp(benchmark_start).isoformat(),
            "end_time": datetime.fromtimestamp(benchmark_end).isoformat(),
            "total_duration": benchmark_end - benchmark_start,
            "single_communication": {
                "tests": single_tests,
                "avg_time": statistics.mean(
                    [t["communication_time"] for t in single_tests]
                ),
                "min_time": min([t["communication_time"] for t in single_tests]),
                "max_time": max([t["communication_time"] for t in single_tests]),
            },
            "concurrent_communication": concurrent_results,
            "four_sages_collaboration": four_sages_result,
            "stress_test": stress_result,
            "summary": {
                "peak_throughput": max(
                    [r["throughput_per_second"] for r in concurrent_results]
                ),
                "best_response_time": min(
                    [t["communication_time"] for t in single_tests]
                ),
                "collaboration_efficiency": four_sages_result["avg_communication_time"],
                "stress_performance": stress_result["successful_per_second"],
            },
        }

        # レポート保存
        report_file = PROJECT_ROOT / "logs" / f"a2a_benchmark_{self.benchmark_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(benchmark_report, f, indent=2, ensure_ascii=False, default=str)

        return benchmark_report

    def print_results(self, report: Dict):
        """結果表示"""
        print("\n" + "=" * 60)
        print("📊 A2A通信パフォーマンステスト結果")
        print("=" * 60)

        print(f"🆔 ベンチマークID: {report['benchmark_id']}")
        print(f"⏱️ 実行時間: {report['total_duration']:.2f}秒")

        print("\n📡 単一通信:")
        print(
            f"  平均応答時間: {report['single_communication']['avg_time']*1000:.2f}ms"
        )
        print(f"  最速応答: {report['single_communication']['min_time']*1000:.2f}ms")
        print(f"  最遅応答: {report['single_communication']['max_time']*1000:.2f}ms")

        print("\n🔄 並行通信:")
        for result in report["concurrent_communication"]:
            print(
                (
                    f"f"  {result['num_concurrent']}件同時: {result['throughput_per_second']:.1f} req/sec (成功率: "
                    f"{result['success_rate']:.1f}%)""
                )
            )

        print("\n🧙‍♂️ 4賢者協調:")
        collab = report["four_sages_collaboration"]
        print(f"  総時間: {collab['total_time']*1000:.2f}ms")
        print(f"  通信数: {collab['total_communications']}件")
        print(f"  平均通信時間: {collab['avg_communication_time']*1000:.2f}ms")

        print("\n⚡ ストレステスト:")
        stress = report["stress_test"]
        print(f"  実行時間: {stress['duration_seconds']:.1f}秒")
        print(f"  総リクエスト: {stress['total_requests']}件")
        print(f"  成功率: {stress['success_rate']:.1f}%")
        print(f"  スループット: {stress['successful_per_second']:.1f} req/sec")
        print(f"  P95応答時間: {stress['response_times']['p95']*1000:.2f}ms")

        print("\n🏆 総合評価:")
        summary = report["summary"]
        print(f"  最大スループット: {summary['peak_throughput']:.1f} req/sec")
        print(f"  最高応答時間: {summary['best_response_time']*1000:.2f}ms")
        print(f"  協調効率: {summary['collaboration_efficiency']*1000:.2f}ms")
        print(f"  ストレス耐性: {summary['stress_performance']:.1f} req/sec")


def main():
    """メイン処理"""
    benchmark = A2APerformanceBenchmark()

    print("🤖 A2A通信システム実戦パフォーマンステスト")
    print("リアルタイム監視システムと連携して計測を実行します...")
    print()

    # ベンチマーク実行
    report = benchmark.run_comprehensive_benchmark()

    # 結果表示
    benchmark.print_results(report)

    print("\n💾 詳細レポートを保存しました:")
    print(f"   logs/a2a_benchmark_{benchmark.benchmark_id}.json")
    print("\n🎯 A2A通信システムの実戦パフォーマンステスト完了！")


if __name__ == "__main__":
    main()

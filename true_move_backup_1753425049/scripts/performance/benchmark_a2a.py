#!/usr/bin/env python3
"""
Auto Issue Processor A2A Performance Benchmarking System
Issue #192 Phase 1: プロファイリングとベースライン確立

パフォーマンス測定、ボトルネック特定、改善目標設定のためのベンチマークツール
"""

import asyncio
import json
import logging
import os
import psutil
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import cProfile
import pstats
import io
from contextlib import asynccontextmanager
import sys
from dataclasses import dataclass, asdict

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Auto Issue Processor import
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """パフォーマンス測定結果"""
    
    # 基本指標
    start_time: float
    end_time: float
    duration_seconds: float
    
    # 処理指標
    issues_processed: int
    issues_per_second: float
    concurrent_processes: int
    
    # リソース指標
    memory_start_mb: float
    memory_peak_mb: float
    memory_end_mb: float
    memory_delta_mb: float
    cpu_percent_avg: float
    cpu_percent_peak: float
    
    # I/O指標
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_received_mb: float
    
    # エラー指標
    errors_count: int
    retry_count: int
    timeout_count: int
    
    # 詳細タイミング
    avg_processing_time_per_issue: float
    median_processing_time: float
    p95_processing_time: float
    p99_processing_time: float
    
    # システム情報
    system_cpu_count: int
    system_memory_total_gb: float
    python_version: str
    
    def to_dict(self) -> Dict[str, Any]return asdict(self):
    """書形式で出力"""

:
class ResourceMonitor:
    """リソース使用量監視"""
    
    def __init__(self):
        self.cpu_samples = []
        self.memory_samples = []
        self.io_start = None
        self.io_end = None
        self.monitoring = False
        
    def start_monitoring(self):
        """監視開始"""
        self.monitoring = True
        self.io_start = psutil.disk_io_counters()
        self.cpu_samples = []
        self.memory_samples = []
        
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring = False
        self.io_end = psutil.disk_io_counters()
        
    async def collect_sample(self):
        """サンプル収集（非同期で呼び出される）"""
        if not self.monitoring:
            return
            
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        self.cpu_samples.append(cpu_percent)
        
        # メモリ使用量
        memory_info = psutil.virtual_memory()
        self.memory_samples.append(memory_info.used / 1024 / 1024)  # MB
        
    def get_cpu_stats(self) -> Dict[str, float]:
        """CPU統計取得"""
        if not self.cpu_samples:
            return {"avg": 0.0, "peak": 0.0}
            
        return {
            "avg": sum(self.cpu_samples) / len(self.cpu_samples),
            "peak": max(self.cpu_samples)
        }
        
    def get_memory_stats(self) -> Dict[str, float]:
        """メモリ統計取得"""
        if not self.memory_samples:
            return {"start": 0.0, "peak": 0.0, "end": 0.0}
            
        return {
            "start": self.memory_samples[0] if self.memory_samples else 0.0,
            "peak": max(self.memory_samples),
            "end": self.memory_samples[-1] if self.memory_samples else 0.0
        }
        
    def get_io_stats(self) -> Dict[str, float]:
        """I/O統計取得"""
        if not self.io_start or not self.io_end:
            return {"read_mb": 0.0, "write_mb": 0.0}
            
        read_bytes = self.io_end.read_bytes - self.io_start.read_bytes
        write_bytes = self.io_end.write_bytes - self.io_start.write_bytes
        
        return {
            "read_mb": read_bytes / 1024 / 1024,
            "write_mb": write_bytes / 1024 / 1024
        }


class A2APerformanceBenchmark:
    """Auto Issue Processor A2A パフォーマンスベンチマーク"""
    
    def __init__(self, output_dir: str = "performance_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.resource_monitor = ResourceMonitor()
        self.processing_times = []
        
        # プロファイラー
        self.profiler = None
        
        logger.info(f"Performance benchmark initialized. Output: {self.output_dir}")
        
    async def run_benchmark(
        self,
        test_scenarios: List[Dict[str, Any]],
        iterations: int = 3
    ) -> List[PerformanceMetrics]:
        """ベンチマーク実行"""
        results = []
        
        for scenario in test_scenarios:
            logger.info(f"Running scenario: {scenario['name']}")
            
            scenario_results = []
            for iteration in range(iterations):
                logger.info(f"Iteration {iteration + 1}/{iterations}")
                
                # メモリトレースの開始
                tracemalloc.start()
                
                # パフォーマンス測定
                metrics = await self._run_single_benchmark(scenario)
                scenario_results.append(metrics)
                
                # メモリリーク検出
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                logger.info(f"Memory usage - Current: {
                    current / 1024 / 1024:0.2f} MB,
                    Peak: {peak / 1024 / 1024:0.2f
                } MB")
                
                # 次のイテレーションまでの間隔
                await asyncio.sleep(2)
            
            # シナリオの平均結果を計算
            avg_metrics = self._calculate_average_metrics(scenario_results)
            results.append(avg_metrics)
            
            # 結果を保存
            await self._save_scenario_results(scenario, scenario_results, avg_metrics)
        
        return results
    
    async def _run_single_benchmark(self, scenario: Dict[str, Any]) -> PerformanceMetrics:
        """単一ベンチマーク実行"""
        
        # システム情報取得
        system_info = self._get_system_info()
        
        # リソース監視開始
        self.resource_monitor.start_monitoring()
        
        # プロファイラー開始
        if scenario.get("enable_profiling", False):
            self.profiler = cProfile.Profile()
            self.profiler.enable()
        
        start_time = time.time()
        processing_times = []
        errors_count = 0
        retry_count = 0
        timeout_count = 0
        
        try:
            # モニタリングタスクを開始
            monitor_task = asyncio.create_task(self._monitor_resources())
            
            # 並列処理実行
            concurrent_limit = scenario.get("concurrent_limit", 5)
            issue_count = scenario.get("issue_count", 10)
            
            # セマフォで並列度制御
            semaphore = asyncio.Semaphore(concurrent_limit)
            
            async def process_single_issue(issue_id: int):
                async with semaphore:
                    issue_start = time.time()
                    try:
                        # 模擬的なイシュー処理
                        await self._simulate_issue_processing(issue_id, scenario)
                        processing_time = time.time() - issue_start
                        processing_times.append(processing_time)
                        
                    except asyncio.TimeoutError:
                        nonlocal timeout_count
                        timeout_count += 1
                    except Exception as e:
                        nonlocal errors_count, retry_count
                        errors_count += 1
                        if "retry" in str(e).lower():
                            retry_count += 1
                        logger.error(f"Error processing issue {issue_id}: {e}")
            
            # 全イシューを並列処理
            tasks = [process_single_issue(i) for i in range(issue_count)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            monitor_task.cancel()
            
        finally:
            end_time = time.time()
            
            # プロファイラー停止
            if self.profiler:
                self.profiler.disable()
                
            # リソース監視停止
            self.resource_monitor.stop_monitoring()
        
        # 統計計算
        duration = end_time - start_time
        issues_processed = len(processing_times)
        issues_per_second = issues_processed / duration if duration > 0 else 0
        
        # リソース統計
        cpu_stats = self.resource_monitor.get_cpu_stats()
        memory_stats = self.resource_monitor.get_memory_stats()
        io_stats = self.resource_monitor.get_io_stats()
        
        # 処理時間統計
        processing_stats = self._calculate_processing_time_stats(processing_times)
        
        return PerformanceMetrics(
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            issues_processed=issues_processed,
            issues_per_second=issues_per_second,
            concurrent_processes=scenario.get("concurrent_limit", 5),
            memory_start_mb=memory_stats["start"],
            memory_peak_mb=memory_stats["peak"],
            memory_end_mb=memory_stats["end"],
            memory_delta_mb=memory_stats["end"] - memory_stats["start"],
            cpu_percent_avg=cpu_stats["avg"],
            cpu_percent_peak=cpu_stats["peak"],
            disk_read_mb=io_stats["read_mb"],
            disk_write_mb=io_stats["write_mb"],
            network_sent_mb=0.0,  # ネットワーク統計は別途実装
            network_received_mb=0.0,
            errors_count=errors_count,
            retry_count=retry_count,
            timeout_count=timeout_count,
            avg_processing_time_per_issue=processing_stats["avg"],
            median_processing_time=processing_stats["median"],
            p95_processing_time=processing_stats["p95"],
            p99_processing_time=processing_stats["p99"],
            system_cpu_count=system_info["cpu_count"],
            system_memory_total_gb=system_info["memory_total_gb"],
            python_version=system_info["python_version"]
        )
    
    async def _monitor_resources(self):
        """リソース監視（バックグラウンドタスク）"""
        try:
            while True:
                await self.resource_monitor.collect_sample()
                await asyncio.sleep(0.1)  # 100ms間隔でサンプリング
        except asyncio.CancelledError:
            pass
    
    async def _simulate_issue_processing(self, issue_id: int, scenario: Dict[str, Any])processing_delay = scenario.get("processing_delay_ms", 100) / 1000.0
    """イシュー処理のシミュレーション"""
        
        # 実際の処理をシミュレート
        if scenario.get("simulate_real_processing", False):
            # ファイルI/O操作をシミュレート
            test_file = self.output_dir / f"temp_issue_{issue_id}.tmp"
            with open(test_file, "w") as f:
                f.write(f"Issue {issue_id} processing data\n" * 100)
            
            # CPU集約的な処理をシミュレート
            total = 0
            for i in range(1000):
                total += i ** 0.5
            
            # ファイル削除
            test_file.unlink()
        
        await asyncio.sleep(processing_delay)
        
        # エラーシミュレーション
        error_rate = scenario.get("error_rate", 0.0)
        if error_rate > 0 and (issue_id % int(1 / error_rate)) == 0:
            raise Exception(f"Simulated error for issue {issue_id}")
    
    def _calculate_processing_time_stats(self, times: List[float]) -> Dict[str, float]:
        """処理時間統計計算"""
        if not times:
            return {"avg": 0.0, "median": 0.0, "p95": 0.0, "p99": 0.0}
        
        times_sorted = sorted(times)
        n = len(times_sorted)
        
        return {
            "avg": sum(times) / n,
            "median": times_sorted[n // 2],
            "p95": times_sorted[int(n * 0.95)] if n > 0 else 0.0,
            "p99": times_sorted[int(n * 0.99)] if n > 0 else 0.0
        }
    
    def _calculate_average_metrics(self, metrics_list: List[PerformanceMetrics]) -> PerformanceMetrics:
        """複数の測定結果の平均を計算"""
        if not metrics_list:
            raise ValueError("Empty metrics list")
        
        if len(metrics_list) == 1:
            return metrics_list[0]
        
        # 数値フィールドの平均を計算
        avg_metrics = metrics_list[0]
        
        # 集計可能な数値フィールドのみ平均化
        numeric_fields = [
            "duration_seconds", "issues_per_second", "memory_delta_mb",
            "cpu_percent_avg", "cpu_percent_peak", "disk_read_mb", "disk_write_mb",
            "avg_processing_time_per_issue", "median_processing_time",
            "p95_processing_time", "p99_processing_time"
        ]
        
        for field in numeric_fields:
            values = [getattr(m, field) for m in metrics_list]
            setattr(avg_metrics, field, sum(values) / len(values))
        
        return avg_metrics
    
    def _get_system_info(self) -> Dict[str, Any]:
        """システム情報取得"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "python_version": sys.version
        }
    
    async def _save_scenario_results(
        self,
        scenario: Dict[str, Any],
        iterations: List[PerformanceMetrics],
        average: PerformanceMetrics
    ):
        """シナリオ結果保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{scenario['name']}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        results = {
            "scenario": scenario,
            "timestamp": timestamp,
            "iterations": [m.to_dict() for m in iterations],
            "average": average.to_dict(),
            "summary": {
                "scenario_name": scenario["name"],
                "avg_duration_seconds": average.duration_seconds,
                "avg_issues_per_second": average.issues_per_second,
                "avg_memory_usage_mb": average.memory_delta_mb,
                "avg_cpu_usage_percent": average.cpu_percent_avg,
                "error_rate": average.errors_count / average.issues_processed if average.issues_processed > 0 else 0
            }
        }
        
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to: {filepath}")
        
        # プロファイル結果保存
        if self.profiler:
            profile_filename = f"profile_{scenario['name']}_{timestamp}.prof"
            profile_filepath = self.output_dir / profile_filename
            
            # プロファイル統計をテキストファイルとして保存
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(50)  # 上位50関数
            
            with open(str(profile_filepath) + ".txt", "w") as f:
                f.write(s.getvalue())
    
    def generate_report(self, results: List[PerformanceMetrics]) -> str:
        """ベンチマーク結果レポート生成"""
        report = []
        report.append("# Auto Issue Processor A2A Performance Benchmark Report")
        report.append(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for i, metrics in enumerate(results):
            report.append(f"## Scenario {i + 1}")
            report.append(f"- **Duration**: {metrics.duration_seconds:0.2f} seconds")
            report.append(f"- **Issues Processed**: {metrics.issues_processed}")
            report.append(f"- **Throughput**: {metrics.issues_per_second:0.2f} issues/second")
            report.append(f"- **Concurrent Processes**: {metrics.concurrent_processes}")
            report.append(f"- **Memory Usage**: {metrics.memory_delta_mb:0.2f} MB delta")
            report.append(f"- **CPU Usage**: {
                metrics.cpu_percent_avg:0.1f}% average,
                {metrics.cpu_percent_peak:0.1f
            }% peak")
            report.append(f"- **Processing Time**: {metrics.avg_processing_time_per_issue:." \
                "3f}s avg, {metrics.p95_processing_time:0.3f}s p95")
                        report.append(f"- **Errors**: {metrics.errors_count} \
                ({metrics.errors_count/metrics.issues_processed*100:0.1f}%)")
            report.append("")
        
        # ボトルネック分析
        report.append("## Bottleneck Analysis")
        if results:
            avg_metrics = results[0]
            
            if avg_metrics.cpu_percent_avg > 80:
                report.append("- ⚠️ **CPU Bottleneck**: High CPU usage detected")
            
            if avg_metrics.memory_delta_mb > 500:
                report.append("- ⚠️ **Memory Usage**: High memory consumption detected")
            
            if avg_metrics.issues_per_second < 1.0:
                report.append("- ⚠️ **Low Throughput**: Processing speed below expected threshold")
            
            if avg_metrics.errors_count > 0:
                report.append(f"- ⚠️ **Error Rate**: {avg_metrics.errors_count} errors occurred")
        
        report.append("")
        report.append("## Recommendations")
        report.append("- Consider implementing dynamic resource scaling")
        report.append("- Optimize memory usage through streaming processing")
        report.append("- Implement connection pooling for external APIs")
        report.append("- Add comprehensive error handling and retry logic")
        
        return "\n".join(report)


# 事前定義されたテストシナリオ
DEFAULT_TEST_SCENARIOS = [
    {
        "name": "baseline_sequential",
        "description": "ベースライン: 逐次処理",
        "concurrent_limit": 1,
        "issue_count": 10,
        "processing_delay_ms": 100,
        "enable_profiling": True,
        "simulate_real_processing": False
    },
    {
        "name": "parallel_5_concurrent",
        "description": "並列処理: 5プロセス",
        "concurrent_limit": 5,
        "issue_count": 20,
        "processing_delay_ms": 100,
        "enable_profiling": True,
        "simulate_real_processing": True
    },
    {
        "name": "parallel_10_concurrent", 
        "description": "並列処理: 10プロセス",
        "concurrent_limit": 10,
        "issue_count": 30,
        "processing_delay_ms": 100,
        "enable_profiling": False,
        "simulate_real_processing": True
    },
    {
        "name": "stress_test_50_issues",
        "description": "ストレステスト: 50イシュー",
        "concurrent_limit": 5,
        "issue_count": 50,
        "processing_delay_ms": 50,
        "error_rate": 0.05,  # 5%エラー率
        "enable_profiling": False,
        "simulate_real_processing": True
    }
]


async def main():
    """ベンチマーク実行メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Auto Issue Processor A2A Performance Benchmark")
    
    # ベンチマーク実行
    benchmark = A2APerformanceBenchmark()
    
    # 事前定義シナリオを使用
    results = await benchmark.run_benchmark(DEFAULT_TEST_SCENARIOS, iterations=2)
    
    # レポート生成
    report = benchmark.generate_report(results)
    
    # レポート保存
    report_file = benchmark.output_dir / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"\n{report}")
    print(f"\nDetailed results saved to: {benchmark.output_dir}")
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
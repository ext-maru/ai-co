#!/usr/bin/env python3
"""
Performance Testing Utilities - TDD Implementation
パフォーマンステストユーティリティ

GREEN Phase: テストを通すための最小限の実装
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gc
import json
import statistics
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import psutil


class PerformanceTimer:
    """パフォーマンス測定タイマー"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """タイマーが実行中かどうか"""
        return self.start_time is not None and self.end_time is None

    @property
    def duration(self) -> float:
        """実行時間（秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    def start(self):
        """タイマー開始"""
        with self._lock:
            self.start_time = time.time()
            self.end_time = None

    def stop(self):
        """タイマー停止"""
        with self._lock:
            if self.start_time is not None:
                self.end_time = time.time()

    def __enter__(self):
        """コンテキストマネージャー開始"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.stop()


class PerformanceCollector:
    """パフォーマンスメトリクス収集器"""

    def __init__(self):
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def add_metric(
        self, operation: str, duration: float, metadata: Optional[Dict] = None
    ):
        """メトリクスを追加"""
        with self._lock:
            if operation not in self._metrics:
                self._metrics[operation] = []

            metric = {
                "duration": duration,
                "timestamp": time.time(),
                "metadata": metadata or {},
            }
            self._metrics[operation].append(metric)

    def get_statistics(self, operation: str) -> Dict[str, float]:
        """操作の統計情報を取得"""
        with self._lock:
            if operation not in self._metrics or not self._metrics[operation]:
                return {"count": 0, "average": 0, "min": 0, "max": 0}

            durations = [m["duration"] for m in self._metrics[operation]]
            return {
                "count": len(durations),
                "average": statistics.mean(durations),
                "min": min(durations),
                "max": max(durations),
                "median": statistics.median(durations),
                "stdev": statistics.stdev(durations) if len(durations) > 1 else 0,
            }

    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """すべてのメトリクスを取得"""
        with self._lock:
            return dict(self._metrics)

    @contextmanager
    def measure(self, operation: str, metadata: Optional[Dict] = None):
        """コンテキストマネージャーで測定"""
        timer = PerformanceTimer(operation)
        timer.start()
        try:
            yield timer
        finally:
            timer.stop()
            self.add_metric(operation, timer.duration, metadata)


class MemoryTracker:
    """メモリ使用量トラッカー"""

    def __init__(self):
        self._process = psutil.Process()
        self._tracking_data: Dict[str, Dict[str, float]] = {}

    def get_current_memory(self) -> float:
        """現在のメモリ使用量を取得（MB）"""
        return self._process.memory_info().rss / 1024 / 1024

    def start_tracking(self, operation: str):
        """メモリ追跡開始"""
        gc.collect()  # ガベージコレクション実行
        initial_memory = self.get_current_memory()
        self._tracking_data[operation] = {
            "initial_memory": initial_memory,
            "peak_memory": initial_memory,
            "start_time": time.time(),
        }

    def stop_tracking(self, operation: str) -> Dict[str, float]:
        """メモリ追跡停止"""
        if operation not in self._tracking_data:
            raise ValueError(f"Operation {operation} not being tracked")

        gc.collect()  # ガベージコレクション実行
        final_memory = self.get_current_memory()
        data = self._tracking_data[operation]

        result = {
            "initial_memory": data["initial_memory"],
            "final_memory": final_memory,
            "peak_memory": max(data["peak_memory"], final_memory),
            "memory_delta": final_memory - data["initial_memory"],
            "duration": time.time() - data["start_time"],
        }

        del self._tracking_data[operation]
        return result


class WorkerBenchmark:
    """ワーカー性能ベンチマーク"""

    def __init__(self):
        self.collector = PerformanceCollector()

    def benchmark_task_worker(
        self, task_count: int, concurrent_workers: int, timeout: int
    ) -> Dict[str, float]:
        """TaskWorkerのベンチマーク（模擬実装）"""
        start_time = time.time()
        completed_tasks = 0

        def simulate_task_processing():
            nonlocal completed_tasks
            # 模擬的なタスク処理（実際のワーカーの代わり）
            """simulate_task_processingを処理"""
            time.sleep(0.01)  # 10ms の処理時間を模擬
            completed_tasks += 1

        # 並行処理でタスクを実行
        threads = []
        tasks_per_worker = task_count // concurrent_workers

        for _ in range(concurrent_workers):
        # 繰り返し処理
            for _ in range(tasks_per_worker):
                thread = threading.Thread(target=simulate_task_processing)
                threads.append(thread)
                thread.start()

        # すべてのスレッドの完了を待つ
        for thread in threads:
            thread.join(timeout=timeout)

        total_time = time.time() - start_time

        return {
            "total_tasks": completed_tasks,
            "avg_processing_time": total_time / max(completed_tasks, 1),
            "throughput": completed_tasks / total_time if total_time > 0 else 0,
            "success_rate": completed_tasks / task_count if task_count > 0 else 0,
        }


class RabbitMQBenchmark:
    """RabbitMQ接続性能ベンチマーク"""

    def __init__(self):
        self.collector = PerformanceCollector()

    def benchmark_connection_pool(
        self, connection_count: int, operations_per_connection: int
    ) -> Dict[str, float]:
        """RabbitMQ接続プールのベンチマーク（模擬実装）"""
        connection_times = []
        message_send_times = []
        successful_connections = 0

        for _ in range(connection_count):
            # 模擬的な接続時間
            conn_start = time.time()
            time.sleep(0.001)  # 1ms の接続時間を模擬
            conn_time = time.time() - conn_start
            connection_times.append(conn_time)
            successful_connections += 1

            # 模擬的なメッセージ送信
            for _ in range(operations_per_connection):
                send_start = time.time()
                time.sleep(0.0001)  # 0.1ms のメッセージ送信時間を模擬
                send_time = time.time() - send_start
                message_send_times.append(send_time)

        return {
            "avg_connection_time": statistics.mean(connection_times)
            if connection_times
            else 0,
            "avg_message_send_time": statistics.mean(message_send_times)
            if message_send_times
            else 0,
            "connection_success_rate": successful_connections / connection_count
            if connection_count > 0
            else 0,
        }


class MemoryLeakDetector:
    """メモリリーク検出器"""

    def __init__(self):
        self.tracker = MemoryTracker()

    def detect_memory_leak(
        self, func: Callable, iterations: int, threshold_mb: float
    ) -> Dict[str, Any]:
        """メモリリーク検出"""
        initial_memory = self.tracker.get_current_memory()
        memory_samples = [initial_memory]

        # 複数回関数を実行してメモリ使用量を監視
        for i in range(iterations):
            func()
            if i % 10 == 0:  # 10回ごとにメモリ使用量をサンプリング
                gc.collect()
                current_memory = self.tracker.get_current_memory()
                memory_samples.append(current_memory)

        final_memory = self.tracker.get_current_memory()
        memory_growth = final_memory - initial_memory
        peak_memory = max(memory_samples)

        return {
            "memory_growth": memory_growth,
            "leak_detected": memory_growth > threshold_mb,
            "peak_memory": peak_memory,
            "initial_memory": initial_memory,
            "final_memory": final_memory,
            "samples": memory_samples,
        }


class PerformanceReporter:
    """パフォーマンスレポート生成器"""

    def __init__(self):
        self.benchmark_results: Dict[str, Dict[str, Any]] = {}
        self.timestamp = datetime.now()

    def add_benchmark_result(self, name: str, result: Dict[str, Any]):
        """ベンチマーク結果を追加"""
        self.benchmark_results[name] = {
            **result,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_report(self, format: str = "dict") -> Any:
        """レポート生成"""
        report_data = {
            "summary": {
                "total_benchmarks": len(self.benchmark_results),
                "report_generated": self.timestamp.isoformat(),
            },
            "benchmarks": self.benchmark_results,
            "timestamp": self.timestamp.isoformat(),
        }

        if format == "dict":
            return report_data
        elif format == "html":
            return self._generate_html_report(report_data)
        elif format == "json":
            return json.dumps(report_data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """HTMLレポート生成"""
        html = f"""
        <html>
        <head>
            <title>Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .benchmark {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .metric {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>Performance Report</h1>
            <p>Generated: {data['timestamp']}</p>
            <p>Total Benchmarks: {data['summary']['total_benchmarks']}</p>

            <h2>Benchmark Results</h2>
        """

        # 繰り返し処理
        for name, result in data["benchmarks"].items():
            html += f"""
            <div class="benchmark">
                <h3>{name}</h3>
            """
            for key, value in result.items():
                if key != "timestamp":
                    html += f'<div class="metric"><strong>{key}:</strong> {value}</div>'
            html += "</div>"

        html += """
        </body>
        </html>
        """
        return html

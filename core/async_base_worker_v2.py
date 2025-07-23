#!/usr/bin/env python3
"""
非同期処理対応の基底ワーカークラス v2
軽量ロガー対応、依存関係最小化版
"""

import asyncio
import json
import os

# 軽量ロガーの使用
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))
from lightweight_logger import LoggingMixin, get_logger


# 軽量メトリクス実装
class SimpleMetrics:
    """軽量メトリクス実装（Prometheus代替）"""

    def __init__(self, worker_name: str):
        """初期化メソッド"""
        self.worker_name = worker_name
        self.counters = {}
        self.gauges = {}
        self.histograms = {}

    def counter(self, name: str, description: str = ""):
        key = f"{self.worker_name}_{name}"
        if key not in self.counters:
            self.counters[key] = 0
        return SimpleCounter(self.counters, key)

    def gauge(self, name: str, description: str = ""):
        key = f"{self.worker_name}_{name}"
        if key not in self.gauges:
            self.gauges[key] = 0
        return SimpleGauge(self.gauges, key)

    def histogram(self, name: str, description: str = ""):
        key = f"{self.worker_name}_{name}"
        if key not in self.histograms:
            self.histograms[key] = []
        return SimpleHistogram(self.histograms, key)

    def get_metrics(self) -> Dict[str, Any]:
        """全メトリクスの取得"""
        metrics = {"counters": self.counters.copy(), "gauges": self.gauges.copy()}

        # ヒストグラムの統計を計算
        hist_stats = {}
        for name, values in self.histograms.items():
            if values:
                hist_stats[name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
            else:
                hist_stats[name] = {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}

        metrics["histograms"] = hist_stats
        return metrics


class SimpleCounter:
    def __init__(self, storage: Dict, key: str):
        """初期化メソッド"""
        self.storage = storage
        self.key = key

    def inc(self, amount: float = 1):
        self.storage[self.key] += amount

    def labels(self, **kwargs):
        # ラベル対応は簡略化
        label_key = f"{self.key}_{hash(str(kwargs))}"
        if label_key not in self.storage:
            self.storage[label_key] = 0
        return SimpleCounter(self.storage, label_key)


class SimpleGauge:
    def __init__(self, storage: Dict, key: str):
        """初期化メソッド"""
        self.storage = storage
        self.key = key

    def set(self, value: float):
        self.storage[self.key] = value

    def inc(self, amount: float = 1):
        self.storage[self.key] += amount

    def dec(self, amount: float = 1):
        self.storage[self.key] -= amount

    def labels(self, **kwargs):
        label_key = f"{self.key}_{hash(str(kwargs))}"
        if label_key not in self.storage:
            self.storage[label_key] = 0
        return SimpleGauge(self.storage, label_key)


class SimpleHistogram:
    def __init__(self, storage: Dict, key: str):
        """初期化メソッド"""
        self.storage = storage
        self.key = key

    def observe(self, value: float):
        self.storage[self.key].append(value)
        # 古いデータを削除（最新1000件のみ保持）
        if len(self.storage[self.key]) > 1000:
            self.storage[self.key] = self.storage[self.key][-1000:]


# 簡易サーキットブレーカー
class SimpleCircuitBreaker:
    """軽量サーキットブレーカー実装"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """初期化メソッド"""
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    async def call(self, func: Callable, *args, **kwargs):
        """サーキットブレーカー経由での関数実行"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise e


class AsyncBaseWorkerV2(ABC, LoggingMixin):
    """
    非同期処理対応の基底ワーカークラス v2

    Features:
    - 軽量ロガー使用
    - 最小限の依存関係
    - 基本的なメトリクス・サーキットブレーカー
    - ヘルスチェック
    """

    def __init__(
        self,
        worker_name: str,
        config: Dict[str, Any],
        input_queues: list[str],
        output_queues: Optional[list[str]] = None,
    ):
        # LoggingMixinの初期化
        self.logger_name = worker_name
        super().__init__()

        self.worker_name = worker_name
        self.config = config
        self.input_queues = input_queues
        self.output_queues = output_queues or []

        # メトリクス設定
        self.metrics = SimpleMetrics(worker_name)
        self._setup_metrics()

        # サーキットブレーカー設定
        self.circuit_breaker = SimpleCircuitBreaker(
            failure_threshold=config.get("circuit_breaker_threshold", 5),
            timeout=config.get("circuit_breaker_timeout", 60),
        )

        # ヘルスチェック状態
        self.health_status = {
            "status": "initializing",
            "last_check": datetime.utcnow().isoformat(),
            "details": {
                "worker_name": worker_name,
                "uptime": 0,
                "processed_messages": 0,
                "failed_messages": 0,
                "circuit_breaker_state": "closed",
            },
        }

        # 実行制御
        self.running = False
        self.tasks = set()

        # 起動時刻
        self.start_time = time.time()

        self.logger.info(
            "Worker initialized", input_queues=input_queues, output_queues=output_queues
        )

    def _setup_metrics(self):
        """メトリクスの初期化"""
        self.processed_messages = self.metrics.counter(
            "processed_total", "Total processed messages"
        )
        self.processing_time = self.metrics.histogram(
            "processing_seconds", "Message processing time"
        )
        self.active_tasks = self.metrics.gauge("active_tasks", "Currently active tasks")
        self.queue_size = self.metrics.gauge("queue_size", "Current queue size")

    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        メッセージ処理の抽象メソッド
        サブクラスで実装必須
        """
        pass

    async def _handle_message_simulation(self, message_data: Dict[str, Any]):
        """メッセージ処理のシミュレーション（RabbitMQ未使用時）"""
        task_id = None
        start_time = time.time()

        try:
            # アクティブタスク数を増やす
            self.active_tasks.inc()

            task_id = message_data.get("task_id", "unknown")

            # ログコンテキストの設定
            task_logger = self.logger.bind(task_id=task_id)

            task_logger.info("Processing message", message_size=len(str(message_data)))

            # サーキットブレーカー経由で処理
            result = await self.circuit_breaker.call(self.process_message, message_data)

            # 処理時間の記録
            duration = time.time() - start_time
            self.processing_time.observe(duration)
            self.processed_messages.labels(status="success").inc()

            task_logger.info("Message processed successfully", duration=duration)

            # ヘルスステータス更新
            self.health_status["details"]["processed_messages"] += 1

            return result

        except Exception as e:
            # エラー処理
            self.processed_messages.labels(status="error").inc()
            self.health_status["details"]["failed_messages"] += 1

            self.logger.error(
                "Message processing failed",
                error=str(e),
                error_type=type(e).__name__,
                task_id=task_id,
                duration=time.time() - start_time,
            )

            raise

        finally:
            # アクティブタスク数を減らす
            self.active_tasks.dec()

    async def run_simulation(self, test_messages: list[Dict[str, Any]]):
        """シミュレーション実行（テスト用）"""
        self.running = True

        try:
            self.logger.info("Starting simulation", message_count=len(test_messages))

            # ヘルスチェックタスクの開始
            health_task = asyncio.create_task(self._health_check_loop())
            self.tasks.add(health_task)

            # テストメッセージの処理
            results = []
            for message in test_messages:
                try:
                    result = await self._handle_message_simulation(message)
                    results.append(result)
                except Exception as e:
                    self.logger.error("Message failed", error=str(e))
                    results.append({"error": str(e)})

            self.logger.info(
                "Simulation completed",
                processed=len(results),
                success=len([r for r in results if "error" not in r]),
            )

            return results

        finally:
            await self.shutdown()

    async def shutdown(self):
        """グレースフルシャットダウン"""
        self.logger.info("Shutting down worker")
        self.running = False

        # アクティブなタスクの完了を待つ
        if self.tasks:
            self.logger.info("Waiting for active tasks", count=len(self.tasks))
            await asyncio.gather(*self.tasks, return_exceptions=True)

        self.logger.info("Worker shutdown complete")

    async def _health_check_loop(self):
        """定期的なヘルスチェック"""
        while self.running:
            try:
                # アップタイムの更新
                uptime = time.time() - self.start_time
                self.health_status["details"]["uptime"] = uptime
                self.health_status["last_check"] = datetime.utcnow().isoformat()

                # サーキットブレーカーの状態
                self.health_status["details"][
                    "circuit_breaker_state"
                ] = self.circuit_breaker.state

                if self.circuit_breaker.state == "open":
                    self.health_status["status"] = "degraded"
                else:
                    self.health_status["status"] = "healthy"

                await asyncio.sleep(30)  # 30秒ごとにチェック

            except Exception as e:
                self.logger.error("Health check error", error=str(e))
                await asyncio.sleep(30)

    async def get_health(self) -> Dict[str, Any]:
        """ヘルスステータスの取得"""
        return self.health_status

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスの取得"""
        return self.metrics.get_metrics()


# テスト用の実装例
class TestWorkerV2(AsyncBaseWorkerV2):
    """テスト用ワーカー"""

    def __init__(self, config):
        """初期化メソッド"""
        super().__init__(
            worker_name="test_worker_v2",
            config=config,
            input_queues=["test_input"],
            output_queues=["test_output"],
        )

    async def process_message(self, message):
        """テスト用のメッセージ処理"""
        # 簡単な処理のシミュレーション
        await asyncio.sleep(0.1)

        return {
            "status": "processed",
            "original_message": message,
            "processed_at": datetime.utcnow().isoformat(),
            "worker": self.worker_name,
        }


# テスト実行
async def test_async_base_worker_v2():
    """AsyncBaseWorkerV2のテスト"""
    print("🧪 AsyncBaseWorkerV2 テスト開始...")

    config = {"circuit_breaker_threshold": 3, "circuit_breaker_timeout": 5}

    worker = TestWorkerV2(config)

    # テストメッセージ
    test_messages = [
        {"task_id": "test_001", "type": "simple", "data": "Hello World"},
        {"task_id": "test_002", "type": "complex", "data": {"key": "value"}},
        {"task_id": "test_003", "type": "batch", "data": list(range(10))},
    ]

    # シミュレーション実行
    results = await worker.run_simulation(test_messages)

    # 結果確認
    assert len(results) == 3
    assert all("status" in result for result in results if "error" not in result)

    # ヘルスチェック
    health = await worker.get_health()
    assert health["status"] in ["healthy", "degraded"]

    # メトリクス確認
    metrics = worker.get_metrics()
    assert "counters" in metrics
    assert "gauges" in metrics
    assert "histograms" in metrics

    print("  ✅ 全てのテストが成功")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_async_base_worker_v2())
    print(f"🎯 AsyncBaseWorkerV2 テスト{'成功' if success else '失敗'}")

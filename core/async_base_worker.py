#!/usr/bin/env python3
"""
非同期処理対応の基底ワーカークラス
改修プロジェクト Phase 1
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import aio_pika
import aioredis
import structlog
from circuitbreaker import Circuitbreaker as CircuitBreaker
from prometheus_client import Counter, Gauge, Histogram, generate_latest


class AsyncBaseWorker(ABC):
    """
    非同期処理対応の基底ワーカークラス

    Features:
    - 非同期メッセージ処理
    - サーキットブレーカー
    - メトリクス収集
    - 構造化ログ
    - ヘルスチェック
    - グレースフルシャットダウン
    """

    def __init__(
        self,
        worker_name: str,
        config: Dict[str, Any],
        input_queues: list[str],
        output_queues: Optional[list[str]] = None,
    ):
        self.worker_name = worker_name
        self.config = config
        self.input_queues = input_queues
        self.output_queues = output_queues or []

        # 構造化ログ設定
        self.logger = structlog.get_logger(
            worker_name=worker_name, worker_id=f"{worker_name}_{int(time.time())}"
        )

        # メトリクス設定
        self._setup_metrics()

        # サーキットブレーカー設定
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get("circuit_breaker_threshold", 5),
            recovery_timeout=config.get("circuit_breaker_timeout", 60),
            expected_exception=Exception,
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

        # 接続管理
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.redis_client = None

        # 実行制御
        self.running = False
        self.tasks = set()

        # 起動時刻
        self.start_time = time.time()

    def _setup_metrics(self):
        """メトリクスの初期化"""
        self.processed_messages = Counter(
            f"{self.worker_name}_processed_total",
            "Total processed messages",
            ["status"],
        )

        self.processing_time = Histogram(
            f"{self.worker_name}_processing_seconds", "Message processing time"
        )

        self.active_tasks = Gauge(
            f"{self.worker_name}_active_tasks", "Currently active tasks"
        )

        self.queue_size = Gauge(
            f"{self.worker_name}_queue_size", "Current queue size", ["queue"]
        )

    async def connect(self):
        """接続の確立"""
        try:
            # RabbitMQ接続
            self.rabbitmq_connection = await aio_pika.connect_robust(
                f"amqp://{self.config['rabbitmq_user']}:{self.config['rabbitmq_pass']}@"
                f"{self.config['rabbitmq_host']}:{self.config['rabbitmq_port']}/",
                heartbeat=self.config.get("rabbitmq_heartbeat", 600),
            )

            self.rabbitmq_channel = await self.rabbitmq_connection.channel()
            await self.rabbitmq_channel.set_qos(prefetch_count=1)

            # Redis接続
            redis_url = self.config.get("redis_url", "redis://localhost:6379")
            self.redis_client = await aioredis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )

            self.logger.info(
                "Connections established", rabbitmq="connected", redis="connected"
            )

            # ヘルスステータス更新
            self.health_status["status"] = "healthy"

        except Exception as e:
            self.logger.error("Failed to establish connections", error=str(e))
            self.health_status["status"] = "unhealthy"
            self.health_status["details"]["error"] = str(e)
            raise

    async def disconnect(self):
        """接続のクリーンアップ"""
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()

        if self.redis_client:
            await self.redis_client.close()

        self.logger.info("Connections closed")

    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        メッセージ処理の抽象メソッド
        サブクラスで実装必須
        """
        pass

    async def _handle_message(self, message: aio_pika.IncomingMessage):
        """メッセージハンドリングのラッパー"""
        task_id = None
        start_time = time.time()

        async with message.process():
            try:
                # アクティブタスク数を増やす
                self.active_tasks.inc()

                # メッセージのパース
                body = json.loads(message.body.decode())
                task_id = body.get("task_id", "unknown")

                # ログコンテキストの設定
                self.logger = self.logger.bind(task_id=task_id)

                self.logger.info(
                    "Processing message",
                    queue=message.routing_key,
                    size=len(message.body),
                )

                # サーキットブレーカー経由で処理
                result = await self.circuit_breaker.call(self.process_message, body)

                # 処理時間の記録
                duration = time.time() - start_time
                self.processing_time.observe(duration)
                self.processed_messages.labels(status="success").inc()

                self.logger.info("Message processed successfully", duration=duration)

                # 結果を出力キューに送信
                if result and self.output_queues:
                    await self._send_to_output_queues(result)

                # ヘルスステータス更新
                self.health_status["details"]["processed_messages"] += 1

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

                # DLQへの送信を検討
                await self._handle_error(message, e)

            finally:
                # アクティブタスク数を減らす
                self.active_tasks.dec()
                # ログコンテキストのクリア
                self.logger = self.logger.unbind("task_id")

    async def _send_to_output_queues(self, result: Dict[str, Any]):
        """結果を出力キューに送信"""
        for queue_name in self.output_queues:
            try:
                queue = await self.rabbitmq_channel.declare_queue(
                    queue_name, durable=True
                )

                await self.rabbitmq_channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(result).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=queue_name,
                )

                self.logger.debug("Result sent to output queue", queue=queue_name)

            except Exception as e:
                self.logger.error(
                    "Failed to send to output queue", queue=queue_name, error=str(e)
                )

    async def _handle_error(self, message: aio_pika.IncomingMessage, error: Exception):
        """エラーハンドリング"""
        # エラー情報をDLQに送信
        dlq_name = f"{message.routing_key}_dlq"

        try:
            dlq = await self.rabbitmq_channel.declare_queue(dlq_name, durable=True)

            error_info = {
                "original_message": json.loads(message.body.decode()),
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": datetime.utcnow().isoformat(),
                "worker": self.worker_name,
                "queue": message.routing_key,
            }

            await self.rabbitmq_channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(error_info).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=dlq_name,
            )

            self.logger.info("Error sent to DLQ", dlq=dlq_name)

        except Exception as dlq_error:
            self.logger.error("Failed to send to DLQ", error=str(dlq_error))

    async def run(self):
        """ワーカーのメインループ"""
        self.running = True

        try:
            # 接続確立
            await self.connect()

            # キューのコンシューマー設定
            for queue_name in self.input_queues:
                queue = await self.rabbitmq_channel.declare_queue(
                    queue_name, durable=True
                )

                # メッセージの消費開始
                await queue.consume(self._handle_message)

                self.logger.info("Started consuming", queue=queue_name)

            # ヘルスチェックタスクの開始
            health_task = asyncio.create_task(self._health_check_loop())
            self.tasks.add(health_task)

            # メトリクス収集タスクの開始
            metrics_task = asyncio.create_task(self._metrics_loop())
            self.tasks.add(metrics_task)

            self.logger.info(
                "Worker started", queues=self.input_queues, pid=asyncio.get_event_loop()
            )

            # シグナルハンドラーの設定
            import signal

            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, lambda s, f: asyncio.create_task(self.shutdown()))

            # メインループ
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error("Worker error", error=str(e))
            self.health_status["status"] = "error"
            self.health_status["details"]["error"] = str(e)

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

        # 接続のクローズ
        await self.disconnect()

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
                if self.circuit_breaker.current_state == "open":
                    self.health_status["details"]["circuit_breaker_state"] = "open"
                    self.health_status["status"] = "degraded"
                else:
                    self.health_status["details"]["circuit_breaker_state"] = "closed"
                    if self.health_status["status"] == "degraded":
                        self.health_status["status"] = "healthy"

                # Redisにヘルス状態を保存
                if self.redis_client:
                    await self.redis_client.setex(
                        f"health:{self.worker_name}",
                        60,  # 1分間のTTL
                        json.dumps(self.health_status),
                    )

                await asyncio.sleep(30)  # 30秒ごとにチェック

            except Exception as e:
                self.logger.error("Health check error", error=str(e))
                await asyncio.sleep(30)

    async def _metrics_loop(self):
        """定期的なメトリクス収集"""
        while self.running:
            try:
                # キューサイズの取得
                for queue_name in self.input_queues:
                    try:
                        queue = await self.rabbitmq_channel.get_queue(queue_name)
                        self.queue_size.labels(queue=queue_name).set(
                            queue.declaration_result.message_count
                        )
                    except:
                        pass

                await asyncio.sleep(60)  # 1分ごとに収集

            except Exception as e:
                self.logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(60)

    async def get_health(self) -> Dict[str, Any]:
        """ヘルスステータスの取得"""
        return self.health_status

    def get_metrics(self) -> bytes:
        """Prometheusメトリクスの取得"""
        return generate_latest()

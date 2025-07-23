#!/usr/bin/env python3
"""
改善版BaseWorker - プロフェッショナルなログ出力
絵文字を最小限に抑え、客観的な情報を重視
"""

import json
import logging
import os
import signal
import sys
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pika
import pika.exceptions

from .common_utils import get_project_paths, setup_logging


class ImprovedBaseWorker(ABC):
    """改善されたワーカー基底クラス（プロフェッショナルなログ）"""

    def __init__(self, worker_type: str, worker_id: Optional[str] = None):
        """
        Args:
            worker_type: ワーカータイプ（task, pm, result, dialog等）
            worker_id: ワーカーID（未指定の場合は自動生成）
        """
        self.worker_type = worker_type
        self.worker_id = worker_id or f"{worker_type}-{os.getpid()}"

        # プロジェクトパス設定
        self.paths = get_project_paths()
        self.project_dir = self.paths["project"]
        self.output_dir = self.paths["output"]
        self.log_dir = self.paths["logs"]

        # ログ設定
        self.logger = setup_logging(
            name=f"{self.__class__.__name__}",
            log_file=self.log_dir / f"{self.worker_type}_worker.log",
        )

        # RabbitMQ関連
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.is_connected = False

        # キュー設定（サブクラスでオーバーライド可能）
        self.input_queue = f"{self.worker_type}_queue"
        self.output_queue = "result_queue"

        # シャットダウン管理
        self.is_running = True
        self.current_task = None

        # メトリクス
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        # プロフェッショナルな初期化ログ
        self.logger.info(
            f"{self.__class__.__name__} initialized (ID: {self.worker_id}, PID: {os.getpid()})"
        )

    def connect(self, retry_count: int = 3, retry_delay: float = 1.0) -> bool:
        """RabbitMQ接続"""
        for attempt in range(retry_count):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host="localhost", heartbeat=600, blocked_connection_timeout=300
                    )
                )
                self.channel = self.connection.channel()

                # キュー宣言
                self._declare_queues()

                self.is_connected = True
                self.logger.info(
                    f"RabbitMQ connection established (attempt: {attempt + 1}/{retry_count})"
                )
                return True

            except pika_exceptions.AMQPConnectionError as e:
                self.logger.warning(
                    f"RabbitMQ connection failed (attempt: {attempt + 1}/{retry_count}): {e}"
                )
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                else:
                    self.logger.error(
                        "RabbitMQ connection failed - max retries reached"
                    )
                    return False
            except Exception as e:
                self.logger.error(f"Unexpected connection error: {e}")
                return False

        return False

    def _declare_queues(self):
        """キュー宣言（サブクラスでオーバーライド可能）"""
        if self.channel:
            # 入力キュー
            self.channel.queue_declare(queue=self.input_queue, durable=True)
            # 出力キュー
            self.channel.queue_declare(queue=self.output_queue, durable=True)
            self.logger.debug(
                f"Queue declared: {self.input_queue}, {self.output_queue}"
            )

    @abstractmethod
    def process_message(self, ch, method, properties, body) -> None:
        """
        メッセージ処理（サブクラスで実装必須）

        Args:
            ch: チャンネル
            method: メソッド
            properties: プロパティ
            body: メッセージ本体
        """
        pass

    def _message_wrapper(self, ch, method, properties, body):
        """メッセージ処理のラッパー（エラーハンドリング等）"""
        task_id = None
        start_time = time.time()

        try:
            # タスクID抽出を試みる
            try:
                message = json.loads(body)
                task_id = message.get("task_id", "unknown")
                self.current_task = task_id
            except:
                task_id = f"raw_message_{int(time.time())}"
                self.current_task = task_id

            self.logger.info(f"Message received: {task_id} (size: {len(body)} bytes)")

            # サブクラスの処理を実行
            self.process_message(ch, method, properties, body)

            # ACK送信
            ch.basic_ack(delivery_tag=method.delivery_tag)

            # 処理時間とメトリクス
            duration = time.time() - start_time
            self.processed_count += 1
            self.logger.info(
                f"Message processed: {task_id} (duration: {duration:.3f}s, total: {self." \
                    "processed_count})"
            )

        except Exception as e:
            self.error_count += 1
            duration = time.time() - start_time
            self.logger.error(
                f"Message processing failed: {task_id} - {type(e).__name__}: {str(e)} " \
                    "(duration: {duration:.3f}s, errors: {self.error_count})"
            )

            if self.logger.isEnabledFor(logging.DEBUG):
                traceback.print_exc()

            # NACK送信（再キュー）
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        finally:
            self.current_task = None

    def send_result(self, result_data: Dict[str, Any]) -> bool:
        """結果キューへの送信"""
        try:
            if not self.channel:
                self.logger.error("Channel not initialized")
                return False

            self.channel.basic_publish(
                exchange="",
                routing_key=self.output_queue,
                body=json.dumps(result_data),
                properties=pika.BasicProperties(delivery_mode=2),  # 永続化
            )

            task_id = result_data.get("task_id", "unknown")
            self.logger.debug(f"Result sent: {task_id} to {self.output_queue}")
            return True

        except Exception as e:
            self.logger.error(f"Result send error: {e}")
            return False

    def _setup_signal_handlers(self):
        """シグナルハンドラーの設定"""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        self.logger.debug("Signal handlers configured")

    def _handle_shutdown(self, signum, frame):
        """シャットダウンシグナルの処理"""
        self.logger.info(f"Shutdown signal received: {signum}")
        self.is_running = False

        if self.current_task:
            self.logger.info(
                f"Waiting for current task to complete: {self.current_task}"
            )

        self.stop()

    def start(self):
        """ワーカー開始"""
        self.logger.info(f"{self.__class__.__name__} starting...")

        if not self.connect():
            self.logger.error("Startup failed: RabbitMQ connection error")
            return

        try:
            # QoS設定
            self.channel.basic_qos(prefetch_count=1)

            # コンシューマー設定
            self.channel.basic_consume(
                queue=self.input_queue, on_message_callback=self._message_wrapper
            )

            self.logger.info(f"Listening on queue: {self.input_queue}")

            # メッセージ処理開始
            self.channel.start_consuming()

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt detected")
            self.stop()
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            traceback.print_exc()
            self.stop()

    def stop(self):
        """ワーカー停止"""
        self.logger.info("Worker stopping...")

        # 実行時間とメトリクスの最終報告
        runtime = time.time() - self.start_time
        if runtime > 0:
            rate = self.processed_count / runtime
            self.logger.info(
                f"Final metrics: processed={self.processed_count}, errors={self.error_count}," \
                    " runtime={runtime:.1f}s, rate={rate:.2f}/s"
            )

        try:
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                self.channel.close()

            if self.connection and self.connection.is_open:
                self.connection.close()

            self.logger.info("Worker stopped successfully")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def handle_error(
        self, error: Exception, operation: str, critical: bool = False
    ) -> None:
        """
        エラーハンドリング

        Args:
            error: 発生したエラー
            operation: 実行中の操作
            critical: クリティカルエラーかどうか
        """
        error_msg = f"[{operation}] {type(error).__name__}: {str(error)}"

        if critical:
            self.logger.error(f"CRITICAL ERROR: {error_msg}")
        else:
            self.logger.warning(f"ERROR: {error_msg}")

        # デバッグモードの場合はトレースバックも出力
        if self.logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()

    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック（サブクラスで拡張可能）"""
        runtime = time.time() - self.start_time
        return {
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "current_task": self.current_task,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.processed_count, 1),
            "runtime_seconds": runtime,
            "timestamp": datetime.now().isoformat(),
        }

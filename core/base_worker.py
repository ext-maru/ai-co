#!/usr/bin/env python3
"""
BaseWorker - Elders Guild ワーカー基底クラス

すべてのワーカーが継承すべき基底クラス。
RabbitMQ接続、ログ設定、シグナルハンドリングなどの共通処理を提供。
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

try:
    import pika
    import pika.exceptions

    pika_exceptions = pika.exceptions
except ImportError:
    # For testing without pika installed
    pika = None

    class MockPikaExceptions:
        class AMQPConnectionError(Exception):
        """MockPikaExceptionsクラス"""
            """AMQPConnectionErrorクラス"""
            pass

    pika_exceptions = MockPikaExceptions()

from .common_utils import get_project_paths, setup_logging
from .error_handler_mixin import ErrorHandlerMixin, ErrorSeverity, with_error_handling


class BaseWorker(ABC, ErrorHandlerMixin):
    """ワーカー基底クラス（統一エラーハンドリング付き）"""

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
        self.input_queue = f"ai_{self.worker_type}"
        self.output_queue = "ai_results"

        # 統計情報
        self.stats = {
            "processed_count": 0,
            "error_count": 0,
            "start_time": time.time(),
            "last_error": None,
        }

        # シャットダウン管理
        self.is_running = True
        self.current_task = None

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        # エラーハンドラー初期化
        ErrorHandlerMixin.__init__(self)

        self.logger.info(f"🚀 {self.__class__.__name__} 初期化完了 (ID: {self.worker_id})")

    def connect(self, retry_count: int = 3, retry_delay: float = 1.0) -> bool:
        """RabbitMQ接続"""
        if pika is None:
            self.logger.warning("pika is not installed, skipping RabbitMQ connection")
            self.is_connected = True  # For testing
            return True

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
                self.logger.info(f"✅ RabbitMQ接続成功 (試行: {attempt + 1}/{retry_count})")
                return True

            except pika_exceptions.AMQPConnectionError as e:
                self.logger.warning(
                    f"RabbitMQ接続失敗 (試行: {attempt + 1}/{retry_count}): {e}"
                )
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                else:
                    self.logger.error("❌ RabbitMQ接続失敗 - 最大試行回数に到達")
                    return False
            except Exception as e:
                self.logger.error(f"予期しない接続エラー: {e}")
                return False

        return False

    def _declare_queues(self):
        """キュー宣言（サブクラスでオーバーライド可能）"""
        if self.channel:
            # 既存のキューに合わせてx-max-priorityを設定
            queue_args = {"x-max-priority": 10}

            # 入力キュー
            self.channel.queue_declare(
                queue=self.input_queue, durable=True, arguments=queue_args
            )
            # 出力キュー
            self.channel.queue_declare(
                queue=self.output_queue, durable=True, arguments=queue_args
            )
            self.logger.debug(f"キュー宣言完了: {self.input_queue}, {self.output_queue}")

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
        try:
            # タスクID抽出を試みる
            try:
                message = json.loads(body)
                task_id = message.get("task_id", "unknown")
                self.current_task = task_id
            except:
                task_id = "raw_message"
                self.current_task = task_id

            self.logger.info(f"📨 メッセージ受信: {task_id}")

            # サブクラスの処理を実行
            self.process_message(ch, method, properties, body)

            # ACK送信
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.info(f"✅ メッセージ処理完了: {task_id}")

        except Exception as e:
            self.logger.error(f"❌ メッセージ処理エラー ({task_id}): {e}")
            traceback.print_exc()

            # NACK送信（再キュー）
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        finally:
            self.current_task = None

    def send_result(self, result_data: Dict[str, Any]) -> bool:
        """結果キューへの送信"""
        try:
            if not self.channel:
                self.logger.error("チャンネルが初期化されていません")
                return False

            self.channel.basic_publish(
                exchange="",
                routing_key=self.output_queue,
                body=json.dumps(result_data),
                properties=pika.BasicProperties(delivery_mode=2),  # 永続化
            )

            self.logger.debug(f"結果送信完了: {result_data.get('task_id', 'unknown')}")
            return True

        except Exception as e:
            self.logger.error(f"結果送信エラー: {e}")
            return False

    def _setup_signal_handlers(self)signal.signal(signal.SIGTERM, self._handle_shutdown)
    """シグナルハンドラーの設定"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        self.logger.debug("シグナルハンドラー設定完了")

    def _handle_shutdown(self, signum, frame)self.logger.info(f"📤 シャットダウンシグナル受信: {signum}")
    """シャットダウンシグナルの処理"""
        self.is_running = False

        if self.current_task:
            self.logger.info(f"⏳ 現在のタスク完了を待機中: {self.current_task}")
            # タスク完了を待つ処理はサブクラスで実装

        self.stop()

    def start(self)self.logger.info(f"🚀 {self.__class__.__name__} 起動中...")
    """ワーカー開始"""

        if not self.connect():
            self.logger.error("起動失敗: RabbitMQ接続エラー")
            return

        try:
            # QoS設定
            self.channel.basic_qos(prefetch_count=1)

            # コンシューマー設定
            self.channel.basic_consume(
                queue=self.input_queue, on_message_callback=self._message_wrapper
            )

            self.logger.info(f"👂 {self.input_queue} を監視中...")

            # メッセージ処理開始
            self.channel.start_consuming()

        except KeyboardInterrupt:
            self.logger.info("⌨️ キーボード割り込み検出")
            self.stop()
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            traceback.print_exc()
            self.stop()

    def stop(self)self.logger.info("🛑 ワーカー停止中...")
    """ワーカー停止（改善版：Bad File Descriptor対策）"""

        # フラグ設定（他のメソッドでの操作を停止）
        self.is_running = False

        try:
            # 1.0 チャンネルの停止（順序重要）
            if self.channel:
                try:
                    if hasattr(self.channel, "is_open") and self.channel.is_open:
                        self.channel.stop_consuming()
                except Exception as e:
                    # 既に停止済みの場合は無視
                    if "Bad file descriptor" not in str(e):
                        self.logger.debug(f"チャンネル停止時の警告: {e}")

                try:
                    if (
                        hasattr(self.channel, "is_closed")
                        and not self.channel.is_closed
                    ):
                        self.channel.close()
                except Exception as e:
                    # ファイルディスクリプタエラーを抑制
                    if "Bad file descriptor" not in str(e):
                        self.logger.debug(f"チャンネルクローズ時の警告: {e}")

                self.channel = None

            # 2.0 コネクションの停止
            if self.connection:
                try:
                    if (
                        hasattr(self.connection, "is_closed")
                        and not self.connection.is_closed
                    ):
                        self.connection.close()
                except Exception as e:
                    # ファイルディスクリプタエラーを抑制
                    if "Bad file descriptor" not in str(e):
                        self.logger.debug(f"コネクションクローズ時の警告: {e}")

                self.connection = None

            self.is_connected = False
            self.logger.info("👋 ワーカー停止完了")

        except Exception as e:
            # 予期しないエラーのみログ出力
            if "Bad file descriptor" not in str(e):
                self.logger.error(f"停止中のエラー: {e}")
            else:
                self.logger.debug(f"ファイルディスクリプタ警告（正常）: {e}")

    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        severity: str = ErrorSeverity.MEDIUM,
        retry_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        統一エラーハンドリング（ErrorHandlerMixinをオーバーライド）

        Args:
            error: 発生したエラー
            context: エラーコンテキスト情報
            severity: エラー深刻度
            retry_callback: リトライ時に実行する関数
        """
        # Slack通知設定
        try:
            from libs.slack_notifier import SlackNotifier

            if not hasattr(self, "slack_notifier"):
                self.slack_notifier = SlackNotifier()
        except:
            pass

        # 統計情報を更新
        self.stats["error_count"] += 1
        self.stats["last_error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": time.time(),
        }

        # ErrorHandlerMixinの統一処理を呼び出し
        return ErrorHandlerMixin.handle_error(
            self, error, context, severity, retry_callback
        )

    def health_check(self) -> Dict[str, Any]uptime = time.time() - self.stats["start_time"]
    """ヘルスチェック（サブクラスで拡張可能）"""
        return {:
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "status": "healthy" if self.is_running else "stopped",
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "current_task": self.current_task,
            "uptime": uptime,
            "stats": self.stats.copy(),
            "timestamp": datetime.now().isoformat(),
        }

    def run(self)self.logger.warning("⚠️ run()は非推奨です。start()を使用してください。")
    """start()メソッドのエイリアス（後方互換性のため）"""
        return self.start()

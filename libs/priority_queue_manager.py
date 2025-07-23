"""
Priority Queue Manager for API Rate Limiting
API制限時の優先度付きキュー管理システム
"""

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue
from typing import Any, Dict, List, Optional

import pika


class TaskPriority(Enum):
    """TaskPriorityクラス"""
    CRITICAL = 1  # システム重要タスク
    HIGH = 3  # 緊急性高
    NORMAL = 5  # 通常
    LOW = 7  # 低優先度
    BACKGROUND = 9  # バックグラウンド


class TaskStatus(Enum):
    """TaskStatusクラス"""
    QUEUED = "queued"
    PROCESSING = "processing"
    RATE_LIMITED = "rate_limited"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class QueuedTask:
    """QueuedTaskクラス"""
    task_id: str
    priority: int
    prompt: str
    task_type: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None
    original_queue: str = "ai_tasks"
    requester: str = "unknown"

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.metadata is None:
            self.metadata = {}
        if self.expires_at is None:
            # デフォルト有効期限: 24時間
            self.expires_at = self.created_at + timedelta(hours=24)

    def __lt__(self, other):
        """__lt__特殊メソッド"""
        # 優先度による比較（数値が小さいほど高優先度）
        if self.priority != other.priority:
            return self.priority < other.priority
        # 優先度が同じ場合は作成日時順
        return self.created_at < other.created_at

    def is_expired(self) -> bool:
        """expired判定メソッド"""
        return datetime.now() > self.expires_at

    def can_retry(self) -> bool:
        """retry可能性判定メソッド"""
        return self.retry_count < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["expires_at"] = self.expires_at.isoformat() if self.expires_at else None
        return data


class PriorityQueueManager:
    """
    API制限時の優先度付きキュー管理
    """

    def __init__(self, config_path: str = None):
        """初期化メソッド"""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)

        # 優先度別キュー
        self.priority_queues = {priority: PriorityQueue() for priority in TaskPriority}

        # タスク状態管理
        self.task_status: Dict[str, TaskStatus] = {}
        self.processing_tasks: Dict[str, QueuedTask] = {}
        self.failed_tasks: List[QueuedTask] = []

        # 統計情報
        self.stats = {
            "total_queued": 0,
            "total_processed": 0,
            "total_failed": 0,
            "rate_limited_count": 0,
            "last_reset": datetime.now(),
        }

        # RabbitMQ接続
        self.connection = None
        self.channel = None
        self._setup_rabbitmq()

        # バックグラウンドタスク
        self.cleanup_thread = None
        self.processor_thread = None
        self.running = False

    def _load_config(self, config_path: str) -> Dict:
        """設定読み込み"""
        default_config = {
            "rate_limit_handling": {
                "enabled": True,
                "queue_size_limit": 1000,
                "cleanup_interval": 300,  # 5分
                "processing_interval": 1,  # 1秒
                "retry_delay_multiplier": 2,
                "max_processing_time": 600,  # 10分
            },
            "priority_thresholds": {
                "critical_queue_size": 10,
                "high_queue_size": 50,
                "normal_queue_size": 200,
            },
        }

        if config_path:
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                    return file_config.get("queue_management", default_config)
            except Exception as e:
                self.logger.warning(f"設定ファイル読み込み失敗: {e}")

        return default_config

    def _setup_rabbitmq(self):
        """RabbitMQ接続セットアップ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()

            # 制限時用キューを宣言
            self.channel.queue_declare(queue="rate_limited_tasks", durable=True)
            self.channel.queue_declare(queue="priority_retry_tasks", durable=True)

            self.logger.info("RabbitMQ接続成功 - Priority Queue Manager")

        except Exception as e:
            self.logger.error(f"RabbitMQ接続失敗: {e}")
            self.connection = None
            self.channel = None

    def add_task(
        self,
        task_id: str,
        prompt: str,
        priority: int = TaskPriority.NORMAL.value,
        task_type: str = "general",
        requester: str = "unknown",
        metadata: Dict[str, Any] = None,
        expires_in_hours: int = 24,
    ) -> bool:
        """タスクをキューに追加"""

        try:
            # 優先度を正規化
            priority_enum = None
            for p in TaskPriority:
                if p.value == priority:
                    priority_enum = p
                    break

            if priority_enum is None:
                priority_enum = TaskPriority.NORMAL

            # キューサイズ制限チェック
            current_size = self.get_queue_size()
            max_size = self.config["rate_limit_handling"]["queue_size_limit"]

            if current_size >= max_size:
                self.logger.warning(f"キューサイズ制限到達: {current_size}/{max_size}")
                # 低優先度タスクを削除して空きを作る
                if not self._make_room_for_task(priority_enum):
                    return False

            # タスク作成
            task = QueuedTask(
                task_id=task_id,
                priority=priority,
                prompt=prompt,
                task_type=task_type,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=expires_in_hours),
                requester=requester,
                metadata=metadata or {},
            )

            # 優先度別キューに追加
            self.priority_queues[priority_enum].put(task)
            self.task_status[task_id] = TaskStatus.QUEUED
            self.stats["total_queued"] += 1

            self.logger.info(
                f"タスクキュー追加: {task_id} (優先度: {priority_enum.name})"
            )
            return True

        except Exception as e:
            self.logger.error(f"タスクキュー追加失敗: {e}")
            return False

    def _make_room_for_task(self, new_task_priority: TaskPriority) -> bool:
        """新しいタスクのためにキューの空きを作る"""

        # 新しいタスクより低い優先度のキューから削除
        for priority in reversed(list(TaskPriority)):
            if priority.value > new_task_priority.value:  # より低い優先度
                queue = self.priority_queues[priority]
                if not queue.empty():
                    removed_task = queue.get()
                    self.task_status[removed_task.task_id] = TaskStatus.EXPIRED
                    self.logger.info(f"低優先度タスクを削除: {removed_task.task_id}")
                    return True

        return False

    def get_next_task(self) -> Optional[QueuedTask]:
        """次に処理すべきタスクを取得"""

        for priority in TaskPriority:
            queue = self.priority_queues[priority]

            # 有効な（期限切れでない）タスクを探す
            temp_tasks = []

            while not queue.empty():
                task = queue.get()

                if task.is_expired():
                    self.task_status[task.task_id] = TaskStatus.EXPIRED
                    self.logger.debug(f"期限切れタスクをスキップ: {task.task_id}")
                    continue

                # 有効なタスクが見つかった
                # 一時的に取り出したタスクを戻す
                for temp_task in temp_tasks:
                    queue.put(temp_task)

                self.task_status[task.task_id] = TaskStatus.PROCESSING
                self.processing_tasks[task.task_id] = task

                return task

            # 期限切れタスクのみだった場合、戻さない

        return None

    def mark_task_completed(self, task_id: str, success: bool = True):
        """タスク完了マーク"""

        if task_id in self.processing_tasks:
            task = self.processing_tasks.pop(task_id)

            if success:
                self.task_status[task_id] = TaskStatus.COMPLETED
                self.stats["total_processed"] += 1
                self.logger.info(f"タスク完了: {task_id}")
            else:
                self._handle_task_failure(task)

    def mark_task_rate_limited(self, task_id: str):
        """タスクをレート制限状態としてマーク"""

        if task_id in self.processing_tasks:
            task = self.processing_tasks.pop(task_id)
            task.retry_count += 1

            if task.can_retry():
                # リトライ可能な場合は優先度を上げてキューに戻す
                retry_priority = max(1, task.priority - 1)  # 優先度を1つ上げる

                # リトライ遅延
                delay_seconds = (2**task.retry_count) * self.config[
                    "rate_limit_handling"
                ]["retry_delay_multiplier"]
                task.created_at = datetime.now() + timedelta(seconds=delay_seconds)

                # 優先度に対応するキューに戻す
                for priority_enum in TaskPriority:
                    if priority_enum.value == retry_priority:
                        self.priority_queues[priority_enum].put(task)
                        break

                self.task_status[task_id] = TaskStatus.RATE_LIMITED
                self.stats["rate_limited_count"] += 1

                self.logger.info(
                    f"レート制限によりリトライキュー追加: {task_id} (試行 {task.retry_count}/{task.max_retries})"
                )
            else:
                # リトライ上限に達した場合
                self._handle_task_failure(task)

    def _handle_task_failure(self, task: QueuedTask):
        """タスク失敗処理"""

        self.task_status[task.task_id] = TaskStatus.FAILED
        self.failed_tasks.append(task)
        self.stats["total_failed"] += 1

        self.logger.warning(
            f"タスク失敗: {task.task_id} (試行回数: {task.retry_count})"
        )

        # 失敗したタスクをDead Letter Queueに送信
        if self.channel:
            try:
                self.channel.basic_publish(
                    exchange="",
                    routing_key="dead_letter_queue",
                    body=json.dumps(task.to_dict()),
                    properties=pika.BasicProperties(delivery_mode=2),
                )
            except Exception as e:
                self.logger.error(f"Dead Letter Queue送信失敗: {e}")

    def get_queue_status(self) -> Dict[str, Any]:
        """キュー状態取得"""

        queue_sizes = {}
        for priority in TaskPriority:
            queue_sizes[priority.name] = self.priority_queues[priority].qsize()

        return {
            "queue_sizes": queue_sizes,
            "total_queued": sum(queue_sizes.values()),
            "processing_count": len(self.processing_tasks),
            "failed_count": len(self.failed_tasks),
            "statistics": self.stats.copy(),
            "last_update": datetime.now().isoformat(),
        }

    def get_queue_size(self) -> int:
        """総キューサイズ取得"""
        return sum(queue.qsize() for queue in self.priority_queues.values())

    def start_background_processing(self):
        """バックグラウンド処理開始"""

        if self.running:
            return

        self.running = True

        # クリーンアップスレッド
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()

        self.logger.info("Priority Queue Manager バックグラウンド処理開始")

    def stop_background_processing(self):
        """バックグラウンド処理停止"""

        self.running = False

        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)

        self.logger.info("Priority Queue Manager バックグラウンド処理停止")

    def _cleanup_worker(self):
        """定期クリーンアップワーカー"""

        cleanup_interval = self.config["rate_limit_handling"]["cleanup_interval"]

        while self.running:
            try:
                self._cleanup_expired_tasks()
                self._cleanup_stale_processing_tasks()
                time.sleep(cleanup_interval)
            except Exception as e:
                self.logger.error(f"クリーンアップエラー: {e}")
                time.sleep(60)  # エラー時は1分待機

    def _cleanup_expired_tasks(self):
        """期限切れタスクのクリーンアップ"""

        expired_count = 0

        for priority in TaskPriority:
            queue = self.priority_queues[priority]
            temp_tasks = []

            while not queue.empty():
                task = queue.get()
                if not task.is_expired():
                    temp_tasks.append(task)
                else:
                    self.task_status[task.task_id] = TaskStatus.EXPIRED
                    expired_count += 1

            # 有効なタスクを戻す
            for task in temp_tasks:
                queue.put(task)

        if expired_count > 0:
            self.logger.info(f"期限切れタスククリーンアップ: {expired_count}件")

    def _cleanup_stale_processing_tasks(self):
        """処理中で停止したタスクのクリーンアップ"""

        max_processing_time = self.config["rate_limit_handling"]["max_processing_time"]
        cutoff_time = datetime.now() - timedelta(seconds=max_processing_time)

        stale_tasks = []

        for task_id, task in self.processing_tasks.items():
            if task.created_at < cutoff_time:
                stale_tasks.append(task_id)

        for task_id in stale_tasks:
            task = self.processing_tasks.pop(task_id)
            self.logger.warning(f"停止処理タスクを再キュー: {task_id}")

            # 優先度を下げて再キューイング
            retry_priority = min(9, task.priority + 1)
            for priority_enum in TaskPriority:
                if priority_enum.value == retry_priority:
                    self.priority_queues[priority_enum].put(task)
                    break

            self.task_status[task_id] = TaskStatus.QUEUED

    def clear_queues(self, priority: Optional[TaskPriority] = None):
        """キューのクリア"""

        if priority:
            # 特定優先度のみクリア
            queue = self.priority_queues[priority]
            cleared_count = queue.qsize()

            while not queue.empty():
                task = queue.get()
                self.task_status[task.task_id] = TaskStatus.EXPIRED

            self.logger.info(f"{priority.name}キューをクリア: {cleared_count}件")
        else:
            # 全キュークリア
            total_cleared = 0

            for priority_enum in TaskPriority:
                queue = self.priority_queues[priority_enum]
                cleared_count = queue.qsize()
                total_cleared += cleared_count

                while not queue.empty():
                    task = queue.get()
                    self.task_status[task.task_id] = TaskStatus.EXPIRED

            self.logger.info(f"全キューをクリア: {total_cleared}件")

    def close(self):
        """リソースのクリーンアップ"""

        self.stop_background_processing()

        if self.connection and not self.connection.is_closed:
            self.connection.close()

        self.logger.info("Priority Queue Manager 終了")

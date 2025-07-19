#!/usr/bin/env python3
"""
Task Tracker Client
pm_workerから使用するTask Tracker連携クライアント
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from core import EMOJI, BaseManager, get_config
from libs.rabbit_manager import RabbitManager

logger = logging.getLogger(__name__)


class TaskTrackerClient(BaseManager):
    """Task Tracker連携クライアント"""

    def __init__(self):
        super().__init__(manager_name="task_tracker_client")
        self.db_path = PROJECT_ROOT / "data" / "tasks.db"
        self.rabbit_manager = RabbitManager()
        self.initialize()

    def initialize(self) -> bool:
        """初期化処理（BaseManager抽象メソッドの実装）"""
        try:
            # データディレクトリの作成
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # データベースの初期化
            if not self.db_path.exists():
                self._create_database()

            self.logger.info("TaskTrackerClient initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"TaskTrackerClient initialization failed: {e}")
            return False

    def _create_database(self):
        """データベースの作成"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            priority INTEGER,
            status TEXT DEFAULT 'pending',
            assignee TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
        )
        conn.commit()
        conn.close()

    def create_task(
        self,
        task_id: str,
        title: str,
        description: str = "",
        priority: int = 3,
        assignee: str = "pm",
    ) -> str:
        """タスク作成（同期的にデータベースへ直接書き込み）"""
        try:
            # RabbitMQ経由でTask Trackerへ送信
            message = {
                "action": "create_task",
                "title": f"[{task_id}] {title}",
                "description": description,
                "priority": priority,
                "assignee": assignee,
                "timestamp": datetime.now().isoformat(),
            }

            self.rabbit_manager.publish_message(
                "task_tracker", message, priority=priority
            )

            logger.info(f"{EMOJI['check']} タスク作成: {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"タスク作成エラー: {e}")
            return None

    def update_task_status(self, task_id: str, status: str, notes: str = ""):
        """タスクステータス更新"""
        try:
            message = {
                "action": "update_status",
                "task_id": task_id,
                "status": status,
                "notes": notes,
                "timestamp": datetime.now().isoformat(),
            }

            self.rabbit_manager.publish_message("task_tracker", message, priority=5)

            logger.info(f"{EMOJI['check']} ステータス更新: {task_id} → {status}")

        except Exception as e:
            logger.error(f"ステータス更新エラー: {e}")

    def get_task_by_original_id(self, original_task_id: str) -> Optional[Dict]:
        """元のタスクIDでタスクを検索"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # タイトルに元のタスクIDが含まれているタスクを検索
            cursor.execute(
                """
            SELECT * FROM tasks
            WHERE title LIKE ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
                (f"%[{original_task_id}]%",),
            )

            task = cursor.fetchone()
            conn.close()

            if task:
                return dict(task)
            return None

        except Exception as e:
            logger.error(f"タスク検索エラー: {e}")
            return None

    def create_pm_task(self, task_data: Dict) -> str:
        """PMワーカーのタスクを作成"""
        task_id = task_data.get(
            "task_id", f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        task_type = task_data.get("task_type", "general")
        prompt = task_data.get("prompt", "")[:100]  # 最初の100文字

        # 優先度の決定
        priority = 3  # デフォルト
        if "urgent" in prompt.lower() or "緊急" in prompt:
            priority = 5
        elif "high" in prompt.lower() or "重要" in prompt:
            priority = 4

        return self.create_task(
            task_id=task_id,
            title=f"{task_type.upper()}: {prompt}",
            description=task_data.get("prompt", ""),
            priority=priority,
            assignee="pm",
        )

    def update_pm_task_status(
        self, task_id: str, status: str, result_data: Dict = None
    ):
        """PMワーカーのタスクステータスを更新"""
        # ステータスマッピング
        status_map = {
            "processing": "in_progress",
            "completed": "review",
            "error": "cancelled",
            "success": "completed",
        }

        tracker_status = status_map.get(status, "in_progress")

        # ノート作成
        notes = f"Status: {status}"
        if result_data:
            if result_data.get("error"):
                notes += f" | Error: {result_data['error']}"
            if result_data.get("files_created"):
                notes += f" | Files: {len(result_data['files_created'])}"

        # 元のタスクIDでタスクを検索
        task = self.get_task_by_original_id(task_id)
        if task:
            self.update_task_status(task["id"], tracker_status, notes)
        else:
            logger.warning(f"タスクが見つかりません: {task_id}")

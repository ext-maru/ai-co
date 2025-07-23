#!/usr/bin/env python3
"""
Claude Task Tracker - エルダーズギルド タスク管理システム
タスク賢者の実装 - タスクの管理、追跡、分析を担当
"""

import asyncio
import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# タスクステータス定義
class TaskStatus(Enum):
    """TaskStatusクラス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVIEW = "review"
    BLOCKED = "blocked"


# タスク優先度定義
class TaskPriority(Enum):
    """TaskPriorityクラス"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# タスクタイプ定義
class TaskType(Enum):
    """TaskTypeクラス"""
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class ClaudeTaskTracker:
    """Claude タスクトラッカー - タスク賢者の実装"""

    def __init__(self, db_path: Optional[str] = None, use_postgres: bool = False):
        """
        初期化

        Args:
            db_path: SQLiteデータベースパス（省略時はデフォルト）
            use_postgres: PostgreSQL使用フラグ（将来実装）
        """
        self.use_postgres = use_postgres

        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = (
                Path(__file__).parent.parent / "data" / "claude_task_tracker.db"
            )

        # データディレクトリ作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # データベース初期化
        self._init_database()

        # タスク実行ロック（同時実行制御）
        self._task_locks = {}

        logger.info(f"Claude Task Tracker initialized (DB: {self.db_path})")

    def _init_database(self):
        """データベース初期化"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # タスクテーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_by TEXT,
                    assigned_to TEXT,
                    estimated_duration_minutes INTEGER,
                    actual_duration_minutes INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    due_date TEXT,
                    tags TEXT,
                    metadata TEXT,
                    context TEXT,
                    progress REAL DEFAULT 0.0,
                    result TEXT,
                    error_message TEXT
                )
            """
            )

            # 依存関係テーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    depends_on_task_id TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'completion',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id),
                    FOREIGN KEY (depends_on_task_id) REFERENCES tasks (task_id)
                )
            """
            )

            # 実行履歴テーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS task_executions (
                    execution_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    log_entries TEXT,
                    error_messages TEXT,
                    execution_context TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            """
            )

            # インデックス作成
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)"
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """データベース接続コンテキストマネージャー"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_task(
        self,
        title: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        description: str = "",
        created_by: str = "claude_elder",
        assigned_to: Optional[str] = None,
        estimated_duration_minutes: Optional[int] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> str:
        """
        新規タスク作成

        Args:
            title: タスクタイトル
            task_type: タスクタイプ
            priority: 優先度
            description: 詳細説明
            created_by: 作成者
            assigned_to: 担当者
            estimated_duration_minutes: 推定時間（分）
            due_date: 期限
            tags: タグリスト
            metadata: メタデータ
            context: 実行コンテキスト

        Returns:
            task_id: 作成されたタスクID
        """
        task_id = f"task_{uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (
                    task_id, title, description, task_type, priority, status,
                    created_by, assigned_to, estimated_duration_minutes,
                    created_at, updated_at, due_date, tags, metadata, context, progress
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    title,
                    description,
                    task_type.value,
                    priority.value,
                    TaskStatus.PENDING.value,
                    created_by,
                    assigned_to,
                    estimated_duration_minutes,
                    now,
                    now,
                    due_date.isoformat() if due_date else None,
                    json.dumps(tags) if tags else None,
                    json.dumps(metadata) if metadata else None,
                    json.dumps(context) if context else None,
                    0.0,
                ),
            )
            conn.commit()

        logger.info(f"タスク作成: {task_id} - {title}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict]:
        """タスク取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
        return None

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
        result: Optional[Dict] = None,
    ) -> bool:
        """タスクステータス更新"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 現在のタスク情報取得
            cursor.execute(
                "SELECT status, started_at FROM tasks WHERE task_id = ?", (task_id,)
            )
            current = cursor.fetchone()
            if not current:
                return False

            # 更新値準備
            updates = {"status": status.value, "updated_at": now}

            # ステータスに応じた処理
            if status == TaskStatus.IN_PROGRESS and not current["started_at"]:
                updates["started_at"] = now
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                updates["completed_at"] = now
                # 実際の所要時間計算
                if current["started_at"]:
                    started = datetime.fromisoformat(current["started_at"])
                    duration = int((datetime.now() - started).total_seconds() / 60)
                    updates["actual_duration_minutes"] = duration

            if progress is not None:
                updates["progress"] = progress
            if error_message:
                updates["error_message"] = error_message
            if result:
                updates["result"] = json.dumps(result)

            # SQL文構築
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [task_id]

            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE task_id = ?", values)
            conn.commit()

        logger.info(f"タスクステータス更新: {task_id} -> {status.value}")
        return True

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """タスクリスト取得"""
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status.value)
        if priority:
            conditions.append("priority = ?")
            params.append(priority.value)
        if assigned_to:
            conditions.append("assigned_to = ?")
            params.append(assigned_to)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM tasks
                {where_clause}
                ORDER BY
                    CASE priority
                        WHEN '{TaskPriority.CRITICAL.value}' THEN 1
                        WHEN '{TaskPriority.HIGH.value}' THEN 2
                        WHEN '{TaskPriority.MEDIUM.value}' THEN 3
                        WHEN '{TaskPriority.LOW.value}' THEN 4
                    END,
                    created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def add_dependency(
        self, task_id: str, depends_on_task_id: str, dependency_type: str = "completion"
    ) -> bool:
        """タスク依存関係追加"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO task_dependencies (
                        task_id, depends_on_task_id, dependency_type, created_at
                    ) VALUES (?, ?, ?, ?)
                """,
                    (task_id, depends_on_task_id, dependency_type, now),
                )
                conn.commit()
                logger.info(f"依存関係追加: {task_id} -> {depends_on_task_id}")
                return True
            except sqlite3.IntegrityError:
                logger.warning(f"依存関係追加失敗: {task_id} -> {depends_on_task_id}")
                return False

    def get_task_dependencies(self, task_id: str) -> List[str]:
        """タスクの依存関係取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT depends_on_task_id FROM task_dependencies WHERE task_id = ?",
                (task_id,),
            )
            return [row["depends_on_task_id"] for row in cursor.fetchall()]

    def record_execution(
        self,
        task_id: str,
        execution_id: Optional[str] = None,
        status: str = "started",
        log_entries: Optional[List[str]] = None,
        error_messages: Optional[List[str]] = None,
        execution_context: Optional[Dict] = None,
    ) -> str:
        """タスク実行記録"""
        if not execution_id:
            execution_id = f"exec_{uuid4().hex[:8]}"

        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 既存のexecution_idをチェック（更新の場合）
            cursor.execute(
                "SELECT execution_id FROM task_executions WHERE execution_id = ?",
                (execution_id,),
            )
            existing = cursor.fetchone()

            if existing:
                # 更新
                updates = {
                    "status": status,
                    "completed_at": now if status in ["completed", "failed"] else None,
                }
                if log_entries:
                    updates["log_entries"] = json.dumps(log_entries)
                if error_messages:
                    updates["error_messages"] = json.dumps(error_messages)

                set_clause = ", ".join(
                    [f"{k} = ?" for k in updates.keys() if updates[k] is not None]
                )
                values = [v for v in updates.values() if v is not None] + [execution_id]

                cursor.execute(
                    f"UPDATE task_executions SET {set_clause} WHERE execution_id = ?",
                    values,
                )
            else:
                # 新規作成
                cursor.execute(
                    """
                    INSERT INTO task_executions (
                        execution_id, task_id, started_at, status,
                        log_entries, error_messages, execution_context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        execution_id,
                        task_id,
                        now,
                        status,
                        json.dumps(log_entries) if log_entries else None,
                        json.dumps(error_messages) if error_messages else None,
                        json.dumps(execution_context) if execution_context else None,
                    ),
                )

            conn.commit()

        return execution_id

    def get_task_statistics(self) -> Dict[str, Any]:
        """タスク統計情報取得"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ステータス別集計
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            """
            )
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

            # 優先度別集計
            cursor.execute(
                """
                SELECT priority, COUNT(*) as count
                FROM tasks
                GROUP BY priority
            """
            )
            priority_counts = {
                row["priority"]: row["count"] for row in cursor.fetchall()
            }

            # 今日のタスク
            today = datetime.now().date().isoformat()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM tasks
                WHERE DATE(created_at) = ?
            """,
                (today,),
            )
            today_count = cursor.fetchone()["count"]

            # 平均完了時間
            cursor.execute(
                """
                SELECT AVG(actual_duration_minutes) as avg_duration
                FROM tasks
                WHERE status = ? AND actual_duration_minutes IS NOT NULL
            """,
                (TaskStatus.COMPLETED.value,),
            )
            avg_duration = cursor.fetchone()["avg_duration"] or 0

            return {
                "total_tasks": sum(status_counts.values()),
                "status_counts": status_counts,
                "priority_counts": priority_counts,
                "today_created": today_count,
                "average_completion_minutes": round(avg_duration, 2),
                "active_tasks": status_counts.get(TaskStatus.IN_PROGRESS.value, 0),
                "pending_tasks": status_counts.get(TaskStatus.PENDING.value, 0),
                "completed_tasks": status_counts.get(TaskStatus.COMPLETED.value, 0),
            }

    def _row_to_dict(self, row) -> Dict:
        """SQLiteRowを辞書に変換"""
        d = dict(row)
        # JSON文字列をパース
        for field in ["tags", "metadata", "context", "result"]:
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    pass
        return d

    # Todo互換メソッド
    def sync_with_todo_list(self, todos: List[Dict]) -> int:
        """
        TodoListとの同期

        Args:
            todos: TodoWriteで管理されているタスクリスト

        Returns:
            同期されたタスク数
        """
        synced_count = 0

        for todo in todos:
            # 既存タスクチェック
            existing = self.get_task(todo["id"])

            if not existing:
                # 新規作成
                task_type = TaskType.FEATURE  # デフォルト
                if "fix" in todo["content"].lower() or "修正" in todo["content"]:
                    task_type = TaskType.BUG_FIX
                elif "refactor" in todo["content"].lower():
                    task_type = TaskType.REFACTOR

                priority_map = {
                    "high": TaskPriority.HIGH,
                    "medium": TaskPriority.MEDIUM,
                    "low": TaskPriority.LOW,
                }

                self.create_task(
                    title=todo["content"],
                    task_type=task_type,
                    priority=priority_map.get(todo["priority"], TaskPriority.MEDIUM),
                    created_by="todo_sync",
                )
                synced_count += 1
            else:
                # ステータス同期
                status_map = {
                    "pending": TaskStatus.PENDING,
                    "in_progress": TaskStatus.IN_PROGRESS,
                    "completed": TaskStatus.COMPLETED,
                }
                if todo["status"] in status_map:
                    self.update_task_status(todo["id"], status_map[todo["status"]])
                    synced_count += 1

        logger.info(f"TodoList同期完了: {synced_count}件")
        return synced_count


# シングルトンインスタンス
_instance = None


def get_task_tracker(
    db_path: Optional[str] = None, use_postgres: bool = False
) -> ClaudeTaskTracker:
    """タスクトラッカーのシングルトンインスタンス取得"""
    global _instance
    if _instance is None:
        _instance = ClaudeTaskTracker(db_path=db_path, use_postgres=use_postgres)
    return _instance


# エクスポート
__all__ = [
    "ClaudeTaskTracker",
    "get_task_tracker",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
]

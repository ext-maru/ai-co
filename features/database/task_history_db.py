#!/usr/bin/env python3
"""
RAG履歴管理 - PostgreSQL統合システム（Elders Guild Unified）
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# PostgreSQL統合システムを使用
from .postgresql_task_history import TaskHistoryDBCompat as TaskHistoryDB

logger = logging.getLogger(__name__)


# 後方互換性のための元クラス定義（非推奨）
class TaskHistoryDBLegacy:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DB_FILE

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _init_tables(self):
        """テーブル作成"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    worker TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    summary TEXT,
                    status TEXT DEFAULT 'completed',
                    task_type TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_id ON task_history(task_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON task_history(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_worker ON task_history(worker)"
            )

    def save_task(
        self,
        task_id,
        worker,
        model,
        prompt,
        response,
        summary=None,
        status="completed",
        task_type="general",
    ):
        """タスク履歴を保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO task_history
                    (task_id, worker, model, prompt, response, summary, status, task_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        worker,
                        model,
                        prompt,
                        response,
                        summary,
                        status,
                        task_type,
                        datetime.now(),
                        datetime.now(),
                    ),
                )
                logger.info(f"タスク履歴保存成功: {task_id}")
                return True
        except Exception as e:
            logger.error(f"タスク履歴保存失敗: {e}")
            return False

    def update_summary(self, task_id, summary):
        """要約を更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE task_history
                    SET summary = ?, updated_at = ?
                    WHERE task_id = ?
                """,
                    (summary, datetime.now(), task_id),
                )
                logger.info(f"要約更新成功: {task_id}")
                return True
        except Exception as e:
            logger.error(f"要約更新失敗: {e}")
            return False

    def search_tasks(self, keyword=None, worker=None, limit=10):
        """タスク検索"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM task_history WHERE 1=1"
                params = []

                if keyword:
                    query += " AND (prompt LIKE ? OR response LIKE ? OR summary LIKE ?)"
                    params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

                if worker:
                    query += " AND worker = ?"
                    params.append(worker)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"タスク検索失敗: {e}")
            return []

    def get_recent_tasks(self, limit=10):
        """最新タスク取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM task_history
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"最新タスク取得失敗: {e}")
            return []

    def get_stats(self):
        """統計情報取得（修正版）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_tasks,
                        COUNT(DISTINCT worker) as unique_workers,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                        COUNT(CASE WHEN summary IS NOT NULL THEN 1 END) as summarized_tasks
                    FROM task_history
                """
                )
                row = cursor.fetchone()
                return {
                    "total_tasks": row[0],
                    "unique_workers": row[1],
                    "completed_tasks": row[2],
                    "failed_tasks": row[3],
                    "summarized_tasks": row[4],
                }
        except Exception as e:
            logger.error(f"統計情報取得失敗: {e}")
            return {}

    def get_task_by_id(self, task_id):
        """タスクIDで検索"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM task_history
                    WHERE task_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (task_id,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"タスクID検索失敗: {e}")
            return None

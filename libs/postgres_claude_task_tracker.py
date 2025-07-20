#!/usr/bin/env python3
"""
PostgreSQL Claude Task Tracker - エルダーズギルド タスク管理システム
タスク賢者のPostgreSQL実装 - 高性能・高信頼性タスク管理

改修版: 新しい接続マネージャーを使用してasyncio問題を解決
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.postgresql_asyncio_connection_manager import (
    EventLoopSafeWrapper,
    PostgreSQLConnectionManager,
    get_postgres_manager,
)

logger = logging.getLogger(__name__)


# タスクステータス定義
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVIEW = "review"
    BLOCKED = "blocked"


# タスク優先度定義
class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# タスクタイプ定義
class TaskType(Enum):
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    DEVELOPMENT = "development"
    OPTIMIZATION = "optimization"
    SYSTEM = "system"


class PostgreSQLClaudeTaskTracker:
    """PostgreSQL Claude タスクトラッカー - タスク賢者の実装（接続マネージャー使用）"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        """
        初期化

        Args:
            host: PostgreSQLホスト
            port: PostgreSQLポート
            database: データベース名
            user: ユーザー名
            password: パスワード
        """
        # 接続情報（環境変数から取得）
        self.config = {
            "host": host or os.getenv("POSTGRES_HOST", "localhost"),
            "port": port or int(os.getenv("POSTGRES_PORT", 5432)),
            "database": database or os.getenv("POSTGRES_DATABASE", "elders_knowledge"),
            "user": user or os.getenv("POSTGRES_USER", "elders_guild"),
            "password": password or os.getenv("POSTGRES_PASSWORD", "elders_2025"),
        }

        # 接続マネージャー（シングルトン）
        self.connection_manager = None

        # タスク実行ロック（同時実行制御）
        self._task_locks = {}

        logger.info(
            f"PostgreSQL Claude Task Tracker initialized ({self.config['host']}:{self.config['port']}/{self.config['database']})"
        )

    async def initialize(self):
        """データベース接続とテーブル初期化"""
        try:
            # 接続マネージャー取得（シングルトン）
            self.connection_manager = await get_postgres_manager(**self.config)

            # テーブル初期化
            await self._init_database()

            logger.info("PostgreSQL Task Tracker database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL Task Tracker: {e}")
            raise

    async def close(self):
        """接続マネージャーの参照を解除（シングルトンなので実際のクローズは管理される）"""
        if self.connection_manager:
            self.connection_manager = None
            logger.info("PostgreSQL Task Tracker connection manager reference released")

    async def _init_database(self):
        """データベーステーブル初期化"""
        async with self.connection_manager.get_connection() as conn:
            # task_sageテーブル（既存テーブル構造に合わせて更新のみ）
            # 必要に応じて新しいカラムを追加
            try:
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS title TEXT"
                )
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) DEFAULT 'claude_elder'"
                )
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS started_at TIMESTAMP"
                )
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS due_date TIMESTAMP"
                )
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'"
                )
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS progress REAL DEFAULT 0.0"
                )
                await conn.execute(
                    "ALTER TABLE task_sage ADD COLUMN IF NOT EXISTS result TEXT"
                )

                # nameカラムが存在する場合はtitleの別名として使用
                # PostgreSQLでは既存のテーブル構造を尊重
            except Exception as e:
                logger.warning(f"Table modification warning: {e}")

            # 既存テーブルがない場合のみ作成
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_sage (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(255) UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    task_type VARCHAR(50),
                    priority VARCHAR(50),
                    status VARCHAR(50) NOT NULL,
                    assignee VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    dependencies JSONB DEFAULT '{}',
                    results JSONB DEFAULT '{}',
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    tags TEXT[],
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    parent_task_id VARCHAR(255),
                    is_archived BOOLEAN DEFAULT FALSE
                );
            """
            )

            # タスク依存関係テーブル
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(255) NOT NULL,
                    depends_on_task_id VARCHAR(255) NOT NULL,
                    dependency_type VARCHAR(50) DEFAULT 'completion',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES task_sage (task_id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on_task_id) REFERENCES task_sage (task_id) ON DELETE CASCADE
                );
            """
            )

            # タスク実行履歴テーブル
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_executions (
                    id SERIAL PRIMARY KEY,
                    execution_id VARCHAR(255) UNIQUE NOT NULL,
                    task_id VARCHAR(255) NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status VARCHAR(50) NOT NULL,
                    progress REAL DEFAULT 0.0,
                    log_entries JSONB DEFAULT '[]',
                    error_messages JSONB DEFAULT '[]',
                    execution_context JSONB DEFAULT '{}',
                    FOREIGN KEY (task_id) REFERENCES task_sage (task_id) ON DELETE CASCADE
                );
            """
            )

            # インデックス作成（既存のインデックスは作成しない）
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);",
                "CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);",
            ]

            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")

    @asynccontextmanager
    async def _get_connection(self):
        """データベース接続コンテキストマネージャー"""
        async with self.connection_manager.get_connection() as conn:
            yield conn

    def _validate_input(self, title: str, description: str = "", **kwargs):
        """
        入力値検証
        
        Args:
            title: タスク名
            description: 説明
            **kwargs: その他パラメータ
            
        Raises:
            ValueError: 検証エラー
        """
        # 必須フィールド検証
        if not title or not isinstance(title, str):
            raise ValueError("タスク名は必須です（文字列）")
        
        if not isinstance(description, str):
            raise ValueError("説明は文字列である必要があります")
        
        # 長さ制限
        if len(title) > 255:
            raise ValueError("タスク名は255文字以下である必要があります")
        
        if len(description) > 10000:
            raise ValueError("説明は10,000文字以下である必要があります")
        
        # 空文字列チェック
        if title.strip() == "":
            raise ValueError("タスク名に空文字列は使用できません")
        
        # 危険な文字列パターンチェック
        dangerous_patterns = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "--", ";"]
        title_upper = title.upper()
        for pattern in dangerous_patterns:
            if pattern in title_upper:
                raise ValueError(f"危険なパターンが検出されました: {pattern}")

    async def create_task(
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
            context: コンテキスト

        Returns:
            str: タスクID
        """
        # 入力値検証
        self._validate_input(title, description)
        
        task_id = str(uuid4())
        now = datetime.now()

        # デフォルト値設定
        tags = tags or []
        metadata = metadata or {}
        context = context or {}

        async with self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO task_sage (
                    task_id, name, description, task_type, priority, status,
                    assignee, estimated_duration,
                    created_at, updated_at, tags, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                )
                """,
                task_id,
                title,  # nameフィールドにtitleを格納
                description,
                task_type.value if hasattr(task_type, 'value') else task_type,
                priority.value if hasattr(priority, 'value') else priority,
                TaskStatus.PENDING.value,
                assigned_to,  # assigneeフィールドに格納
                estimated_duration_minutes,  # estimated_durationフィールドに格納
                now,
                now,
                tags,
                json.dumps(metadata),
            )

        logger.info(f"Created task: {task_id} - {title}")
        return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスク情報取得

        Args:
            task_id: タスクID

        Returns:
            Optional[Dict]: タスク情報（存在しない場合はNone）
        """
        async with self._get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM task_sage WHERE task_id = $1", task_id
            )

        if row:
            task = dict(row)
            # JSON フィールドをパース
            if task.get("metadata"):
                task["metadata"] = json.loads(task["metadata"])
            if task.get("context"):
                task["context"] = json.loads(task["context"])
            return task
        return None

    async def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[float] = None,
        assigned_to: Optional[str] = None,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        タスク更新

        Args:
            task_id: タスクID
            status: ステータス
            progress: 進捗率
            assigned_to: 担当者
            result: 結果
            error_message: エラーメッセージ
            **kwargs: その他の更新フィールド

        Returns:
            bool: 更新成功フラグ
        """
        updates = []
        values = []
        param_count = 1

        # 更新フィールド設定
        if status is not None:
            updates.append(f"status = ${param_count}")
            values.append(status.value if hasattr(status, 'value') else status)
            param_count += 1

        if progress is not None:
            updates.append(f"progress = ${param_count}")
            values.append(progress)
            param_count += 1

        if assigned_to is not None:
            updates.append(f"assignee = ${param_count}")
            values.append(assigned_to)
            param_count += 1

        if result is not None:
            updates.append(f"result = ${param_count}")
            values.append(result)
            param_count += 1

        if error_message is not None:
            updates.append(f"error_message = ${param_count}")
            values.append(error_message)
            param_count += 1

        # ステータス完了時の処理
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            updates.append(f"completed_at = ${param_count}")
            values.append(datetime.now())
            param_count += 1

        # ステータス開始時の処理
        if status == TaskStatus.IN_PROGRESS:
            updates.append(f"started_at = ${param_count}")
            values.append(datetime.now())
            param_count += 1

        # 必須更新: updated_at
        updates.append(f"updated_at = ${param_count}")
        values.append(datetime.now())
        param_count += 1

        # その他のフィールド
        for key, value in kwargs.items():
            updates.append(f"{key} = ${param_count}")
            values.append(value)
            param_count += 1

        if not updates:
            return False

        # SQL実行
        values.append(task_id)  # WHERE条件用
        sql = (
            f"UPDATE task_sage SET {', '.join(updates)} WHERE task_id = ${param_count}"
        )

        async with self._get_connection() as conn:
            result = await conn.execute(sql, *values)

        # PostgreSQL UPDATE結果の適切な処理
        if result.startswith("UPDATE"):
            updated_count = int(result.split()[-1])
            updated = updated_count > 0
            if updated:
                logger.info(f"Updated task: {task_id}")
            else:
                logger.warning(f"Task not found for update: {task_id}")
            return updated
        else:
            logger.error(f"Unexpected UPDATE result: {result}")
            return False

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC",
    ) -> List[Dict[str, Any]]:
        """
        タスクリスト取得

        Args:
            status: フィルター - ステータス
            priority: フィルター - 優先度
            assigned_to: フィルター - 担当者
            task_type: フィルター - タスクタイプ
            limit: 取得件数上限
            offset: オフセット
            order_by: ソート順

        Returns:
            List[Dict]: タスクリスト
        """
        conditions = []
        values = []
        param_count = 1

        # フィルター条件構築
        if status:
            conditions.append(f"status = ${param_count}")
            values.append(status.value)
            param_count += 1

        if priority:
            conditions.append(f"priority = ${param_count}")
            values.append(priority.value)
            param_count += 1

        if assigned_to:
            conditions.append(f"assignee = ${param_count}")
            values.append(assigned_to)
            param_count += 1

        if task_type:
            conditions.append(f"task_type = ${param_count}")
            values.append(task_type.value)
            param_count += 1

        # アーカイブされていないタスクのみ
        conditions.append("is_archived = FALSE")

        # SQL構築
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT * FROM task_sage
            {where_clause}
            ORDER BY {order_by}
            LIMIT {limit} OFFSET {offset}
        """

        async with self._get_connection() as conn:
            rows = await conn.fetch(sql, *values)

        tasks = []
        for row in rows:
            task = dict(row)
            # JSON フィールドをパース
            if task.get("metadata"):
                try:
                    task["metadata"] = json.loads(task["metadata"])
                except:
                    task["metadata"] = {}
            if task.get("context"):
                try:
                    task["context"] = json.loads(task["context"])
                except:
                    task["context"] = {}
            tasks.append(task)

        return tasks

    async def get_task_statistics(self) -> Dict[str, Any]:
        """
        タスク統計情報取得

        Returns:
            Dict: 統計情報
        """
        async with self._get_connection() as conn:
            # 基本統計
            total_tasks = await conn.fetchval(
                "SELECT COUNT(*) FROM task_sage WHERE is_archived = FALSE"
            )

            # ステータス別統計
            status_stats = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM task_sage
                WHERE is_archived = FALSE
                GROUP BY status
            """
            )

            # 優先度別統計
            priority_stats = await conn.fetch(
                """
                SELECT priority, COUNT(*) as count
                FROM task_sage
                WHERE is_archived = FALSE
                GROUP BY priority
            """
            )

            # タスクタイプ別統計
            type_stats = await conn.fetch(
                """
                SELECT task_type, COUNT(*) as count
                FROM task_sage
                WHERE is_archived = FALSE
                GROUP BY task_type
            """
            )

        return {
            "total_tasks": total_tasks,
            "status_distribution": {
                row["status"]: row["count"] for row in status_stats
            },
            "priority_distribution": {
                row["priority"]: row["count"] for row in priority_stats
            },
            "type_distribution": {row["task_type"]: row["count"] for row in type_stats},
            "timestamp": datetime.now().isoformat(),
        }

    async def delete_task(self, task_id: str, archive: bool = True) -> bool:
        """
        タスク削除（またはアーカイブ）

        Args:
            task_id: タスクID
            archive: True=アーカイブ, False=物理削除

        Returns:
            bool: 削除成功フラグ
        """
        async with self._get_connection() as conn:
            if archive:
                result = await conn.execute(
                    "UPDATE task_sage SET is_archived = TRUE, updated_at = $1 WHERE task_id = $2",
                    datetime.now(),
                    task_id,
                )
                action = "archived"
            else:
                result = await conn.execute(
                    "DELETE FROM task_sage WHERE task_id = $1", task_id
                )
                action = "deleted"

        deleted = result.split()[-1] == "1"
        if deleted:
            logger.info(f"Task {action}: {task_id}")
        return deleted

    async def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック

        Returns:
            Dict: ヘルス情報
        """
        try:
            async with self._get_connection() as conn:
                # 接続テスト
                await conn.fetchval("SELECT 1")

                # 基本統計取得
                total_tasks = await conn.fetchval("SELECT COUNT(*) FROM task_sage")
                active_tasks = await conn.fetchval(
                    "SELECT COUNT(*) FROM task_sage WHERE status IN ('pending', 'in_progress')"
                )

            return {
                "status": "healthy",
                "database": "connected",
                "total_tasks": total_tasks,
                "active_tasks": active_tasks,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# 非同期初期化関数
async def create_postgres_task_tracker(**config) -> PostgreSQLClaudeTaskTracker:
    """
    PostgreSQL タスクトラッカーを作成して初期化

    Args:
        **config: PostgreSQL接続設定

    Returns:
        PostgreSQLClaudeTaskTracker: 初期化済みトラッカー
    """
    tracker = PostgreSQLClaudeTaskTracker(**config)
    await tracker.initialize()
    return tracker


# 使用例とテスト用のメイン関数
async def main():
    """使用例とテスト"""
    tracker = await create_postgres_task_tracker()

    try:
        # ヘルスチェック
        health = await tracker.health_check()
        print(f"ヘルス: {health}")

        # タスク作成
        task_id = await tracker.create_task(
            title="PostgreSQL移行テスト",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH,
            description="PostgreSQLバックエンドのテスト実行",
            tags=["migration", "postgresql", "test"],
            metadata={"version": "1.0", "project": "elders_guild"},
        )
        print(f"作成したタスクID: {task_id}")

        # タスク取得
        task = await tracker.get_task(task_id)
        print(f"タスク詳細: {task}")

        # タスク更新
        await tracker.update_task(task_id, status=TaskStatus.IN_PROGRESS, progress=0.5)

        # タスクリスト
        tasks = await tracker.list_tasks(limit=5)
        print(f"タスクリスト: {len(tasks)}件")

        # 統計
        stats = await tracker.get_task_statistics()
        print(f"統計: {stats}")

    finally:
        await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())

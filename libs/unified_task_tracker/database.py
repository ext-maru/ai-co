"""
統合タスクトラッカー データベース層

Repository Pattern実装によるデータアクセス層
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .models import (
    Task, TaskHistory, TaskDependency,
    TaskStatus, TaskPriority, TaskVisibility
)


class DatabaseError(Exception):
    """データベースエラー"""
    pass


class TaskDatabase:
    """タスクデータベース管理クラス"""
    
    def __init__(self, db_path: str = "task_tracker.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    async def initialize(self):
        """データベース初期化"""
        try:
            # SQLite接続をスレッドプールで実行
            self._connection = await asyncio.get_event_loop().run_in_executor(
                self._executor, sqlite3.connect, self.db_path
            )
            # WALモードを有効化（並行アクセス改善）
            await self._execute("PRAGMA journal_mode=WAL")
            await self._execute("PRAGMA foreign_keys=ON")
            await self._create_tables()
            await self._migrate_schema()
        except Exception as e:
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def close(self):
        """データベース接続を閉じる"""
        if self._connection:
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._connection.close
            )
            self._connection = None
        if self._executor:
            self._executor.shutdown(wait=True)
    
    @property
    def connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        if not self._connection:
            raise DatabaseError("Database not initialized")
        return self._connection
    
    async def _execute(self, query: str, params: tuple = ()):
        """SQLクエリを非同期実行"""
        def _exec():
            cursor = self.connection.execute(query, params)
            self.connection.commit()
            return cursor
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _exec
        )
    
    async def _fetchone(self, query: str, params: tuple = ()):
        """単一行取得"""
        def _fetch():
            cursor = self.connection.execute(query, params)
            return cursor.fetchone()
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _fetch
        )
    
    async def _fetchall(self, query: str, params: tuple = ()):
        """全行取得"""
        def _fetch():
            cursor = self.connection.execute(query, params)
            return cursor.fetchall()
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _fetch
        )
    
    async def _create_tables(self):
        """テーブル作成"""
        # タスクテーブル
        await self._execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                visibility TEXT NOT NULL,
                assignee TEXT,
                creator TEXT,
                labels TEXT,  -- JSON array
                tags TEXT,    -- JSON array
                metadata TEXT,  -- JSON object
                github_issue_number INTEGER,
                github_issue_url TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                estimated_hours REAL,
                actual_hours REAL,
                progress INTEGER DEFAULT 0,
                parent_task_id TEXT,
                FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
            )
        """)
        
        # タスク履歴テーブル
        await self._execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT NOT NULL,
                changed_at TIMESTAMP NOT NULL,
                comment TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # タスク依存関係テーブル
        await self._execute("""
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                depends_on_task_id TEXT NOT NULL,
                dependency_type TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                UNIQUE (task_id, depends_on_task_id)
            )
        """)
        
        # スキーマバージョンテーブル
        await self._execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL
            )
        """)
        
        # インデックス作成
        await self._execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
        )
        await self._execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"
        )
        await self._execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee)"
        )
        await self._execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_github_issue ON tasks(github_issue_number)"
        )
        await self._execute(
            "CREATE INDEX IF NOT EXISTS idx_history_task_id ON task_history(task_id)"
        )
        await self._execute(
            "CREATE INDEX IF NOT EXISTS idx_dependencies_task_id ON task_dependencies(task_id)"
        )
    
    async def _migrate_schema(self):
        """スキーママイグレーション"""
        current_version = await self.get_schema_version()
        
        if current_version < 1:
            # 初回マイグレーション
            await self._execute("""
                INSERT INTO schema_version (version, applied_at)
                VALUES (1, ?)
            """, (datetime.now().isoformat(),))
    
    async def get_schema_version(self) -> int:
        """現在のスキーマバージョンを取得"""
        row = await self._fetchone(
            "SELECT MAX(version) FROM schema_version"
        )
        return row[0] if row and row[0] is not None else 0
    
    async def get_tables(self) -> List[str]:
        """テーブル一覧を取得"""
        rows = await self._fetchall(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row[0] for row in rows]


class TaskRepository:
    """タスクリポジトリ"""
    
    def __init__(self, database: TaskDatabase):
        """
        初期化
        
        Args:
            database: TaskDatabaseインスタンス
        """
        self.db = database
    
    async def create(self, task: Task) -> Task:
        """
        タスクを作成
        
        Args:
            task: 作成するタスク
            
        Returns:
            作成されたタスク
        """
        try:
            await self.db._execute("""
                INSERT INTO tasks (
                    id, title, description, status, priority, visibility,
                    assignee, creator, labels, tags, metadata,
                    github_issue_number, github_issue_url,
                    created_at, updated_at, due_date, completed_at,
                    estimated_hours, actual_hours, progress, parent_task_id
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                task.id, task.title, task.description,
                task.status.value, task.priority.value, task.visibility.value,
                task.assignee, task.creator,
                json.dumps(task.labels), json.dumps(task.tags),
                json.dumps(task.metadata),
                task.github_issue_number, task.github_issue_url,
                task.created_at.isoformat() if task.created_at else None,
                task.updated_at.isoformat() if task.updated_at else None,
                task.due_date.isoformat() if task.due_date else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.estimated_hours, task.actual_hours,
                task.progress, task.parent_task_id
            ))
            return task
        except Exception as e:
            raise DatabaseError(f"Failed to create task: {e}")
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        IDでタスクを取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスクまたはNone
        """
        row = await self.db._fetchone(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        )
        
        if row:
            return self._row_to_task(row)
        return None
    
    async def get_by_github_issue(self, issue_number: int) -> Optional[Task]:
        """
        GitHub Issue番号でタスクを取得
        
        Args:
            issue_number: Issue番号
            
        Returns:
            タスクまたはNone
        """
        row = await self.db._fetchone(
            "SELECT * FROM tasks WHERE github_issue_number = ?", (issue_number,)
        )
        
        if row:
            return self._row_to_task(row)
        return None
    
    async def update(self, task: Task) -> Task:
        """
        タスクを更新
        
        Args:
            task: 更新するタスク
            
        Returns:
            更新されたタスク
        """
        task.updated_at = datetime.now()
        
        try:
            await self.db._execute("""
                UPDATE tasks SET
                    title = ?, description = ?, status = ?,
                    priority = ?, visibility = ?, assignee = ?,
                    creator = ?, labels = ?, tags = ?, metadata = ?,
                    github_issue_number = ?, github_issue_url = ?,
                    updated_at = ?, due_date = ?, completed_at = ?,
                    estimated_hours = ?, actual_hours = ?, progress = ?,
                    parent_task_id = ?
                WHERE id = ?
            """, (
                task.title, task.description, task.status.value,
                task.priority.value, task.visibility.value, task.assignee,
                task.creator, json.dumps(task.labels), json.dumps(task.tags),
                json.dumps(task.metadata),
                task.github_issue_number, task.github_issue_url,
                task.updated_at.isoformat(), 
                task.due_date.isoformat() if task.due_date else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.estimated_hours, task.actual_hours, task.progress,
                task.parent_task_id, task.id
            ))
            return task
        except Exception as e:
            raise DatabaseError(f"Failed to update task: {e}")
    
    async def delete(self, task_id: str) -> bool:
        """
        タスクを削除
        
        Args:
            task_id: タスクID
            
        Returns:
            削除成功ならTrue
        """
        try:
            cursor = await self.db._execute(
                "DELETE FROM tasks WHERE id = ?", (task_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete task: {e}")
    
    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee: Optional[str] = None,
        visibility: Optional[TaskVisibility] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        条件に基づいてタスク一覧を取得
        
        Args:
            status: ステータスフィルタ
            priority: 優先度フィルタ
            assignee: 担当者フィルタ
            visibility: 可視性フィルタ
            limit: 取得件数
            offset: オフセット
            
        Returns:
            タスクリスト
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        if priority:
            query += " AND priority = ?"
            params.append(priority.value)
        
        if assignee:
            query += " AND assignee = ?"
            params.append(assignee)
        
        if visibility:
            query += " AND visibility = ?"
            params.append(visibility.value)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = await self.db._fetchall(query, tuple(params))
        
        return [self._row_to_task(row) for row in rows]
    
    def _row_to_task(self, row) -> Task:
        """SQLiteの行データをTaskオブジェクトに変換"""
        return Task(
            id=row[0],
            title=row[1],
            description=row[2],
            status=TaskStatus(row[3]),
            priority=TaskPriority(row[4]),
            visibility=TaskVisibility(row[5]),
            assignee=row[6],
            creator=row[7],
            labels=json.loads(row[8]),
            tags=json.loads(row[9]),
            metadata=json.loads(row[10]),
            github_issue_number=row[11],
            github_issue_url=row[12],
            created_at=datetime.fromisoformat(row[13]) if row[13] else None,
            updated_at=datetime.fromisoformat(row[14]) if row[14] else None,
            due_date=datetime.fromisoformat(row[15]) if row[15] else None,
            completed_at=datetime.fromisoformat(row[16]) if row[16] else None,
            estimated_hours=row[17],
            actual_hours=row[18],
            progress=row[19],
            parent_task_id=row[20]
        )


class TaskHistoryRepository:
    """タスク履歴リポジトリ"""
    
    def __init__(self, database: TaskDatabase):
        """
        初期化
        
        Args:
            database: TaskDatabaseインスタンス
        """
        self.db = database
    
    async def create(self, history: TaskHistory) -> TaskHistory:
        """
        履歴を作成
        
        Args:
            history: 作成する履歴
            
        Returns:
            作成された履歴
        """
        try:
            await self.db.connection.execute("""
                INSERT INTO task_history (
                    id, task_id, field_name, old_value, new_value,
                    changed_by, changed_at, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history.id, history.task_id, history.field_name,
                history.old_value, history.new_value,
                history.changed_by, history.changed_at, history.comment
            ))
            await self.db.connection.commit()
            return history
        except Exception as e:
            raise DatabaseError(f"Failed to create task history: {e}")
    
    async def get_task_history(
        self,
        task_id: str,
        limit: int = 100
    ) -> List[TaskHistory]:
        """
        タスクの履歴を取得
        
        Args:
            task_id: タスクID
            limit: 取得件数
            
        Returns:
            履歴リスト
        """
        cursor = await self.db.connection.execute("""
            SELECT * FROM task_history
            WHERE task_id = ?
            ORDER BY changed_at DESC
            LIMIT ?
        """, (task_id, limit))
        
        rows = await cursor.fetchall()
        return [self._row_to_history(row) for row in rows]
    
    def _row_to_history(self, row) -> TaskHistory:
        """SQLiteの行データをTaskHistoryオブジェクトに変換"""
        return TaskHistory(
            id=row[0],
            task_id=row[1],
            field_name=row[2],
            old_value=row[3],
            new_value=row[4],
            changed_by=row[5],
            changed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            comment=row[7]
        )


class TaskDependencyRepository:
    """タスク依存関係リポジトリ"""
    
    def __init__(self, database: TaskDatabase):
        """
        初期化
        
        Args:
            database: TaskDatabaseインスタンス
        """
        self.db = database
    
    async def create(self, dependency: TaskDependency) -> TaskDependency:
        """
        依存関係を作成
        
        Args:
            dependency: 作成する依存関係
            
        Returns:
            作成された依存関係
        """
        try:
            await self.db.connection.execute("""
                INSERT INTO task_dependencies (
                    id, task_id, depends_on_task_id,
                    dependency_type, created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                dependency.id, dependency.task_id,
                dependency.depends_on_task_id,
                dependency.dependency_type, dependency.created_at
            ))
            await self.db.connection.commit()
            return dependency
        except Exception as e:
            raise DatabaseError(f"Failed to create task dependency: {e}")
    
    async def get_dependencies(self, task_id: str) -> List[TaskDependency]:
        """
        タスクが依存するタスクを取得
        
        Args:
            task_id: タスクID
            
        Returns:
            依存関係リスト
        """
        cursor = await self.db.connection.execute("""
            SELECT * FROM task_dependencies
            WHERE task_id = ?
            ORDER BY created_at
        """, (task_id,))
        
        rows = await cursor.fetchall()
        return [self._row_to_dependency(row) for row in rows]
    
    async def get_dependents(self, task_id: str) -> List[TaskDependency]:
        """
        タスクに依存するタスクを取得
        
        Args:
            task_id: タスクID
            
        Returns:
            依存関係リスト
        """
        cursor = await self.db.connection.execute("""
            SELECT * FROM task_dependencies
            WHERE depends_on_task_id = ?
            ORDER BY created_at
        """, (task_id,))
        
        rows = await cursor.fetchall()
        return [self._row_to_dependency(row) for row in rows]
    
    async def delete(self, dependency_id: str) -> bool:
        """
        依存関係を削除
        
        Args:
            dependency_id: 依存関係ID
            
        Returns:
            削除成功ならTrue
        """
        try:
            cursor = await self.db.connection.execute(
                "DELETE FROM task_dependencies WHERE id = ?",
                (dependency_id,)
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete dependency: {e}")
    
    def _row_to_dependency(self, row) -> TaskDependency:
        """SQLiteの行データをTaskDependencyオブジェクトに変換"""
        return TaskDependency(
            id=row[0],
            task_id=row[1],
            depends_on_task_id=row[2],
            dependency_type=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None
        )
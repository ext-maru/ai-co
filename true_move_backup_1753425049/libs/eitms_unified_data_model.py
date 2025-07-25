#!/usr/bin/env python3
"""
EITMS (Elders Guild Integrated Task Management System) - 統一データモデル

4賢者会議決定事項に基づく統合タスク管理システムの基盤データモデル
Todo・Issue・TaskTracker・計画書の統一スキーマを定義

Author: クロードエルダー（Claude Elder）
Created: 2025/07/21
Version: 1.0.0
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import uuid


# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """タスク種別"""
    TODO = "todo"                    # 即座実行タスク (< 1日)
    PROJECT_TASK = "project_task"    # プロジェクト管理 (1日-1週)
    ISSUE = "issue"                  # 要件・課題 (1週-数ヶ月)
    PLANNING = "planning"            # 戦略・設計 (数ヶ月-年)


class TaskStatus(Enum):
    """タスクステータス"""
    DRAFT = "draft"
    CREATED = "created"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Priority(Enum):
    """優先度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class UnifiedTask:
    """統一タスクモデル - Single Source of Truth"""
    
    # 基本情報
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    task_type: TaskType = TaskType.TODO
    
    # ステータス管理
    status: TaskStatus = TaskStatus.CREATED
    priority: Priority = Priority.MEDIUM
    
    # 時間管理
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # 関係性
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    sub_tasks: List[str] = field(default_factory=list)
    
    # 外部システム連携
    github_issue_number: Optional[int] = None
    github_pr_number: Optional[int] = None
    planning_doc_path: Optional[str] = None
    
    # メタデータ
    tags: List[str] = field(default_factory=list)
    assignee: str = "claude_elder"
    created_by: str = "claude_elder"
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 実行データ
    time_estimated: Optional[int] = None  # 分
    time_spent: Optional[int] = None      # 分
    session_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'parent_id': self.parent_id,
            'dependencies': self.dependencies,
            'sub_tasks': self.sub_tasks,
            'github_issue_number': self.github_issue_number,
            'github_pr_number': self.github_pr_number,
            'planning_doc_path': self.planning_doc_path,
            'tags': self.tags,
            'assignee': self.assignee,
            'created_by': self.created_by,
            'context': self.context,
            'time_estimated': self.time_estimated,
            'time_spent': self.time_spent,
            'session_data': self.session_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedTask':
        """辞書から復元"""
        task = cls()
        task.id = data.get('id', task.id)
        task.title = data.get('title', '')
        task.description = data.get('description', '')
        task.task_type = TaskType(data.get('task_type', 'todo'))
        task.status = TaskStatus(data.get('status', 'created'))
        task.priority = Priority(data.get('priority', 'medium'))
        
        # 時間データ復元
        if data.get('created_at'):
            task.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if data.get('updated_at'):
            task.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        if data.get('started_at'):
            task.started_at = datetime.fromisoformat(data['started_at'].replace('Z', '+00:00'))
        if data.get('completed_at'):
            task.completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
        if data.get('due_date'):
            task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        
        # その他のフィールド
        task.parent_id = data.get('parent_id')
        task.dependencies = data.get('dependencies', [])
        task.sub_tasks = data.get('sub_tasks', [])
        task.github_issue_number = data.get('github_issue_number')
        task.github_pr_number = data.get('github_pr_number')
        task.planning_doc_path = data.get('planning_doc_path')
        task.tags = data.get('tags', [])
        task.assignee = data.get('assignee', 'claude_elder')
        task.created_by = data.get('created_by', 'claude_elder')
        task.context = data.get('context', {})
        task.time_estimated = data.get('time_estimated')
        task.time_spent = data.get('time_spent')
        task.session_data = data.get('session_data', {})
        
        return task


@dataclass
class SystemSync:
    """システム間同期状態"""
    
    task_id: str
    todo_synced: bool = False
    issue_synced: bool = False
    tracker_synced: bool = False
    planning_synced: bool = False
    last_sync: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sync_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'task_id': self.task_id,
            'todo_synced': self.todo_synced,
            'issue_synced': self.issue_synced,
            'tracker_synced': self.tracker_synced,
            'planning_synced': self.planning_synced,
            'last_sync': self.last_sync.isoformat(),
            'sync_errors': self.sync_errors
        }


class EitmsUnifiedDatabase:
    """EITMS統一データベース"""
    
    def __init__(self, db_path: str = "/home/aicompany/ai_co/data/eitms_unified.db"):
        """初期化メソッド"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3Connection] = None
        
    async def initialize(self):
        """データベース初期化"""
        self._connection = sqlite3connect(str(self.db_path))
        self._connection.row_factory = sqlite3Row
        
        await self._create_tables()
        logger.info(f"🏛️ EITMS統一データベース初期化完了: {self.db_path}")
    
    async def _create_tables(self):
        """テーブル作成"""
        cursor = self._connection.cursor()
        
        # 統一タスクテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unified_tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                due_date TEXT,
                parent_id TEXT,
                dependencies TEXT,  -- JSON array
                sub_tasks TEXT,     -- JSON array
                github_issue_number INTEGER,
                github_pr_number INTEGER,
                planning_doc_path TEXT,
                tags TEXT,          -- JSON array
                assignee TEXT,
                created_by TEXT,
                context TEXT,       -- JSON object
                time_estimated INTEGER,
                time_spent INTEGER,
                session_data TEXT,  -- JSON object
                FOREIGN KEY (parent_id) REFERENCES unified_tasks (id)
            )
        ''')
        
        # システム同期状態テーブル  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_sync (
                task_id TEXT PRIMARY KEY,
                todo_synced BOOLEAN DEFAULT FALSE,
                issue_synced BOOLEAN DEFAULT FALSE,
                tracker_synced BOOLEAN DEFAULT FALSE,
                planning_synced BOOLEAN DEFAULT FALSE,
                last_sync TEXT NOT NULL,
                sync_errors TEXT,   -- JSON array
                FOREIGN KEY (task_id) REFERENCES unified_tasks (id)
            )
        ''')
        
        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_type ON unified_tasks (task_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON unified_tasks (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON unified_tasks (priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON unified_tasks (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_github_issue ON unified_tasks (github_issue_number)' \
            'CREATE INDEX IF NOT EXISTS idx_github_issue ON unified_tasks (github_issue_number)')
        
        self._connection.commit()
        logger.info("📋 データベーステーブル作成完了")
    
    async def save_task(self, task: UnifiedTask) -> bool:
        """タスク保存"""
        try:
            cursor = self._connection.cursor()
            task_dict = task.to_dict()
            
            # JSON フィールドをシリアライズ
            task_dict['dependencies'] = json.dumps(task_dict['dependencies'])
            task_dict['sub_tasks'] = json.dumps(task_dict['sub_tasks'])
            task_dict['tags'] = json.dumps(task_dict['tags'])
            task_dict['context'] = json.dumps(task_dict['context'])
            task_dict['session_data'] = json.dumps(task_dict['session_data'])
            
            # UPSERT実行
            cursor.execute('''
                INSERT OR REPLACE INTO unified_tasks (
                    id, title, description, task_type, status, priority,
                    created_at, updated_at, started_at, completed_at, due_date,
                    parent_id, dependencies, sub_tasks, github_issue_number,
                    github_pr_number, planning_doc_path, tags, assignee,
                    created_by, context, time_estimated, time_spent, session_data
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                task_dict['id'], task_dict['title'], task_dict['description'],
                task_dict['task_type'], task_dict['status'], task_dict['priority'],
                task_dict['created_at'], task_dict['updated_at'], task_dict['started_at'],
                task_dict['completed_at'], task_dict['due_date'], task_dict['parent_id'],
                task_dict['dependencies'], task_dict['sub_tasks'], task_dict['github_issue_number'],
                task_dict['github_pr_number'], task_dict['planning_doc_path'],
                task_dict['tags'], task_dict['assignee'], task_dict['created_by'],
                task_dict['context'], task_dict['time_estimated'], task_dict['time_spent'],
                task_dict['session_data']
            ))
            
            self._connection.commit()
            logger.info(f"💾 タスク保存完了: {task.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ タスク保存失敗: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[UnifiedTask]:
        """タスク取得"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('SELECT * FROM unified_tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 辞書に変換
            data = dict(row)
            
            # JSONフィールドをデシリアライズ
            data['dependencies'] = json.loads(data['dependencies'])
            data['sub_tasks'] = json.loads(data['sub_tasks'])
            data['tags'] = json.loads(data['tags'])
            data['context'] = json.loads(data['context'])
            data['session_data'] = json.loads(data['session_data'])
            
            return UnifiedTask.from_dict(data)
            
        except Exception as e:
            logger.error(f"❌ タスク取得失敗: {e}")
            return None
    
    async def list_tasks(self, 
                        task_type: Optional[TaskType] = None,
                        status: Optional[TaskStatus] = None,
                        limit: int = 100) -> List[UnifiedTask]:
        """タスク一覧取得"""
        try:
            cursor = self._connection.cursor()
            query = 'SELECT * FROM unified_tasks WHERE 1=1'
            params = []
            
            if task_type:
                query += ' AND task_type = ?'
                params.append(task_type.value)
            
            if status:
                query += ' AND status = ?'
                params.append(status.value)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                data = dict(row)
                # JSONフィールドをデシリアライズ
                data['dependencies'] = json.loads(data['dependencies'])
                data['sub_tasks'] = json.loads(data['sub_tasks'])
                data['tags'] = json.loads(data['tags'])
                data['context'] = json.loads(data['context'])
                data['session_data'] = json.loads(data['session_data'])
                
                tasks.append(UnifiedTask.from_dict(data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"❌ タスク一覧取得失敗: {e}")
            return []
    
    async def delete_task(self, task_id: str) -> bool:
        """タスク削除"""
        try:
            cursor = self._connection.cursor()
            cursor.execute('DELETE FROM unified_tasks WHERE id = ?', (task_id,))
            cursor.execute('DELETE FROM system_sync WHERE task_id = ?', (task_id,))
            self._connection.commit()
            
            logger.info(f"🗑️ タスク削除完了: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ タスク削除失敗: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """統計データ取得"""
        try:
            cursor = self._connection.cursor()
            
            # 基本統計
            cursor.execute('SELECT COUNT(*) as total FROM unified_tasks')
            total = cursor.fetchone()['total']
            
            # タスク種別統計
            cursor.execute('''
                SELECT task_type, COUNT(*) as count 
                FROM unified_tasks 
                GROUP BY task_type
            ''')
            task_type_stats = {row['task_type']: row['count'] for row in cursor.fetchall()}
            
            # ステータス統計
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM unified_tasks 
                GROUP BY status
            ''')
            status_stats = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_tasks': total,
                'task_type_distribution': task_type_stats,
                'status_distribution': status_stats,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 統計取得失敗: {e}")
            return {}
    
    def close(self):
        """データベース接続終了"""
        if self._connection:
            self._connection.close()
            logger.info("🔐 データベース接続終了")


class EitmsUnifiedManager:
    """EITMS統一管理クラス"""
    
    def __init__(self, db_path: str = "/home/aicompany/ai_co/data/eitms_unified.db"):
        """初期化メソッド"""
        self.db = EitmsUnifiedDatabase(db_path)
    
    async def initialize(self):
        """システム初期化"""
        await self.db.initialize()
        logger.info("🏛️ EITMS統一管理システム初期化完了")
    
    async def create_task(self, 
                         title: str,
                         description: str = "",
                         task_type: TaskType = TaskType.TODO,
                         priority: Priority = Priority.MEDIUM,
                         **kwargs) -> str:
        """新規タスク作成"""
        task = UnifiedTask(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            **kwargs
        )
        
        success = await self.db.save_task(task)
        if success:
            logger.info(f"✅ タスク作成成功: {task.title} (ID: {task.id})")
            return task.id
        else:
            logger.error(f"❌ タスク作成失敗: {title}")
            return ""
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """タスクステータス更新"""
        task = await self.db.get_task(task_id)
        if not task:
            logger.error(f"❌ タスクが見つかりません: {task_id}")
            return False
        
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        elif status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
        
        return await self.db.save_task(task)
    
    async def link_github_issue(self, task_id: str, issue_number: int) -> bool:
        """GitHub Issue連携"""
        task = await self.db.get_task(task_id)
        if not task:
            return False
        
        task.github_issue_number = issue_number
        task.updated_at = datetime.now(timezone.utc)
        
        return await self.db.save_task(task)
    
    async def link_planning_doc(self, task_id: str, doc_path: str) -> bool:
        """計画書連携"""
        task = await self.db.get_task(task_id)
        if not task:
            return False
        
        task.planning_doc_path = doc_path
        task.updated_at = datetime.now(timezone.utc)
        
        return await self.db.save_task(task)
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボードデータ取得"""
        stats = await self.db.get_stats()
        
        # 進行中タスク
        in_progress = await self.db.list_tasks(status=TaskStatus.IN_PROGRESS)
        
        # 今日のタスク（TODOタイプ）
        today_todos = await self.db.list_tasks(
            task_type=TaskType.TODO,
            status=TaskStatus.CREATED
        )
        
        return {
            'stats': stats,
            'in_progress_tasks': [task.to_dict() for task in in_progress[:5]],
            'today_todos': [task.to_dict() for task in today_todos[:10]]
        }
    
    def close(self):
        """システム終了"""
        self.db.close()


# テスト実行用
async def main():
    """テスト実行"""
    manager = EitmsUnifiedManager()
    await manager.initialize()
    
    # サンプルタスク作成
    task_id = await manager.create_task(
        title="EITMS Phase 1 テスト",
        description="統一データモデルのテスト実行",
        task_type=TaskType.PROJECT_TASK,
        priority=Priority.HIGH
    )
    
    logger.info(f"🎯 テストタスクID: {task_id}")
    
    # ステータス更新
    await manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    
    # ダッシュボードデータ取得
    dashboard = await manager.get_dashboard_data()
    logger.info(f"📊 統計: {dashboard['stats']}")
    
    manager.close()


if __name__ == "__main__":
    asyncio.run(main())
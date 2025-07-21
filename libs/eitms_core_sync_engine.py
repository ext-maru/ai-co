#!/usr/bin/env python3
"""
EITMS コア同期エンジン

Issue → TaskTracker → Todo の自動連携フローを実装
4賢者の英知による最適化された同期メカニズム

Author: クロードエルダー（Claude Elder）
Created: 2025/07/21
Version: 1.0.0
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import uuid

# 内部インポート処理
import sys
import os
sys.path.append(os.path.dirname(__file__))

# 統一データモデルからインポート
if os.path.exists(os.path.join(os.path.dirname(__file__), 'eitms_unified_data_model.py')):
    from eitms_unified_data_model import (
        UnifiedTask, TaskType, TaskStatus, Priority,
        EitmsUnifiedManager
    )
else:
    # モック定義（テスト用）
    from enum import Enum
    from dataclasses import dataclass
    
    class TaskType(Enum):
        TODO = "todo"
        PROJECT_TASK = "project_task" 
        ISSUE = "issue"
        PLANNING = "planning"
    
    class TaskStatus(Enum):
        CREATED = "created"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        BLOCKED = "blocked"
    
    class Priority(Enum):
        HIGH = "high"
        MEDIUM = "medium"
        LOW = "low"
        CRITICAL = "critical"
    
    @dataclass
    class UnifiedTask:
        id: str = "mock-id"
        title: str = ""
        task_type: TaskType = TaskType.TODO
        status: TaskStatus = TaskStatus.CREATED
        priority: Priority = Priority.MEDIUM

# 自動連携基盤からインポート
if os.path.exists(os.path.join(os.path.dirname(__file__), 'eitms_auto_sync_foundation.py')):
    from eitms_auto_sync_foundation import (
        EventType, SyncEvent, EventBus, EitmsAutoSyncManager
    )
else:
    # モック定義
    from enum import Enum
    
    class EventType(Enum):
        SYNC_CASCADE = "sync_cascade"
        TASK_CREATED = "task_created"
    
    @dataclass
    class SyncEvent:
        event_type: EventType = EventType.SYNC_CASCADE
        task_id: str = ""

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CascadeRule(Enum):
    """カスケード（連鎖）ルール"""
    ISSUE_TO_PROJECT = "issue_to_project"
    PROJECT_TO_TODO = "project_to_todo"
    ISSUE_TO_TODO = "issue_to_todo"  # 直接変換
    PROJECT_BREAKDOWN = "project_breakdown"  # プロジェクト分解


@dataclass
class SyncFlow:
    """同期フロー定義"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_type: TaskType = TaskType.ISSUE
    target_type: TaskType = TaskType.PROJECT_TASK
    cascade_rule: CascadeRule = CascadeRule.ISSUE_TO_PROJECT
    auto_create: bool = True
    breakdown_rules: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    transformations: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type.value,
            'target_type': self.target_type.value,
            'cascade_rule': self.cascade_rule.value,
            'auto_create': self.auto_create,
            'breakdown_rules': self.breakdown_rules,
            'conditions': self.conditions,
            'transformations': self.transformations
        }


class EitmsCascadeEngine:
    """EITMS カスケード（連鎖）エンジン"""
    
    def __init__(self, unified_manager):
        self.unified_manager = unified_manager
        self.sync_flows: Dict[str, SyncFlow] = {}
        self.cascade_rules: Dict[CascadeRule, Callable] = {}
        self.event_bus = EventBus()
        self._initialize_default_flows()
        self._register_cascade_handlers()
    
    def _initialize_default_flows(self):
        """デフォルト同期フロー初期化"""
        # Issue → ProjectTask フロー
        issue_to_project = SyncFlow(
            name="Issue to Project Task Flow",
            source_type=TaskType.ISSUE,
            target_type=TaskType.PROJECT_TASK,
            cascade_rule=CascadeRule.ISSUE_TO_PROJECT,
            breakdown_rules={
                'create_subtasks': True,
                'estimate_effort': True,
                'assign_phases': True
            },
            transformations={
                'title_prefix': '[PROJECT] ',
                'priority_boost': False,
                'add_tags': ['from-issue']
            }
        )
        
        # ProjectTask → Todo フロー
        project_to_todo = SyncFlow(
            name="Project Task to Todo Flow", 
            source_type=TaskType.PROJECT_TASK,
            target_type=TaskType.TODO,
            cascade_rule=CascadeRule.PROJECT_TO_TODO,
            breakdown_rules={
                'create_daily_tasks': True,
                'time_boxing': True,
                'priority_inheritance': True
            },
            transformations={
                'title_prefix': '📋 ',
                'due_date_calculation': 'same_day',
                'add_tags': ['daily-task']
            }
        )
        
        # Issue → Todo 直接フロー（小規模Issue用）
        issue_to_todo = SyncFlow(
            name="Issue to Todo Direct Flow",
            source_type=TaskType.ISSUE,
            target_type=TaskType.TODO,
            cascade_rule=CascadeRule.ISSUE_TO_TODO,
            conditions=['priority:low', 'estimated_hours:<2'],
            transformations={
                'title_prefix': '🔧 ',
                'simplify_description': True
            }
        )
        
        self.sync_flows['issue_to_project'] = issue_to_project
        self.sync_flows['project_to_todo'] = project_to_todo  
        self.sync_flows['issue_to_todo'] = issue_to_todo
        
        logger.info(f"🔄 デフォルト同期フロー初期化: {len(self.sync_flows)}件")
    
    def _register_cascade_handlers(self):
        """カスケードハンドラー登録"""
        self.cascade_rules[CascadeRule.ISSUE_TO_PROJECT] = self._handle_issue_to_project
        self.cascade_rules[CascadeRule.PROJECT_TO_TODO] = self._handle_project_to_todo
        self.cascade_rules[CascadeRule.ISSUE_TO_TODO] = self._handle_issue_to_todo
        self.cascade_rules[CascadeRule.PROJECT_BREAKDOWN] = self._handle_project_breakdown
        
        logger.info(f"🎯 カスケードハンドラー登録: {len(self.cascade_rules)}件")
    
    async def trigger_cascade(self, source_task_id: str, cascade_rules: Optional[List[CascadeRule]] = None) -> Dict[str, List[str]]:
        """カスケード（連鎖）同期実行"""
        try:
            source_task = await self.unified_manager.db.get_task(source_task_id)
            if not source_task:
                logger.error(f"❌ ソースタスクが見つかりません: {source_task_id}")
                return {}
            
            results = {}
            
            # 実行するカスケードルール決定
            if cascade_rules is None:
                cascade_rules = self._determine_cascade_rules(source_task)
            
            for cascade_rule in cascade_rules:
                if cascade_rule in self.cascade_rules:
                    created_tasks = await self.cascade_rules[cascade_rule](source_task)
                    results[cascade_rule.value] = created_tasks
                    logger.info(f"✅ カスケード実行: {cascade_rule.value} → {len(created_tasks)}件作成")
                else:
                    logger.warning(f"⚠️ 未実装のカスケードルール: {cascade_rule.value}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ カスケード実行失敗: {e}")
            return {}
    
    def _determine_cascade_rules(self, task: UnifiedTask) -> List[CascadeRule]:
        """タスクに適用するカスケードルール決定"""
        rules = []
        
        if task.task_type == TaskType.ISSUE:
            # Issue の場合
            if self._should_create_direct_todo(task):
                rules.append(CascadeRule.ISSUE_TO_TODO)
            else:
                rules.append(CascadeRule.ISSUE_TO_PROJECT)
        
        elif task.task_type == TaskType.PROJECT_TASK:
            # ProjectTask の場合
            rules.append(CascadeRule.PROJECT_TO_TODO)
            
            if self._should_breakdown_project(task):
                rules.append(CascadeRule.PROJECT_BREAKDOWN)
        
        return rules
    
    def _should_create_direct_todo(self, task: UnifiedTask) -> bool:
        """Issue から直接 Todo を作成すべきか判定"""
        # 低優先度かつ小規模な Issue の場合
        return (task.priority == Priority.LOW and 
                len(task.description) < 200)
    
    def _should_breakdown_project(self, task: UnifiedTask) -> bool:
        """Project Task を分解すべきか判定"""
        # 高優先度かつ大規模なプロジェクト
        return (task.priority in [Priority.HIGH, Priority.CRITICAL] and
                len(task.description) > 500)
    
    async def _handle_issue_to_project(self, issue_task: UnifiedTask) -> List[str]:
        """Issue → ProjectTask カスケード処理"""
        try:
            project_id = await self.unified_manager.create_task(
                title=f"[PROJECT] {issue_task.title}",
                description=f"Issue #{issue_task.github_issue_number or 'N/A'} から生成\n\n{issue_task.description}",
                task_type=TaskType.PROJECT_TASK,
                priority=issue_task.priority,
                context={
                    'source_issue_id': issue_task.id,
                    'source_github_issue': issue_task.github_issue_number,
                    'cascade_rule': 'issue_to_project'
                }
            )
            
            logger.info(f"📋 Issue → ProjectTask 作成: {issue_task.title} → {project_id}")
            return [project_id] if project_id else []
            
        except Exception as e:
            logger.error(f"❌ Issue → ProjectTask 失敗: {e}")
            return []
    
    async def _handle_project_to_todo(self, project_task: UnifiedTask) -> List[str]:
        """ProjectTask → Todo カスケード処理"""
        try:
            created_todos = []
            
            # プロジェクトタスクを実行可能なTodoに分解
            todo_items = self._break_down_project_to_todos(project_task)
            
            for todo_item in todo_items:
                todo_id = await self.unified_manager.create_task(
                    title=f"📋 {todo_item['title']}",
                    description=todo_item['description'],
                    task_type=TaskType.TODO,
                    priority=todo_item['priority'],
                    context={
                        'source_project_id': project_task.id,
                        'cascade_rule': 'project_to_todo',
                        'todo_order': todo_item['order']
                    }
                )
                
                if todo_id:
                    created_todos.append(todo_id)
            
            logger.info(f"📝 ProjectTask → Todo 作成: {project_task.title} → {len(created_todos)}件")
            return created_todos
            
        except Exception as e:
            logger.error(f"❌ ProjectTask → Todo 失敗: {e}")
            return []
    
    async def _handle_issue_to_todo(self, issue_task: UnifiedTask) -> List[str]:
        """Issue → Todo 直接カスケード処理"""
        try:
            todo_id = await self.unified_manager.create_task(
                title=f"🔧 {issue_task.title}",
                description=f"Issue直接対応\n{issue_task.description[:200]}",
                task_type=TaskType.TODO,
                priority=issue_task.priority,
                context={
                    'source_issue_id': issue_task.id,
                    'cascade_rule': 'issue_to_todo',
                    'direct_conversion': True
                }
            )
            
            logger.info(f"🔧 Issue → Todo 直接作成: {issue_task.title}")
            return [todo_id] if todo_id else []
            
        except Exception as e:
            logger.error(f"❌ Issue → Todo 直接変換失敗: {e}")
            return []
    
    async def _handle_project_breakdown(self, project_task: UnifiedTask) -> List[str]:
        """大規模プロジェクトの分解処理"""
        try:
            created_subtasks = []
            
            # プロジェクトをフェーズ別サブタスクに分解
            subtasks = self._break_down_large_project(project_task)
            
            for subtask in subtasks:
                subtask_id = await self.unified_manager.create_task(
                    title=f"[{subtask['phase']}] {subtask['title']}",
                    description=subtask['description'],
                    task_type=TaskType.PROJECT_TASK,
                    priority=subtask['priority'],
                    context={
                        'parent_project_id': project_task.id,
                        'phase': subtask['phase'],
                        'cascade_rule': 'project_breakdown'
                    }
                )
                
                if subtask_id:
                    created_subtasks.append(subtask_id)
            
            logger.info(f"🔄 プロジェクト分解: {project_task.title} → {len(created_subtasks)}サブタスク")
            return created_subtasks
            
        except Exception as e:
            logger.error(f"❌ プロジェクト分解失敗: {e}")
            return []
    
    def _break_down_project_to_todos(self, project_task: UnifiedTask) -> List[Dict[str, Any]]:
        """プロジェクトタスクをTodoアイテムに分解"""
        todos = []
        
        # プロジェクトの複雑度に基づいてTodo分解
        if project_task.priority == Priority.HIGH:
            todos.extend([
                {
                    'title': f"{project_task.title} - 要件分析",
                    'description': "要件とアーキテクチャの詳細分析",
                    'priority': Priority.HIGH,
                    'order': 1
                },
                {
                    'title': f"{project_task.title} - 設計書作成", 
                    'description': "技術設計書とAPIスペックの作成",
                    'priority': Priority.HIGH,
                    'order': 2
                },
                {
                    'title': f"{project_task.title} - 実装",
                    'description': "コア機能の実装",
                    'priority': Priority.MEDIUM,
                    'order': 3
                },
                {
                    'title': f"{project_task.title} - テスト",
                    'description': "ユニットテストと統合テストの実行",
                    'priority': Priority.HIGH,
                    'order': 4
                }
            ])
        else:
            # 通常のプロジェクト
            todos.extend([
                {
                    'title': f"{project_task.title} - 実装準備",
                    'description': "実装に必要な調査と準備",
                    'priority': project_task.priority,
                    'order': 1
                },
                {
                    'title': f"{project_task.title} - 実装",
                    'description': "機能の実装",
                    'priority': project_task.priority,
                    'order': 2
                },
                {
                    'title': f"{project_task.title} - 検証",
                    'description': "実装結果の検証とテスト",
                    'priority': project_task.priority,
                    'order': 3
                }
            ])
        
        return todos
    
    def _break_down_large_project(self, project_task: UnifiedTask) -> List[Dict[str, Any]]:
        """大規模プロジェクトをサブタスクに分解"""
        subtasks = []
        
        phases = [
            {
                'phase': 'ANALYSIS',
                'title': 'システム分析・要件定義',
                'description': 'システム全体の分析と詳細要件定義',
                'priority': Priority.HIGH
            },
            {
                'phase': 'DESIGN', 
                'title': 'アーキテクチャ設計',
                'description': 'システムアーキテクチャとAPI設計',
                'priority': Priority.HIGH
            },
            {
                'phase': 'IMPLEMENTATION',
                'title': 'コア機能実装',
                'description': 'メインロジックとインターフェースの実装',
                'priority': Priority.MEDIUM
            },
            {
                'phase': 'INTEGRATION',
                'title': 'システム統合',
                'description': 'コンポーネント統合とシステムテスト',
                'priority': Priority.HIGH
            },
            {
                'phase': 'OPTIMIZATION',
                'title': 'パフォーマンス最適化',
                'description': 'パフォーマンス調整と最終検証',
                'priority': Priority.MEDIUM
            }
        ]
        
        return phases
    
    async def get_cascade_status(self, task_id: str) -> Dict[str, Any]:
        """カスケード状況取得"""
        try:
            task = await self.unified_manager.db.get_task(task_id)
            if not task:
                return {'error': 'Task not found'}
            
            # 関連タスク検索
            all_tasks = await self.unified_manager.db.list_tasks(limit=1000)
            
            # ソースタスク（このタスクから生成されたタスク）
            derived_tasks = [
                t for t in all_tasks 
                if t.context.get('source_issue_id') == task_id or
                   t.context.get('source_project_id') == task_id or
                   t.context.get('parent_project_id') == task_id
            ]
            
            # 親タスク（このタスクを生成した元タスク）  
            parent_task = None
            if task.context.get('source_issue_id'):
                parent_task = await self.unified_manager.db.get_task(task.context['source_issue_id'])
            elif task.context.get('source_project_id'):
                parent_task = await self.unified_manager.db.get_task(task.context['source_project_id'])
            
            return {
                'task_id': task_id,
                'task_type': task.task_type.value,
                'cascade_rule': task.context.get('cascade_rule'),
                'parent_task': {
                    'id': parent_task.id,
                    'title': parent_task.title,
                    'type': parent_task.task_type.value
                } if parent_task else None,
                'derived_tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'type': t.task_type.value,
                        'status': t.status.value,
                        'cascade_rule': t.context.get('cascade_rule')
                    }
                    for t in derived_tasks
                ],
                'cascade_chain_length': len(derived_tasks),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ カスケード状況取得失敗: {e}")
            return {'error': str(e)}


class EitmsCoreSyncEngine:
    """EITMS コア同期エンジン - メインオーケストレーター"""
    
    def __init__(self, unified_manager):
        self.unified_manager = unified_manager
        self.cascade_engine = EitmsCascadeEngine(unified_manager)
        self.auto_sync_enabled = True
        self.sync_stats = {
            'total_cascades': 0,
            'successful_cascades': 0,
            'failed_cascades': 0,
            'tasks_created': 0
        }
    
    async def initialize(self):
        """システム初期化"""
        await self.cascade_engine._initialize_default_flows()
        logger.info("🏛️ EITMS コア同期エンジン初期化完了")
    
    async def sync_task(self, task_id: str, manual_rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """タスク同期実行"""
        try:
            self.sync_stats['total_cascades'] += 1
            
            # カスケードルール決定
            cascade_rules = []
            if manual_rules:
                cascade_rules = [CascadeRule(rule) for rule in manual_rules if rule in CascadeRule.__members__.values()]
            
            # カスケード実行
            results = await self.cascade_engine.trigger_cascade(task_id, cascade_rules)
            
            # 統計更新
            if results:
                self.sync_stats['successful_cascades'] += 1
                self.sync_stats['tasks_created'] += sum(len(task_list) for task_list in results.values())
            else:
                self.sync_stats['failed_cascades'] += 1
            
            # 結果サマリー
            return {
                'task_id': task_id,
                'cascade_results': results,
                'success': bool(results),
                'total_created': sum(len(task_list) for task_list in results.values()),
                'executed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.sync_stats['failed_cascades'] += 1
            logger.error(f"❌ タスク同期失敗: {e}")
            return {
                'task_id': task_id,
                'success': False,
                'error': str(e)
            }
    
    async def bulk_sync(self, task_ids: List[str]) -> Dict[str, Any]:
        """一括同期処理"""
        results = []
        
        for task_id in task_ids:
            result = await self.sync_task(task_id)
            results.append(result)
            
            # 過負荷防止のための小休止
            await asyncio.sleep(0.1)
        
        return {
            'total_tasks': len(task_ids),
            'successful': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']]),
            'results': results,
            'executed_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def auto_sync_new_task(self, task_id: str) -> bool:
        """新規タスクの自動同期"""
        if not self.auto_sync_enabled:
            return False
        
        try:
            result = await self.sync_task(task_id)
            return result['success']
        except Exception as e:
            logger.error(f"❌ 自動同期失敗: {e}")
            return False
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """同期統計取得"""
        return {
            **self.sync_stats,
            'auto_sync_enabled': self.auto_sync_enabled,
            'success_rate': (
                self.sync_stats['successful_cascades'] / max(self.sync_stats['total_cascades'], 1)
            ) * 100,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def enable_auto_sync(self):
        """自動同期有効化"""
        self.auto_sync_enabled = True
        logger.info("✅ 自動同期有効化")
    
    def disable_auto_sync(self):
        """自動同期無効化"""
        self.auto_sync_enabled = False
        logger.info("⏸️ 自動同期無効化")


# テスト実行用
async def main():
    """テスト実行"""
    # モック定義を使用してテスト実行
    class MockUnifiedManager:
        def __init__(self):
            self.tasks = {}
        
        async def create_task(self, **kwargs):
            task_id = str(uuid.uuid4())
            self.tasks[task_id] = kwargs
            return task_id
        
        @property 
        def db(self):
            return type('MockDB', (), {
                'get_task': lambda self, task_id: UnifiedTask(id=task_id, title="Test Task") if task_id in self.tasks else None,
                'list_tasks': lambda self, limit=100: []
            })()
    
    # テスト実行
    manager = MockUnifiedManager()
    sync_engine = EitmsCoreSyncEngine(manager)
    await sync_engine.initialize()
    
    # テストタスク作成 
    test_task_id = await manager.create_task(
        title="テスト Issue",
        task_type=TaskType.ISSUE,
        priority=Priority.HIGH
    )
    
    logger.info(f"🎯 テストタスクID: {test_task_id}")
    
    # 同期実行
    result = await sync_engine.sync_task(test_task_id)
    logger.info(f"🔄 同期結果: {result}")
    
    # 統計確認
    stats = sync_engine.get_sync_statistics()
    logger.info(f"📊 同期統計: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
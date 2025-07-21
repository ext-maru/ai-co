#!/usr/bin/env python3
"""
EITMS コア同期エンジン - テストスイート

TDD原則に基づくテスト実装
Phase 3: Issue → TaskTracker → Todo 自動連携システム

Author: クロードエルダー（Claude Elder）
Created: 2025/07/21
"""

import asyncio
import json
import pytest
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# テスト対象のモジュールをインポート
import sys
sys.path.append('/home/aicompany/ai_co')
sys.path.append('/home/aicompany/ai_co/libs')

from libs.eitms_core_sync_engine import (
    CascadeRule,
    SyncFlow,
    EitmsCascadeEngine,
    EitmsCoreSyncEngine
)


# テスト用のモッククラス
class MockUnifiedTask:
    """UnifiedTaskのモック"""
    def __init__(self, task_id="test-id", title="Test Task", task_type="issue", priority="medium", description="", context=None):
        self.id = task_id
        self.title = title
        self.task_type = type('TaskType', (), {task_type.upper(): task_type})()
        self.task_type.value = task_type
        self.priority = type('Priority', (), {priority.upper(): priority})()
        self.priority.value = priority
        self.description = description
        self.github_issue_number = 123
        self.context = context or {}


class MockUnifiedManager:
    """EitmsUnifiedManagerのモック"""
    def __init__(self):
        self.tasks = {}
        self._task_counter = 1
    
    async def create_task(self, **kwargs):
        task_id = f"mock-task-{self._task_counter}"
        self._task_counter += 1
        self.tasks[task_id] = kwargs
        return task_id
    
    @property
    def db(self):
        return type('MockDB', (), {
            'get_task': lambda self, task_id: MockUnifiedTask(task_id=task_id) if task_id in self.tasks else None,
            'list_tasks': lambda self, limit=100: []
        })()


class TestCascadeRule:
    """CascadeRule Enumのテスト"""
    
    def test_cascade_rule_values(self):
        """CascadeRule値のテスト"""
        assert CascadeRule.ISSUE_TO_PROJECT.value == "issue_to_project"
        assert CascadeRule.PROJECT_TO_TODO.value == "project_to_todo"
        assert CascadeRule.ISSUE_TO_TODO.value == "issue_to_todo"
        assert CascadeRule.PROJECT_BREAKDOWN.value == "project_breakdown"


class TestSyncFlow:
    """SyncFlowクラスのテスト"""
    
    def test_sync_flow_creation_with_defaults(self):
        """デフォルト値でのSyncFlow作成テスト"""
        sync_flow = SyncFlow()
        
        assert sync_flow.id is not None
        assert len(sync_flow.id) > 0
        assert sync_flow.name == ""
        assert sync_flow.auto_create is True
        assert sync_flow.breakdown_rules == {}
        assert sync_flow.conditions == []
        assert sync_flow.transformations == {}
    
    def test_sync_flow_creation_with_parameters(self):
        """パラメータ指定でのSyncFlow作成テスト"""
        sync_flow = SyncFlow(
            name="Test Flow",
            auto_create=False,
            breakdown_rules={'test': True},
            conditions=['priority:high'],
            transformations={'prefix': 'TEST: '}
        )
        
        assert sync_flow.name == "Test Flow"
        assert sync_flow.auto_create is False
        assert sync_flow.breakdown_rules == {'test': True}
        assert sync_flow.conditions == ['priority:high']
        assert sync_flow.transformations == {'prefix': 'TEST: '}
    
    def test_sync_flow_to_dict(self):
        """SyncFlowの辞書変換テスト"""
        sync_flow = SyncFlow(
            name="Dict Test Flow",
            auto_create=True
        )
        
        flow_dict = sync_flow.to_dict()
        
        assert isinstance(flow_dict, dict)
        assert flow_dict['name'] == "Dict Test Flow"
        assert flow_dict['auto_create'] is True
        assert 'id' in flow_dict
        assert 'source_type' in flow_dict
        assert 'target_type' in flow_dict
        assert 'cascade_rule' in flow_dict


@pytest.mark.asyncio
class TestEitmsCascadeEngine:
    """EitmsCascadeEngineクラスのテスト"""
    
    async def test_cascade_engine_initialization(self):
        """カスケードエンジン初期化テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        # デフォルトフローが初期化されているか確認
        assert len(engine.sync_flows) >= 3
        assert 'issue_to_project' in engine.sync_flows
        assert 'project_to_todo' in engine.sync_flows
        assert 'issue_to_todo' in engine.sync_flows
        
        # カスケードハンドラーが登録されているか確認
        assert len(engine.cascade_rules) >= 4
        assert CascadeRule.ISSUE_TO_PROJECT in engine.cascade_rules
        assert CascadeRule.PROJECT_TO_TODO in engine.cascade_rules
    
    async def test_determine_cascade_rules_for_issue(self):
        """Issue のカスケードルール決定テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        # 通常のIssue（ProjectTaskを経由）
        normal_issue = MockUnifiedTask(
            task_type="issue", 
            priority="high",
            description="長い詳細な説明が含まれています。" * 10
        )
        
        rules = engine._determine_cascade_rules(normal_issue)
        assert CascadeRule.ISSUE_TO_PROJECT in rules
        
        # 小規模Issue（直接Todo化）
        small_issue = MockUnifiedTask(
            task_type="issue",
            priority="low", 
            description="短い説明"
        )
        
        rules = engine._determine_cascade_rules(small_issue)
        assert CascadeRule.ISSUE_TO_TODO in rules
    
    async def test_determine_cascade_rules_for_project(self):
        """ProjectTask のカスケードルール決定テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        # 通常のプロジェクト
        normal_project = MockUnifiedTask(
            task_type="project_task",
            priority="medium",
            description="中規模のプロジェクト"
        )
        
        rules = engine._determine_cascade_rules(normal_project)
        assert CascadeRule.PROJECT_TO_TODO in rules
        
        # 大規模プロジェクト
        large_project = MockUnifiedTask(
            task_type="project_task",
            priority="high",
            description="非常に大規模で複雑なプロジェクトです。" * 20
        )
        
        rules = engine._determine_cascade_rules(large_project)
        assert CascadeRule.PROJECT_TO_TODO in rules
        assert CascadeRule.PROJECT_BREAKDOWN in rules
    
    async def test_should_create_direct_todo(self):
        """直接Todo作成判定テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        # 小規模Issue（直接Todo化対象）
        small_task = MockUnifiedTask(
            priority="low",
            description="短い説明"
        )
        assert engine._should_create_direct_todo(small_task) is True
        
        # 大規模Issue（ProjectTask経由）
        large_task = MockUnifiedTask(
            priority="high",
            description="非常に長い詳細な説明です。" * 10
        )
        assert engine._should_create_direct_todo(large_task) is False
    
    async def test_should_breakdown_project(self):
        """プロジェクト分解判定テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        # 小規模プロジェクト（分解不要）
        small_project = MockUnifiedTask(
            priority="medium",
            description="小規模プロジェクト"
        )
        assert engine._should_breakdown_project(small_project) is False
        
        # 大規模プロジェクト（分解対象）
        large_project = MockUnifiedTask(
            priority="high",
            description="非常に大規模で複雑なプロジェクトです。" * 20
        )
        assert engine._should_breakdown_project(large_project) is True
    
    async def test_handle_issue_to_project(self):
        """Issue → ProjectTask カスケード処理テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        issue_task = MockUnifiedTask(
            title="Test Issue",
            task_type="issue",
            priority="high"
        )
        
        created_tasks = await engine._handle_issue_to_project(issue_task)
        
        assert len(created_tasks) == 1
        assert created_tasks[0] in mock_manager.tasks
        
        # 作成されたタスクの確認
        created_task = mock_manager.tasks[created_tasks[0]]
        assert "[PROJECT]" in created_task['title']
        assert created_task['task_type'].value == 'project_task'
        assert "source_issue_id" in created_task['context']
    
    async def test_handle_project_to_todo(self):
        """ProjectTask → Todo カスケード処理テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        project_task = MockUnifiedTask(
            title="Test Project",
            task_type="project_task",
            priority="medium"
        )
        
        created_tasks = await engine._handle_project_to_todo(project_task)
        
        assert len(created_tasks) >= 3  # 最低3つのTodoが作成される
        
        # 作成されたTodoの確認
        for task_id in created_tasks:
            created_task = mock_manager.tasks[task_id]
            assert created_task['task_type'].value == 'todo'
            assert "source_project_id" in created_task['context']
    
    async def test_handle_issue_to_todo_direct(self):
        """Issue → Todo 直接カスケード処理テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        issue_task = MockUnifiedTask(
            title="Small Issue",
            task_type="issue",
            priority="low"
        )
        
        created_tasks = await engine._handle_issue_to_todo(issue_task)
        
        assert len(created_tasks) == 1
        
        # 作成されたTodoの確認
        created_task = mock_manager.tasks[created_tasks[0]]
        assert created_task['task_type'].value == 'todo'
        assert "🔧" in created_task['title']
        assert created_task['context']['direct_conversion'] is True
    
    async def test_handle_project_breakdown(self):
        """大規模プロジェクト分解処理テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        large_project = MockUnifiedTask(
            title="Large Project",
            task_type="project_task",
            priority="high"
        )
        
        created_tasks = await engine._handle_project_breakdown(large_project)
        
        assert len(created_tasks) == 5  # 5つのフェーズに分解される
        
        phases = ['ANALYSIS', 'DESIGN', 'IMPLEMENTATION', 'INTEGRATION', 'OPTIMIZATION']
        
        for i, task_id in enumerate(created_tasks):
            created_task = mock_manager.tasks[task_id]
            assert phases[i] in created_task['title']
            assert created_task['context']['phase'] == phases[i]
    
    async def test_break_down_project_to_todos(self):
        """プロジェクトのTodo分解テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        # 高優先度プロジェクト
        high_priority_project = MockUnifiedTask(priority="high")
        todos = engine._break_down_project_to_todos(high_priority_project)
        
        assert len(todos) == 4  # 要件分析、設計、実装、テスト
        assert todos[0]['title'].endswith(" - 要件分析")
        assert todos[1]['title'].endswith(" - 設計書作成")
        assert todos[2]['title'].endswith(" - 実装")
        assert todos[3]['title'].endswith(" - テスト")
        
        # 通常プロジェクト
        normal_project = MockUnifiedTask(priority="medium")
        todos = engine._break_down_project_to_todos(normal_project)
        
        assert len(todos) == 3  # 準備、実装、検証
    
    async def test_break_down_large_project(self):
        """大規模プロジェクト分解テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCascadeEngine(mock_manager)
        
        large_project = MockUnifiedTask()
        subtasks = engine._break_down_large_project(large_project)
        
        assert len(subtasks) == 5
        
        expected_phases = ['ANALYSIS', 'DESIGN', 'IMPLEMENTATION', 'INTEGRATION', 'OPTIMIZATION']
        for i, subtask in enumerate(subtasks):
            assert subtask['phase'] == expected_phases[i]
            assert 'title' in subtask
            assert 'description' in subtask
            assert 'priority' in subtask
    
    async def test_trigger_cascade_with_specific_rules(self):
        """特定ルールでのカスケード実行テスト"""
        mock_manager = MockUnifiedManager()
        mock_manager.tasks['test-issue-1'] = {}  # タスクが存在するとみなす
        
        engine = EitmsCascadeEngine(mock_manager)
        
        # モックのget_taskメソッドを設定
        def mock_get_task(task_id):
            if task_id == 'test-issue-1':
                return MockUnifiedTask(
                    task_id=task_id,
                    title="Test Issue",
                    task_type="issue",
                    priority="high"
                )
            return None
        
        engine.unified_manager.db.get_task = mock_get_task
        
        # カスケード実行
        results = await engine.trigger_cascade(
            'test-issue-1', 
            [CascadeRule.ISSUE_TO_PROJECT]
        )
        
        assert 'issue_to_project' in results
        assert len(results['issue_to_project']) == 1


@pytest.mark.asyncio
class TestEitmsCoreSyncEngine:
    """EitmsCoreSyncEngineクラスのテスト"""
    
    async def test_core_sync_engine_initialization(self):
        """コア同期エンジン初期化テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        
        assert engine.unified_manager == mock_manager
        assert engine.auto_sync_enabled is True
        assert engine.sync_stats['total_cascades'] == 0
        assert engine.sync_stats['successful_cascades'] == 0
        assert engine.sync_stats['failed_cascades'] == 0
        assert engine.sync_stats['tasks_created'] == 0
        assert isinstance(engine.cascade_engine, EitmsCascadeEngine)
    
    async def test_sync_task_success(self):
        """タスク同期成功テスト"""
        mock_manager = MockUnifiedManager() 
        mock_manager.tasks['test-task-1'] = {}
        
        engine = EitmsCoreSyncEngine(mock_manager)
        
        # モック設定
        engine.cascade_engine.trigger_cascade = AsyncMock(
            return_value={'issue_to_project': ['new-task-1', 'new-task-2']}
        )
        
        result = await engine.sync_task('test-task-1')
        
        assert result['success'] is True
        assert result['task_id'] == 'test-task-1'
        assert result['total_created'] == 2
        assert 'executed_at' in result
        
        # 統計更新確認
        assert engine.sync_stats['total_cascades'] == 1
        assert engine.sync_stats['successful_cascades'] == 1
        assert engine.sync_stats['tasks_created'] == 2
    
    async def test_sync_task_failure(self):
        """タスク同期失敗テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        
        # カスケードエンジンでエラーを発生させる
        engine.cascade_engine.trigger_cascade = AsyncMock(
            side_effect=Exception("Cascade failed")
        )
        
        result = await engine.sync_task('non-existent-task')
        
        assert result['success'] is False
        assert 'error' in result
        
        # 統計更新確認
        assert engine.sync_stats['total_cascades'] == 1
        assert engine.sync_stats['failed_cascades'] == 1
    
    async def test_bulk_sync(self):
        """一括同期処理テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        
        # sync_taskをモック
        engine.sync_task = AsyncMock(side_effect=[
            {'success': True, 'total_created': 2},
            {'success': False, 'error': 'Test error'},
            {'success': True, 'total_created': 1}
        ])
        
        result = await engine.bulk_sync(['task-1', 'task-2', 'task-3'])
        
        assert result['total_tasks'] == 3
        assert result['successful'] == 2
        assert result['failed'] == 1
        assert len(result['results']) == 3
        assert 'executed_at' in result
    
    async def test_auto_sync_new_task_enabled(self):
        """自動同期有効時のテスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        engine.auto_sync_enabled = True
        
        # sync_taskをモック
        engine.sync_task = AsyncMock(return_value={'success': True})
        
        result = await engine.auto_sync_new_task('new-task-1')
        
        assert result is True
        engine.sync_task.assert_called_once_with('new-task-1')
    
    async def test_auto_sync_new_task_disabled(self):
        """自動同期無効時のテスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        engine.auto_sync_enabled = False
        
        result = await engine.auto_sync_new_task('new-task-1')
        
        assert result is False
    
    def test_get_sync_statistics(self):
        """同期統計取得テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        
        # テストデータ設定
        engine.sync_stats = {
            'total_cascades': 10,
            'successful_cascades': 8,
            'failed_cascades': 2,
            'tasks_created': 25
        }
        
        stats = engine.get_sync_statistics()
        
        assert stats['total_cascades'] == 10
        assert stats['successful_cascades'] == 8
        assert stats['failed_cascades'] == 2
        assert stats['tasks_created'] == 25
        assert stats['auto_sync_enabled'] is True
        assert stats['success_rate'] == 80.0
        assert 'generated_at' in stats
    
    def test_enable_disable_auto_sync(self):
        """自動同期有効化・無効化テスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        
        # 初期状態は有効
        assert engine.auto_sync_enabled is True
        
        # 無効化
        engine.disable_auto_sync()
        assert engine.auto_sync_enabled is False
        
        # 有効化
        engine.enable_auto_sync()
        assert engine.auto_sync_enabled is True


# 統合テスト
@pytest.mark.asyncio
class TestEitmsCoreSyncIntegration:
    """EITMS コア同期システム統合テスト"""
    
    async def test_full_cascade_workflow(self):
        """完全カスケードワークフローテスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        await engine.initialize()
        
        # Issue作成
        issue_id = await mock_manager.create_task(
            title="統合テストIssue",
            task_type="issue",
            priority="high",
            description="統合テストのための Issue です。" * 10
        )
        
        # モックのget_taskを設定
        def mock_get_task(task_id):
            if task_id == issue_id:
                return MockUnifiedTask(
                    task_id=task_id,
                    title="統合テストIssue",
                    task_type="issue", 
                    priority="high",
                    description="統合テストのための Issue です。" * 10
                )
            return None
        
        engine.unified_manager.db.get_task = mock_get_task
        
        # カスケード実行
        result = await engine.sync_task(issue_id)
        
        # 結果確認
        assert result['success'] is True
        assert result['total_created'] >= 1
        
        # 統計確認
        stats = engine.get_sync_statistics()
        assert stats['total_cascades'] >= 1
        assert stats['successful_cascades'] >= 1
    
    async def test_multiple_cascade_types(self):
        """複数カスケードタイプテスト"""
        mock_manager = MockUnifiedManager()
        engine = EitmsCoreSyncEngine(mock_manager)
        
        # 異なるタイプのタスクでテスト
        test_tasks = [
            ('issue', 'high', 'Test Issue'),
            ('project_task', 'medium', 'Test Project'),
            ('issue', 'low', 'Small Issue')  # 直接Todo化対象
        ]
        
        results = []
        for task_type, priority, title in test_tasks:
            task_id = await mock_manager.create_task(
                title=title,
                task_type=task_type,
                priority=priority
            )
            
            # モック設定
            def make_mock_get_task(t_id, t_type, t_priority, t_title):
                def mock_get_task(task_id):
                    if task_id == t_id:
                        return MockUnifiedTask(
                            task_id=t_id,
                            title=t_title,
                            task_type=t_type,
                            priority=t_priority
                        )
                    return None
                return mock_get_task
            
            engine.unified_manager.db.get_task = make_mock_get_task(
                task_id, task_type, priority, title
            )
            
            result = await engine.sync_task(task_id)
            results.append(result)
        
        # 全体結果確認
        successful_syncs = [r for r in results if r['success']]
        assert len(successful_syncs) >= 1  # 最低1つは成功する


# pytest実行用のメイン関数
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
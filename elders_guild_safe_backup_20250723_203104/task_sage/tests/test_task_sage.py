#!/usr/bin/env python3
"""
Task Sage Unit Tests
TDD: テストファースト開発
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

# Elder Tree imports
import sys
sys.path.insert(0, '/home/aicompany/elders_guild')

from shared_libs import MessageType, MessagePriority
from task_sage.soul import TaskSageSoul
from task_sage.abilities.task_models import (
    Task, TaskStatus, TaskPriority, 
    Project, TaskSpec, ProjectSpec,
    EffortEstimate
)


class TestTaskSageCore:


"""Task Sageのコア機能テスト"""
        """Task Sageインスタンスの作成"""
        sage = TaskSageSoul()
        await sage.initialize()
        yield sage
        await sage.shutdown()
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_sage):

        """タスク作成機能のテスト"""
        """工数見積もり機能のテスト"""
        # Arrange
        task = Task(
            id=str(uuid4()),
            title="複雑なリファクタリング",
            description="レガシーコードの大規模リファクタリング",
            complexity_factors={
                "lines_of_code": 5000,
                "cyclomatic_complexity": 25,
                "dependencies": 15
            }
        )
        
        # Act
        estimate = await task_sage.estimate_effort(task)
        
        # Assert
        assert isinstance(estimate, EffortEstimate)
        assert estimate.hours > 0
        assert estimate.confidence >= 0.0 and estimate.confidence <= 1.0
        assert estimate.breakdown is not None
        assert "analysis" in estimate.breakdown
        assert "implementation" in estimate.breakdown
        assert "testing" in estimate.breakdown
    
    @pytest.mark.asyncio
    async def test_task_dependencies(self, task_sage):

            """タスク依存関係解決のテスト"""
        """プロジェクト計画機能のテスト"""
        # Arrange
        project_spec = ProjectSpec(
            name="Elder Tree Phase 1",
            description="Task Sage実装プロジェクト",
            target_completion=datetime.now() + timedelta(days=14),
            resource_constraints={
                "developers": 1,
                "daily_hours": 8
            }
        )
        
        # Act
        project = await task_sage.create_project(project_spec)
        
        # プロジェクトにタスクを追加
        task1 = await task_sage.create_task(TaskSpec(
            title="基本設計",
            project_id=project.id,
            estimated_hours=10.0,
            priority=TaskPriority.HIGH
        ))
        task2 = await task_sage.create_task(TaskSpec(
            title="実装",
            project_id=project.id,
            estimated_hours=20.0,
            priority=TaskPriority.HIGH,
            dependencies=[task1.id]
        ))
        task3 = await task_sage.create_task(TaskSpec(
            title="テスト",
            project_id=project.id,
            estimated_hours=15.0,
            priority=TaskPriority.MEDIUM,
            dependencies=[task2.id]
        ))
        
        plan = await task_sage.plan_project(project.id)
        
        # Assert
        assert project.id is not None
        assert project.name == "Elder Tree Phase 1"
        assert plan.total_estimated_hours == 45.0  # 10 + 20 + 15
        assert plan.critical_path is not None
        assert len(plan.critical_path) == 3  # 3つのタスクが依存関係でつながっている
        assert plan.milestones is not None
        assert len(plan.milestones) > 0
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, task_sage):

            """進捗追跡機能のテスト"""
            task = await task_sage.create_task(TaskSpec(
                title=f"Task {i+1}",
                project_id=project.id,
                estimated_hours=10.0
            ))
            tasks.append(task)
        
        # 一部のタスクを完了
        await task_sage.update_task(tasks[0].id, {
            "status": TaskStatus.COMPLETED,
            "actual_hours": 9.0
        })
        
        # Act
        progress = await task_sage.track_progress(project.id)
        
        # Assert
        assert progress.total_tasks == 3
        assert progress.completed_tasks == 1
        assert progress.completion_percentage == pytest.approx(33.33, 0.01)
        assert progress.hours_spent == 9.0
        assert progress.hours_remaining == 20.0


class TestTaskSageIntegration:

        """Task Sageの統合テスト"""
        """Task Sageインスタンスの作成"""
        sage = TaskSageSoul()
        await sage.initialize()
        yield sage
        await sage.shutdown()
    
    # A2A通信テストは削除（A2A依存除去）
    # @pytest.mark.asyncio
    # async def test_sage_communication(self, task_sage):
    #     """他の賢者との通信テスト"""
    #     pass
    
    @pytest.mark.asyncio
    async def test_error_handling(self, task_sage):

    """エラーハンドリングのテスト"""
            # 無効なタイトルでTaskSpecを作成しようとする
            invalid_task_spec = TaskSpec(
                title="",  # 無効なタイトル
                description="テスト"
            )
    
    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, task_sage):

            """並行タスク作成のテスト"""
            assert task.title == f"並行タスク {i}"


class TestTaskSageQuality:

            """品質保証テスト（Elder Guild品質基準）"""
        """Task Sageインスタンスの作成"""
        sage = TaskSageSoul()
        await sage.initialize()
        yield sage
        await sage.shutdown()
    
    @pytest.mark.asyncio
    async def test_iron_will_compliance(self, task_sage):

        """Iron Will遵守テスト - TODO/FIXME禁止"""
        """パフォーマンス要件テスト"""
        import time
        
        # 100タスクの作成時間測定
        start_time = time.time()
        
        tasks = []
        for i in range(100):
            task = await task_sage.create_task(TaskSpec(
                title=f"Performance Test {i}",
                estimated_hours=1.0
            ))
            tasks.append(task)
        
        elapsed_time = time.time() - start_time
        
        # Assert: 100タスクを5秒以内に作成
        assert elapsed_time < 5.0
        assert len(tasks) == 100
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, task_sage):

        """メモリ効率テスト"""
            await task_sage.create_task(TaskSpec(
                title=f"Memory Test {i}",
                description="x" * 1000  # 1KB description
            ))
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Assert: メモリ増加が100MB以内
        assert memory_increase < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
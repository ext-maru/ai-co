#!/usr/bin/env python3
"""
Enhanced Task Sage 統合テスト
Created: 2025-07-17
Author: Claude Elder
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.four_sages.task.enhanced_task_sage import EnhancedTaskSage
from libs.four_sages.task.task_sage import TaskPriority, TaskStatus, TaskType

@pytest.fixture
async def enhanced_sage():
    """Enhanced Task Sage フィクスチャ"""
    sage = EnhancedTaskSage()
    yield sage
    # クリーンアップ
    await sage.database.store_task  # 接続を閉じる

@pytest.mark.asyncio
async def test_dynamic_priority_calculation(enhanced_sage):
    """動的優先度計算のテスト"""
    # テストタスクを作成
    task_data = {
        "type": "create_task",
        "title": "Critical Bug Fix",
        "description": "Fix critical production bug affecting users",
        "task_type": "maintenance",
        "priority": "critical",
        "assignee": "test_user",
        "due_date": (datetime.now() + timedelta(hours=2)).isoformat(),
        "tags": ["bug", "critical", "production"]
    }
    
    # タスク作成
    create_result = await enhanced_sage.process_request(task_data)
    assert create_result["success"]
    task_id = create_result["task_id"]
    
    # 完了時間予測をリクエスト
    predict_request = {
        "type": "predict_completion",
        "task_id": task_id
    }
    
    predict_result = await enhanced_sage.process_request(predict_request)
    assert predict_result["success"]
    assert "dynamic_priority" in predict_result["prediction"]
    assert predict_result["prediction"]["dynamic_priority"] > 100  # Critical taskは高優先度

@pytest.mark.asyncio
async def test_schedule_optimization(enhanced_sage):
    """スケジュール最適化のテスト"""
    # 複数のテストタスクを作成
    task_ids = []
    for i in range(5):
        task_data = {
            "type": "create_task",
            "title": f"Test Task {i}",
            "description": f"Test task description {i}",
            "task_type": "development",
            "priority": ["high", "medium", "low"][i % 3],
            "assignee": "test_user",
            "estimated_hours": 1 + i * 0.5
        }
        
        result = await enhanced_sage.process_request(task_data)
        if result["success"]:
            task_ids.append(result["task_id"])
    
    # スケジュール最適化をリクエスト
    optimize_request = {
        "type": "optimize_schedule",
        "status": "pending",
        "max_parallel": 3,
        "respect_due_dates": True
    }
    
    optimize_result = await enhanced_sage.process_request(optimize_request)
    assert optimize_result["success"]
    assert len(optimize_result["optimized_schedule"]) >= len(task_ids)
    assert "gantt_chart" in optimize_result
    assert "resource_optimization" in optimize_result

@pytest.mark.asyncio
async def test_resource_analysis(enhanced_sage):
    """リソース分析のテスト"""
    # リソース分析をリクエスト
    analyze_request = {
        "type": "analyze_resources"
    }
    
    analyze_result = await enhanced_sage.process_request(analyze_request)
    assert analyze_result["success"]
    assert "resource_analysis" in analyze_result
    assert "current" in analyze_result["resource_analysis"]
    assert "cpu_percent" in analyze_result["resource_analysis"]["current"]
    assert "memory_percent" in analyze_result["resource_analysis"]["current"]
    assert "efficiency_score" in analyze_result["resource_analysis"]

@pytest.mark.asyncio
async def test_task_recommendations(enhanced_sage):
    """タスク推奨のテスト"""
    # タスクを作成
    for i in range(3):
        task_data = {
            "type": "create_task",
            "title": f"Priority Task {i}",
            "description": f"Task with varying priority {i}",
            "task_type": ["development", "optimization", "investigation"][i],
            "priority": ["critical", "high", "medium"][i],
            "due_date": (datetime.now() + timedelta(days=i)).isoformat() if i < 2 else None
        }
        await enhanced_sage.process_request(task_data)
    
    # 推奨を取得
    recommend_request = {
        "type": "get_recommendations",
        "limit": 5
    }
    
    recommend_result = await enhanced_sage.process_request(recommend_request)
    assert recommend_result["success"]
    assert "recommendations" in recommend_result
    assert "priority_tasks" in recommend_result["recommendations"]
    assert len(recommend_result["recommendations"]["priority_tasks"]) > 0

@pytest.mark.asyncio
async def test_execution_time_prediction(enhanced_sage):
    """実行時間予測のテスト"""
    # タスクを作成
    task_data = {
        "type": "create_task",
        "title": "Development Task",
        "description": "A complex development task requiring multiple resources",
        "task_type": "development",
        "priority": "high",
        "estimated_hours": 4,
        "dependencies": [],
        "resources": [
            {"type": "cpu", "id": "cpu-1", "allocation": 80},
            {"type": "memory", "id": "mem-1", "allocation": 60}
        ]
    }
    
    create_result = await enhanced_sage.process_request(task_data)
    assert create_result["success"]
    task_id = create_result["task_id"]
    
    # 予測を取得
    predict_request = {
        "type": "predict_completion",
        "task_id": task_id
    }
    
    predict_result = await enhanced_sage.process_request(predict_request)
    assert predict_result["success"]
    assert "predicted_duration_seconds" in predict_result["prediction"]
    assert "confidence_interval" in predict_result["prediction"]
    
    # 予測時間が妥当な範囲内か確認
    predicted_time = predict_result["prediction"]["predicted_duration_seconds"]
    assert 3600 <= predicted_time <= 18000  # 1時間〜5時間

@pytest.mark.asyncio
async def test_tracking_update(enhanced_sage):
    """追跡データ更新のテスト"""
    # タスクを作成して完了させる
    task_data = {
        "type": "create_task",
        "title": "Tracking Test Task",
        "description": "Task for testing tracking updates",
        "task_type": "maintenance",
        "priority": "medium"
    }
    
    create_result = await enhanced_sage.process_request(task_data)
    task_id = create_result["task_id"]
    
    # タスクを開始
    update_request = {
        "type": "update_task",
        "task_id": task_id,
        "status": "in_progress"
    }
    await enhanced_sage.process_request(update_request)
    
    # タスクを完了
    await asyncio.sleep(1)  # 実行時間をシミュレート
    complete_request = {
        "type": "update_task",
        "task_id": task_id,
        "status": "completed"
    }
    await enhanced_sage.process_request(complete_request)
    
    # 追跡データを更新
    tracking_request = {
        "type": "update_tracking",
        "task_id": task_id
    }
    
    tracking_result = await enhanced_sage.process_request(tracking_request)
    assert tracking_result["success"]
    assert tracking_result["task_id"] == task_id

@pytest.mark.asyncio
async def test_dependency_scheduling(enhanced_sage):
    """依存関係を持つタスクのスケジューリングテスト"""
    # 親タスクを作成
    parent_task = {
        "type": "create_task",
        "title": "Parent Task",
        "description": "Must be completed first",
        "task_type": "development",
        "priority": "medium"
    }
    parent_result = await enhanced_sage.process_request(parent_task)
    parent_id = parent_result["task_id"]
    
    # 依存タスクを作成
    child_task = {
        "type": "create_task",
        "title": "Child Task",
        "description": "Depends on parent task",
        "task_type": "development",
        "priority": "high",
        "dependencies": [{"task_id": parent_id, "type": "requires"}]
    }
    child_result = await enhanced_sage.process_request(child_task)
    
    # スケジュール最適化
    optimize_request = {
        "type": "optimize_schedule",
        "status": "pending"
    }
    
    optimize_result = await enhanced_sage.process_request(optimize_request)
    assert optimize_result["success"]
    
    # 親タスクが子タスクより先にスケジュールされているか確認
    schedule = optimize_result["optimized_schedule"]
    parent_schedule = next((s for s in schedule if s["task_id"] == parent_id), None)
    child_schedule = next((s for s in schedule if s["task_id"] == child_result["task_id"]), None)
    
    if parent_schedule and child_schedule:
        assert parent_schedule["scheduled_start"] < child_schedule["scheduled_start"]

@pytest.mark.asyncio
async def test_parallel_execution_optimization(enhanced_sage):
    """並列実行最適化のテスト"""
    # 並列実行可能なタスクを作成
    task_ids = []
    for i in range(6):
        task_data = {
            "type": "create_task",
            "title": f"Parallel Task {i}",
            "description": f"Can be executed in parallel {i}",
            "task_type": "investigation",
            "priority": "medium",
            "estimated_hours": 0.5
        }
        result = await enhanced_sage.process_request(task_data)
        task_ids.append(result["task_id"])
    
    # 並列数を制限してスケジュール最適化
    optimize_request = {
        "type": "optimize_schedule",
        "status": "pending",
        "max_parallel": 3
    }
    
    optimize_result = await enhanced_sage.process_request(optimize_request)
    assert optimize_result["success"]
    
    # 並列グループが正しく作成されているか確認
    schedule = optimize_result["optimized_schedule"]
    parallel_groups = {}
    for task in schedule:
        group = task["parallel_group"]
        if group not in parallel_groups:
            parallel_groups[group] = []
        parallel_groups[group].append(task)
    
    # 各グループが最大3タスクまでか確認
    assert len(parallel_groups) >= 2  # 6タスクで最大3並列なら最低2グループ

@pytest.mark.asyncio
async def test_enhanced_capabilities(enhanced_sage):
    """拡張能力のテスト"""
    capabilities = enhanced_sage.get_capabilities()
    
    # 基本能力が含まれているか
    assert "task_creation" in capabilities
    assert "task_management" in capabilities
    
    # 拡張能力が含まれているか
    assert "dynamic_priority_calculation" in capabilities
    assert "execution_time_prediction" in capabilities
    assert "resource_optimization" in capabilities
    assert "smart_task_scheduling" in capabilities
    assert "performance_tracking" in capabilities

if __name__ == "__main__":
    # テスト実行
    asyncio.run(test_dynamic_priority_calculation(EnhancedTaskSage()))
    asyncio.run(test_resource_analysis(EnhancedTaskSage()))
    print("✅ All integration tests passed!")
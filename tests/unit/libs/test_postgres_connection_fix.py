#!/usr/bin/env python3
"""
PostgreSQL接続修正テスト - 応急処置根絶令準拠
既存コードの直接修正による問題解決確認
"""

import asyncio
import pytest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.postgres_claude_task_tracker import (
    PostgreSQLClaudeTaskTracker,
    TaskPriority,
    TaskStatus,
    TaskType,
)


@pytest.mark.asyncio
async def test_postgres_connection_without_workaround():
    """応急処置を使わずに正しく接続できることを確認"""
    tracker = PostgreSQLClaudeTaskTracker()
    
    try:
        # 初期化（asyncpg直接使用）
        await tracker.initialize()
        
        # タスク作成テスト
        task_id = await tracker.create_task(
            title="PostgreSQL接続テスト",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH,
            description="応急処置根絶令準拠テスト",
        )
        
        assert task_id is not None
        
        # タスク取得テスト
        task = await tracker.get_task(task_id)
        assert task is not None
        assert task["name"] == "PostgreSQL接続テスト"  # データベースではnameフィールド
        
        # タスク更新テスト
        await tracker.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100.0,
        )
        
        # 更新確認
        updated_task = await tracker.get_task(task_id)
        assert updated_task["status"] == TaskStatus.COMPLETED.value
        assert updated_task["progress"] == 100.0
        
        print("✅ PostgreSQL接続テスト成功 - 応急処置なしで正常動作")
        
    finally:
        # クリーンアップ
        await tracker.close()


@pytest.mark.asyncio
async def test_multiple_connections_without_manager():
    """接続マネージャーなしで複数接続が正しく動作することを確認"""
    trackers = []
    
    try:
        # 複数のトラッカーインスタンスを作成
        for i in range(3):
            tracker = PostgreSQLClaudeTaskTracker()
            await tracker.initialize()
            trackers.append(tracker)
        
        # 各トラッカーでタスクを作成
        task_ids = []
        for i, tracker in enumerate(trackers):
            task_id = await tracker.create_task(
                title=f"並列接続テスト #{i+1}",
                task_type=TaskType.FEATURE,
                priority=TaskPriority.MEDIUM,
            )
            task_ids.append(task_id)
        
        # すべてのタスクが作成されたことを確認
        assert len(task_ids) == 3
        assert all(task_id is not None for task_id in task_ids)
        
        print("✅ 複数接続テスト成功 - 接続マネージャーなしで正常動作")
        
    finally:
        # すべての接続をクローズ
        for tracker in trackers:
            await tracker.close()


@pytest.mark.asyncio
async def test_event_loop_compatibility():
    """イベントループ競合がないことを確認"""
    # 新しいイベントループで実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        tracker = PostgreSQLClaudeTaskTracker()
        await tracker.initialize()
        
        # タスク作成
        task_id = await tracker.create_task(
            title="イベントループテスト",
            task_type=TaskType.RESEARCH,
            priority=TaskPriority.LOW,
        )
        
        assert task_id is not None
        
        print("✅ イベントループ互換性テスト成功 - asyncio問題なし")
        
    finally:
        await tracker.close()
        loop.close()


if __name__ == "__main__":
    # 単独実行時のテスト
    asyncio.run(test_postgres_connection_without_workaround())
    asyncio.run(test_multiple_connections_without_manager())
    asyncio.run(test_event_loop_compatibility())
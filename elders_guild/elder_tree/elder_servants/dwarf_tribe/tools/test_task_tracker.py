#!/usr/bin/env python3
"""タスクトラッカー動作テスト"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.claude_task_tracker import get_task_tracker, TaskStatus, TaskPriority, TaskType

def test_task_tracker():
    """タスクトラッカーの動作確認"""
    tracker = get_task_tracker()
    
    print("🔧 タスクトラッカー動作テスト開始...")
    
    # テストタスク作成
    task_id = tracker.create_task(
        title="タスクトラッカーシステム修復テスト",
        task_type=TaskType.MAINTENANCE,
        priority=TaskPriority.HIGH,
        description="Elder Flowと連携した本物のタスクトラッカー実装",
        created_by="test_script"
    )
    print(f"✅ タスク作成成功: {task_id}")
    
    # タスク取得
    task = tracker.get_task(task_id)
    if task:
        print(f"📋 タスク詳細: {task['title']} (Status: {task['status']})")
    
    # ステータス更新
    tracker.update_task_status(task_id, TaskStatus.IN_PROGRESS, progress=0.5)
    print("🔄 ステータス更新: IN_PROGRESS")
    
    # 統計情報
    stats = tracker.get_task_statistics()
    print(f"📊 統計情報:")
    print(f"  - 総タスク数: {stats['total_tasks']}")
    print(f"  - アクティブ: {stats['active_tasks']}")
    print(f"  - 保留中: {stats['pending_tasks']}")
    print(f"  - 完了済み: {stats['completed_tasks']}")
    
    # 完了
    tracker.update_task_status(task_id, TaskStatus.COMPLETED, progress=1.0)
    print("✅ タスク完了")
    
    return True

if __name__ == "__main__":
    test_task_tracker()
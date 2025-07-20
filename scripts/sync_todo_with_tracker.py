#!/usr/bin/env python3
"""TodoListとタスクトラッカーの同期スクリプト"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.claude_task_tracker import get_task_tracker


def sync_todos():
    """現在のTodoListをタスクトラッカーと同期"""
    tracker = get_task_tracker()

    # 現在のTodoリスト（TodoReadの結果から）
    todos = [
        {
            "content": "Elder Flowを使用してタスクトラッカーシステムの完全修復を実行",
            "status": "in_progress",
            "priority": "high",
            "id": "task-tracker-repair-1",
        },
        {
            "content": "claude_task_tracker.pyを本物の実装に置き換え",
            "status": "pending",
            "priority": "high",
            "id": "task-tracker-repair-2",
        },
        {
            "content": "PostgreSQL統合を有効化してタスク記録を移行",
            "status": "pending",
            "priority": "high",
            "id": "task-tracker-repair-3",
        },
        {
            "content": "Elder Flow自動適用メカニズムを確実に動作させる",
            "status": "pending",
            "priority": "high",
            "id": "task-tracker-repair-4",
        },
        {
            "content": "現在のTodoListをタスクトラッカーと同期",
            "status": "pending",
            "priority": "medium",
            "id": "task-tracker-repair-5",
        },
    ]

    print("📋 TodoListとタスクトラッカーの同期開始...")

    synced_count = tracker.sync_with_todo_list(todos)

    print(f"✅ 同期完了: {synced_count}件のタスクを同期しました")

    # 統計表示
    stats = tracker.get_task_statistics()
    print(f"\n📊 タスク統計:")
    print(f"  - 総タスク数: {stats['total_tasks']}")
    print(f"  - アクティブ: {stats['active_tasks']}")
    print(f"  - 保留中: {stats['pending_tasks']}")
    print(f"  - 完了済み: {stats['completed_tasks']}")


if __name__ == "__main__":
    sync_todos()

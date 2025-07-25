#!/usr/bin/env python3
"""
PostgreSQL統合テスト - 実際の動作確認
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


async def test_real_postgres_connection():
    """実際のPostgreSQL接続テスト"""
    print("🔍 実際のPostgreSQL接続テストを実行中...")
    try:
        from elders_guild.elder_tree.postgresql_asyncio_connection_manager import get_postgres_manager

        # 接続マネージャー取得
        manager = await get_postgres_manager()

        # ヘルスチェック実行
        health = await manager.health_check()
        print(f"✅ PostgreSQL接続成功: {health['status']}")
        print(f"📊 応答時間: {health.get('response_time_ms', 'N/A')}ms")
        
        return health['status'] == 'healthy'
        
    except Exception as e:
        print(f"❌ PostgreSQL接続エラー: {e}")
        return False


async def test_task_tracker_operations():
    """タスクトラッカー操作テスト"""
    print("🔍 タスクトラッカー操作テストを実行中...")
    try:
        from elders_guild.elder_tree.postgres_claude_task_tracker import (
            create_postgres_task_tracker,
            TaskType,
            TaskPriority,
        )

        # タスクトラッカー作成
        tracker = await create_postgres_task_tracker()

        # タスク作成
        task_id = await tracker.create_task(
            title="PostgreSQL修正テスト",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH,
            description="PostgreSQL AsyncIO修正の動作確認テスト",
            tags=["postgresql", "asyncio", "fix"],
            metadata={"test": "integration", "version": "1.0"}
        )
        print(f"✅ タスク作成成功: {task_id}")

        # タスク取得
        task = await tracker.get_task(task_id)
        if task:
            print(f"✅ タスク取得成功: {task['name']}")
        else:
            print("❌ タスク取得失敗")
            return False

        # タスクリスト取得
        tasks = await tracker.list_tasks(limit=5)
        print(f"✅ タスクリスト取得成功: {len(tasks)}件")

        # 統計取得
        stats = await tracker.get_task_statistics()
        print(f"✅ 統計取得成功: 総タスク数 {stats['total_tasks']}")

        # リソース解放
        await tracker.close()
        print("✅ リソース解放完了")

        return True

    except Exception as e:
        print(f"❌ タスクトラッカー操作エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_wrapper_operations():
    """同期ラッパー操作テスト"""
    print("🔍 同期ラッパー操作テストを実行中...")
    try:
        from elders_guild.elder_tree.claude_task_tracker_postgres import ClaudeTaskTracker
        from elders_guild.elder_tree.postgres_claude_task_tracker import TaskType, TaskPriority

        # 同期ラッパー使用
        tracker = ClaudeTaskTracker()

        # ヘルスチェック（同期的に実行）
        health = tracker.health_check()
        print(f"✅ 同期ヘルスチェック成功: {health.get('status', 'unknown')}")

        # タスク作成（同期的に実行）
        task_id = tracker.create_task(
            title="同期ラッパーテスト",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.MEDIUM,
            description="同期ラッパーの動作確認",
            tags=["sync", "wrapper"]
        )
        print(f"✅ 同期タスク作成成功: {task_id}")

        # タスク取得（同期的に実行）
        task = tracker.get_task(task_id)
        if task:
            print(f"✅ 同期タスク取得成功: {task['name']}")
        else:
            print("❌ 同期タスク取得失敗")
            return False

        # 統計取得（同期的に実行）
        stats = tracker.get_task_statistics()
        print(f"✅ 同期統計取得成功: {stats.get('total_tasks', 0)}件")

        # リソース解放
        tracker.close_sync()
        print("✅ 同期リソース解放完了")

        return True

    except Exception as e:
        print(f"❌ 同期ラッパー操作エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_operations():
    """並行操作テスト"""
    print("🔍 並行操作テストを実行中...")
    try:
        from elders_guild.elder_tree.postgres_claude_task_tracker import (
            create_postgres_task_tracker,
            TaskType,
            TaskPriority,
        )

        # 複数のタスクトラッカーを並行作成
        async def create_and_use_tracker(tracker_id):
            """create_and_use_trackerを作成"""
            tracker = await create_postgres_task_tracker()
            
            task_id = await tracker.create_task(
                title=f"並行テスト {tracker_id}",
                task_type=TaskType.FEATURE,
                priority=TaskPriority.LOW,
                description=f"並行操作テスト {tracker_id}",
                tags=["concurrent", f"tracker_{tracker_id}"]
            )
            
            task = await tracker.get_task(task_id)
            await tracker.close()
            
            return task_id, task['name'] if task else None

        # 5つの並行操作
        tasks = [
            asyncio.create_task(create_and_use_tracker(i))
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)
        success_count = sum(1 for task_id, name in results if task_id and name)
        
        print(f"✅ 並行操作成功: {success_count}/5")
        return success_count == 5

    except Exception as e:
        print(f"❌ 並行操作エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メイン実行関数"""
    print("🚀 PostgreSQL統合テスト開始")
    print("=" * 60)

    # 非同期テスト
    async_tests = [
        ("PostgreSQL接続テスト", test_real_postgres_connection),
        ("タスクトラッカー操作テスト", test_task_tracker_operations),
        ("並行操作テスト", test_concurrent_operations),
    ]

    results = []
    for test_name, test_func in async_tests:
        print(f"\n📋 {test_name}:")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {e}")
            results.append(False)

    # 同期テスト
    print(f"\n📋 同期ラッパー操作テスト:")
    try:
        sync_result = test_sync_wrapper_operations()
        results.append(sync_result)
    except Exception as e:
        print(f"❌ 同期ラッパー操作テストで予期しないエラー: {e}")
        results.append(False)

    # 結果の集計
    print("\n" + "=" * 60)
    print("📊 統合テスト結果:")
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"✅ 成功: {passed_tests}/{total_tests}")
    print(f"❌ 失敗: {failed_tests}/{total_tests}")
    print(f"📊 成功率: {passed_tests/total_tests*100:0.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 全統合テスト成功！PostgreSQL統合が完全に動作しています。")
        return True
    else:
        print(f"\n⚠️ {failed_tests}個のテストが失敗しました。")
        print("💡 PostgreSQLサーバーが起動していない可能性があります。")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
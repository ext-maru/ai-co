#!/usr/bin/env python3
"""
PostgreSQL AsyncIO修正の簡単な検証スクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_import():
    """インポートテスト"""
    print("🔍 インポートテストを実行中...")
    try:
        from elders_guild.elder_tree.postgresql_asyncio_connection_manager import (
            PostgreSQLConnectionManager,
            EventLoopSafeWrapper,
            get_postgres_manager,
        )
        print("✅ 接続マネージャーのインポート成功")
        return True
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False


def test_event_loop_safe_wrapper():
    """EventLoopSafeWrapperのテスト"""
    print("🔍 EventLoopSafeWrapperテストを実行中...")
    try:
        from elders_guild.elder_tree.postgresql_asyncio_connection_manager import EventLoopSafeWrapper

        async def test_coro():
            await asyncio.sleep(0.1)
            return "test_success"

        # 安全な非同期実行
        result = EventLoopSafeWrapper.run_async(test_coro())
        print(f"✅ EventLoopSafeWrapper実行成功: {result}")
        return result == "test_success"
    except Exception as e:
        print(f"❌ EventLoopSafeWrapperエラー: {e}")
        return False


def test_singleton_pattern():
    """シングルトンパターンのテスト"""
    print("🔍 シングルトンパターンテストを実行中...")
    try:
        from elders_guild.elder_tree.postgresql_asyncio_connection_manager import PostgreSQLConnectionManager

        # 複数のインスタンス作成
        manager1 = PostgreSQLConnectionManager()
        manager2 = PostgreSQLConnectionManager()

        # 同じインスタンスであることを確認
        is_singleton = manager1 is manager2
        print(f"✅ シングルトンパターン確認: {is_singleton}")
        return is_singleton
    except Exception as e:
        print(f"❌ シングルトンパターンエラー: {e}")
        return False


def test_task_tracker_wrapper():
    """タスクトラッカーラッパーのテスト"""
    print("🔍 タスクトラッカーラッパーテストを実行中...")
    try:
        from elders_guild.elder_tree.claude_task_tracker_postgres import ClaudeTaskTracker

        # 初期化テスト
        tracker = ClaudeTaskTracker()
        has_run_async = hasattr(tracker, '_run_async')
        print(f"✅ タスクトラッカーラッパー初期化成功: _run_async={has_run_async}")
        return has_run_async
    except Exception as e:
        print(f"❌ タスクトラッカーラッパーエラー: {e}")
        return False


async def test_async_functionality():
    """非同期機能のテスト"""
    print("🔍 非同期機能テストを実行中...")
    try:
        # 複数の並行処理
        async def worker(worker_id):
            await asyncio.sleep(0.1)
            return f"worker_{worker_id}_completed"

        # 5つの並行タスク
        tasks = [asyncio.create_task(worker(i)) for i in range(5)]
        results = await asyncio.gather(*tasks)

        success = len(results) == 5 and all("completed" in result for result in results)
        print(f"✅ 並行処理テスト成功: {success}, 結果数: {len(results)}")
        return success
    except Exception as e:
        print(f"❌ 非同期機能エラー: {e}")
        return False


def test_error_handling():
    """エラーハンドリングのテスト"""
    print("🔍 エラーハンドリングテストを実行中...")
    try:
        from elders_guild.elder_tree.postgresql_asyncio_connection_manager import EventLoopSafeWrapper

        async def error_coro():
            raise ValueError("Test error")

        # エラーが適切に伝播することを確認
        try:
            EventLoopSafeWrapper.run_async(error_coro())
            return False  # エラーが発生しなかった場合は失敗
        except ValueError:
            print("✅ エラーハンドリング成功: 例外が適切に伝播")
            return True
    except Exception as e:
        print(f"❌ エラーハンドリングテストエラー: {e}")
        return False


def main():
    """メイン実行関数"""
    print("🚀 PostgreSQL AsyncIO修正検証スクリプト開始")
    print("=" * 60)

    tests = [
        ("インポートテスト", test_import),
        ("EventLoopSafeWrapperテスト", test_event_loop_safe_wrapper),
        ("シングルトンパターンテスト", test_singleton_pattern),
        ("タスクトラッカーラッパーテスト", test_task_tracker_wrapper),
        ("エラーハンドリングテスト", test_error_handling),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {e}")
            results.append(False)

    # 非同期テストの実行
    print(f"\n📋 非同期機能テスト:")
    try:
        async_result = asyncio.run(test_async_functionality())
        results.append(async_result)
    except Exception as e:
        print(f"❌ 非同期機能テストで予期しないエラー: {e}")
        results.append(False)

    # 結果の集計
    print("\n" + "=" * 60)
    print("📊 テスト結果集計:")
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"✅ 成功: {passed_tests}/{total_tests}")
    print(f"❌ 失敗: {failed_tests}/{total_tests}")
    print(f"📊 成功率: {passed_tests/total_tests*100:0.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 全テスト成功！PostgreSQL AsyncIO修正が正常に動作しています。")
        return True
    else:
        print(f"\n⚠️ {failed_tests}個のテストが失敗しました。修正が必要です。")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
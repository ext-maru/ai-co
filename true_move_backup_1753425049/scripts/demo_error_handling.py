#!/usr/bin/env python3
"""
強化エラーハンドリングシステムのデモ（短時間版）
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from libs.enhanced_error_handling import ErrorClassifier
from libs.enhanced_error_handling import RetryStrategy
from libs.enhanced_error_handling import smart_retry
from libs.enhanced_error_handling import task_executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """エラーハンドリングシステムのデモ"""
    print("=" * 60)
    print("🛡️ Elders Guild 強化エラーハンドリングシステム")
    print("=" * 60)

    # 1.0 エラー分類のデモ
    print("\n📋 エラー分類システム")
    print("-" * 40)

    test_errors = [
        (TimeoutError("Operation timed out"), "タイムアウトエラー"),
        (PermissionError("sudo required"), "権限エラー"),
        (ConnectionError("Network unreachable"), "ネットワークエラー"),
        (Exception("429 Too Many Requests"), "レート制限"),
        (ImportError("No module named 'xyz'"), "インポートエラー"),
    ]

    for error, description in test_errors:
        error_type, retryable, strategy = ErrorClassifier.classify(error)
        print(f"\n{description}: {error}")
        print(f"  → 分類: {error_type}")
        print(f"  → リトライ可能: {'はい' if retryable else 'いいえ'}")
        if strategy:
            print(f"  → 最大試行回数: {strategy.max_attempts}")

    # 2.0 スマートリトライのデモ
    print("\n\n📋 スマートリトライ機能")
    print("-" * 40)

    attempt_count = 0

    @smart_retry(strategy=RetryStrategy(max_attempts=3, initial_delay=0.5))
    def demo_retry_function():
        """3回目で成功する関数"""
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise ConnectionError(f"Connection failed (attempt {attempt_count})")

        return "接続成功！"

    try:
        result = demo_retry_function()
        print(f"\n✅ 最終結果: {result}")
        print(f"   試行回数: {attempt_count}回")
    except Exception as e:
        print(f"\n❌ 失敗: {e}")

    # 3.0 タスク実行器のデモ
    print("\n\n📋 レジリエントタスク実行")
    print("-" * 40)

    def sample_task(success_rate=0.5):
        """成功率を指定できるサンプルタスク"""
        import random

        if random.random() < success_rate:
            return "タスク完了"
        raise Exception("タスク失敗")

    # 成功率30%のタスクを実行
    result = task_executor.execute_with_resilience(
        sample_task, args=(0.3,), task_id="demo_task_001"
    )

    print("\nタスク実行結果:")
    print(f"  状態: {result['status']}")
    print(f"  実行時間: {result['execution_time']:0.2f}秒")
    if result["status"] == "success":
        print(f"  結果: {result['result']}")
    else:
        print(f"  エラータイプ: {result['error_type']}")
        print(f"  エラー: {result['error']}")

    # 4.0 システムヘルスレポート
    print("\n\n📋 システムヘルスレポート")
    print("-" * 40)

    health = task_executor.get_health_report()
    print(f"\n生成時刻: {health['timestamp']}")

    if health["error_patterns_24h"]:
        print("\n24時間のエラーパターン:")
        for error_type, count in health["error_patterns_24h"].items():
            print(f"  - {error_type}: {count}件")
    else:
        print("\n24時間のエラー: なし")

    if health["recommendations"]:
        print("\n推奨事項:")
        for rec in health["recommendations"]:
            print(f"  ⚠️  {rec}")

    print("\n" + "=" * 60)
    print("✅ デモ完了！")
    print("\n💡 使用方法:")
    print("1.0 @smart_retry デコレーターで自動リトライ")
    print("2.0 task_executor.execute_with_resilience() で安全実行")
    print("3.0 エラー履歴は自動的に記録・分析されます")
    print("=" * 60)


if __name__ == "__main__":
    main()

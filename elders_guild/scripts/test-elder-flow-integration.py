#!/usr/bin/env python3
"""
Elder Flow統合テスト（実際のElder Flow実行版）
Created: 2025-01-20
Author: Claude Elder

修正されたElder Flowシステムの統合テストを実行
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.claude_elder_request_processor import process_claude_elder_input


async def test_elder_flow_command():
    """Elder Flowコマンドの動作確認"""
    print("🔧 Elder Flowコマンド動作確認")
    print("=" * 60)

    # elder-flow statusコマンドをテスト
    try:
        result = subprocess.run(
            ["python3", f"{project_root}/scripts/elder-flow", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            print("✅ elder-flow status コマンド成功")
            return True
        else:
            print("❌ elder-flow status コマンド失敗")
            print(f"エラー: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ コマンド実行エラー: {e}")
        return False


async def test_simple_elder_flow():
    """シンプルなElder Flow実行テスト"""
    print("\n🧪 シンプルなElder Flow実行テスト")
    print("=" * 60)

    test_task = "テスト用のシンプルなタスク"

    try:
        # Elder Flow直接実行
        result = subprocess.run(
            [
                "python3",
                f"{project_root}/scripts/elder-flow",
                "execute",
                test_task,
                "--priority",
                "low",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_root),
        )

        print(f"終了コード: {result.returncode}")

        if result.stdout:
            print("標準出力:")
            print(result.stdout[:500])  # 最初の500文字

        if result.stderr:
            print("エラー出力:")
            print(result.stderr[:500])  # 最初の500文字

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Elder Flow実行エラー: {e}")
        return False


async def test_auto_flow_integration():
    """自動Elder Flow統合テスト（簡易版）"""
    print("\n🧪 自動Elder Flow統合テスト")
    print("=" * 60)

    # テストケース（簡易版）
    test_cases = [
        ("OAuth2.0認証システムを実装してください", True),
        ("help", False),
        ("バグを修正してください", True),
        ("現在の状況を説明してください", False),
    ]

    success_count = 0

    for test_input, should_apply in test_cases:
        print(f"\n📋 テスト: {test_input}")

        try:
            result = await process_claude_elder_input(test_input)
            actual_applied = not result["should_continue_normal_processing"]

            if actual_applied == should_apply:
                print(f"✅ 期待通り: {'Elder Flow適用' if actual_applied else '通常処理'}")
                success_count += 1
            else:
                print(f"❌ 期待と異なる: {'Elder Flow適用' if actual_applied else '通常処理'}")

        except Exception as e:
            print(f"❌ エラー: {e}")

    print(f"\n📊 結果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)


async def main():
    """メインテスト実行"""
    print("🏛️ Claude Elder Auto Flow Complete Integration Test")
    print("🤖 クロードエルダー自動Elder Flow完全統合テスト")
    print()

    # 各テストを実行
    elder_flow_ok = await test_elder_flow_command()

    if elder_flow_ok:
        simple_ok = await test_simple_elder_flow()
        auto_flow_ok = await test_auto_flow_integration()

        print("\n" + "=" * 60)
        print("📊 統合テスト結果")
        print(f"Elder Flowコマンド: {'✅ OK' if elder_flow_ok else '❌ NG'}")
        print(f"シンプル実行: {'✅ OK' if simple_ok else '❌ NG'}")
        print(f"自動適用: {'✅ OK' if auto_flow_ok else '❌ NG'}")

        if elder_flow_ok and auto_flow_ok:
            print("\n✅ 主要機能は正常に動作しています")
            return 0
    else:
        print("\n❌ Elder Flowコマンドに問題があります")
        print("依存関係の問題は解決されましたが、他の問題がある可能性があります")

    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

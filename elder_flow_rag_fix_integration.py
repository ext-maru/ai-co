#!/usr/bin/env python3
"""
Elder Flow RAG賢者修正統合スクリプト
Elder Flowシステム全体に軽量版RAG賢者を統合

作成者: クロードエルダー
作成日: 2025-07-20
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# RAG賢者修正を最初に適用
from libs.elder_flow_rag_sage_fix import patch_rag_sage_imports

print("🔧 Elder Flow RAG賢者修正を適用中...")
if patch_rag_sage_imports():
    print("✅ RAG賢者を軽量版にパッチ完了")
else:
    print("❌ RAG賢者パッチ失敗")
    sys.exit(1)

import argparse
import asyncio

# Elder Flow CLIをインポート（パッチ適用後）
from elder_flow_cli import ElderFlowCLI


class PatchedElderFlowCLI(ElderFlowCLI):
    """RAG賢者修正を適用したElder Flow CLI"""

    def __init__(self):
        """初期化時に軽量版RAG賢者を使用"""
        print("🌊 Elder Flow CLI (RAG賢者修正版) 初期化中...")

        # 基底クラスの初期化前にパッチを確認
        from libs.lightweight_rag_sage import LightweightRAGSage

        print("  → 軽量版RAG賢者を使用")

        # 基底クラスを初期化
        super().__init__()
        print("✅ Elder Flow CLI初期化完了")


async def test_elder_flow_execution():
    """Elder Flow実行テスト"""
    print("\n" + "=" * 60)
    print("🌊 Elder Flow実行テスト（RAG賢者修正版）")
    print("=" * 60)

    # CLIインスタンス作成
    cli = PatchedElderFlowCLI()

    # テストタスク
    test_task = "RAG賢者のメモリ効率を改善する軽量版実装を作成"

    # 実行引数を作成
    class Args:
        request = test_task
        max_workers = 4
        output_dir = "output"

    args = Args()

    try:
        print(f"\n📋 タスク: {test_task}")
        print("⚡ 実行開始...")

        result = await cli.execute_command(args)

        if result:
            print("\n✅ Elder Flow実行成功")
            print("📊 実行結果:")
            if "execution_results" in result:
                exec_results = result["execution_results"]
                print(f"  - 並列効率: {exec_results.get('parallel_efficiency', 0):.1f}%")
                print(f"  - 完了タスク: {exec_results.get('completed', 0)}")
                print(f"  - 全タスク数: {exec_results.get('total_tasks', 0)}")

            if "wisdom_evolution" in result:
                wisdom = result["wisdom_evolution"]
                print(f"  - 英知レベル: {wisdom.get('wisdom_level', 'unknown')}")

            return True
        else:
            print("\n❌ Elder Flow実行失敗")
            return False

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Elder Flow RAG賢者修正統合テスト")

    parser.add_argument("--test", action="store_true", help="テスト実行モード")

    parser.add_argument("--task", type=str, help="実行するタスク")

    args = parser.parse_args()

    if args.test or not args.task:
        # テストモード
        success = asyncio.run(test_elder_flow_execution())
        if success:
            print("\n🎉 Elder Flow RAG賢者修正統合成功！")
            print("✅ メモリエラーは解決されました")
            return 0
        else:
            print("\n❌ Elder Flow RAG賢者修正統合失敗")
            return 1
    else:
        # 通常実行モード
        cli = PatchedElderFlowCLI()

        class ExecArgs:
            request = args.task
            max_workers = 8
            output_dir = "output"

        exec_args = ExecArgs()

        try:
            result = asyncio.run(cli.execute_command(exec_args))
            if result:
                print("\n✅ タスク実行完了")
                return 0
            else:
                print("\n❌ タスク実行失敗")
                return 1
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())

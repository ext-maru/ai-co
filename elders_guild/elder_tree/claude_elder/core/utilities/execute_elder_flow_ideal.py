#!/usr/bin/env python3
"""
Elder Flow理想実装実行スクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_flow_orchestrator import ElderFlowOrchestrator


async def main():
    """Elder Flow理想実装プロジェクトの実行"""
    print("🌊 Elder Flow理想実装プロジェクト開始")
    print("=" * 60)

    orchestrator = ElderFlowOrchestrator()

    # Elder Flow理想実装タスクの実行
    task_description = """
    Elder Flow理想実装プロジェクト - 根本からの改修

    目標:
    1.0 4賢者システムの実統合（モックから実装へ）
    2.0 エルダーサーバントの実コード生成機能
    3.0 品質ゲートの実測定実装
    4.0 Git自動化の実装
    5.0 Mind Reading Protocol統合

    要件:
    - 各賢者が実際のファイル/DBにアクセス
    - 実際のコード生成とテスト実行
    - 実際の品質測定とGit操作
    - 完全自動化された開発フロー
    """

    try:
        task_id = await orchestrator.execute_task(task_description, priority="high")
        print(f"\n✅ Elder Flow実行完了: Task ID {task_id}")

        # タスクの詳細を表示
        task = orchestrator.active_tasks.get(task_id)
        if task:
            print(f"\nタスク状態: {task.status.value}")
            print("\n実行ログ:")
            for log in task.logs[-10:]:  # 最後の10件のログを表示
                print(f"  [{log['level']}] {log['message']}")

    except Exception as e:
        print(f"\n❌ Elder Flow実行エラー: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

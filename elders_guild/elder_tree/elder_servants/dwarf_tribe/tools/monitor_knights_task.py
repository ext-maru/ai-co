#!/usr/bin/env python3
"""
騎士団タスク監視スクリプト

騎士団からの完了報告を監視し、適切な判断を支援する
"""

import json
import sys
import time
from datetime import datetime

sys.path.append("/home/aicompany/ai_co")

from libs.report_management import ReportManager

def monitor_task(task_id: str):
    """タスクを監視"""
    manager = ReportManager()

    print(f"\n🛡️ 騎士団タスク監視開始: {task_id}\n")
    print("=" * 60)

    # タスクの概要を表示
    overview = manager.get_task_overview(task_id)

    if overview["status"]:
        print(f"📋 タスク: {overview['status']['title']}")
        print(f"   優先度: {overview['status']['priority']}")
        print(f"   担当: {overview['status']['assignee']}")
        print(f"   期限: {overview['status']['expected_completion']}")
        print(f"   状態: {overview['status']['status']}")

    # サンプル完了報告（テスト用）
    print("\n💡 完了報告のサンプル:")
    print(
        """
騎士団が完了報告を提出する際は、以下のような形式で報告されます：

```python
report_data = {
    'status': 'completed',  # または 'partial', 'failed'

    'deliverables': [

    ],
    'metrics': {
        'lines_of_code': 1500,
        'test_coverage': 95,
        'functions_implemented': 12
    },
    'issues_encountered': [
        'RabbitMQ APIアクセスに権限問題があったが解決済み'
    ],
    'lessons_learned': [
        'psutilライブラリの制限事項を把握',
        'ログ解析の高速化にripgrepが有効'
    ],
    'next_steps': [
        'Phase 2の実装開始',
        'パフォーマンステストの実施',
        'Elder Council統合のテスト'
    ]
}
```
    """
    )

    print("\n📊 報告を受けた際の自動処理:")
    print("1.0 品質分析（完了度、明確性、詳細度を評価）")
    print("2.0 リスク評価（問題や未完了項目を分析）")
    print("3.0 次のアクション提案（デプロイ、テスト、改善など）")
    print("4.0 優先順位付けとタイムライン生成")

    print("\n" + "=" * 60)
    print("⏳ 騎士団からの完了報告を待機中...")

def simulate_completion_report(task_id: str):
    """完了報告のシミュレーション（テスト用）"""
    manager = ReportManager()

    print("\n📝 完了報告シミュレーション開始...")

    # サンプル報告データ
    report_data = {
        "status": "completed",

Phase 1の全要件を達成：
- 基本的なシステム診断機能
- Worker健康状態の詳細分析
- スケーリング失敗の診断機能
- 診断レポートの生成

Worker Health Monitorのスケーリング分析失敗の原因を特定し、
診断ツールで問題を検出できるようになりました。""",
        "deliverables": [

        ],
        "metrics": {
            "lines_of_code": 1847,
            "test_coverage": 92.5,
            "functions_implemented": 15,
            "execution_time_hours": 18,
        },
        "issues_encountered": [
            "RabbitMQ管理APIの権限設定で一時的な遅延",
            "ログファイルのサイズが大きい場合のパフォーマンス問題",
        ],
        "lessons_learned": [
            "psutilライブラリはWSL2環境で一部制限があることを発見",
            "ripgrepを使用することで大規模ログの解析が100倍高速化",
            "Worker Health Monitorのスケーリング分析失敗は設定キーの欠落が原因",
        ],
        "next_steps": [

            "Phase 2の自動問題検出機能の実装開始",
            "Elder Council統合のためのAPI実装",
        ],
    }

    # 報告を提出
    result = manager.submit_report(task_id, report_data)

    if result["success"]:
        print("✅ 完了報告を受理しました")

        # 分析結果を表示
        if "analysis" in result:
            analysis = result["analysis"]
            print(f"\n📊 品質スコア:")
            quality = analysis["quality_score"]
            print(f"   総合: {quality['overall']:0.1f}%")
            print(f"   完全性: {quality['completeness']:0.1f}%")
            print(f"   明確性: {quality['clarity']:0.1f}%")

            print(f"\n✅ 成功指標:")
            for indicator in analysis["success_indicators"][:3]:
                print(f"   - {indicator}")

        # 決定内容を表示
        if "decision" in result:
            decision = result["decision"]
            print(f"\n🎯 推奨アクション:")
            for i, action in enumerate(decision["recommended_actions"][:3]):
                print(f"   {i+1}. {action['title']}")
                print(f"      理由: {action['rationale']}")

            print(f"\n⏱️ タイムライン:")
            timeline = decision["timeline"]
            if timeline["immediate"]:
                print(f"   即座（24時間以内）: {', '.join(timeline['immediate'])}")
            if timeline["short_term"]:
                print(f"   短期（1週間以内）: {', '.join(timeline['short_term'])}")

            print(f"\n🔍 信頼度: {decision['confidence_level']*100:0.1f}%")

    return result

if __name__ == "__main__":
    # 騎士団タスクIDを指定

    # タスクを監視
    monitor_task(task_id)

    # シミュレーションを実行するか確認
    print("\n\n💡 完了報告のシミュレーションを実行しますか？")
    print("   （実際の騎士団からの報告を待つ場合は 'n' を入力）")

    try:
        response = input("\n実行しますか？ [Y/n]: ").strip().lower()
        if response != "n":
            simulate_completion_report(task_id)
    except KeyboardInterrupt:
        print("\n\n👋 監視を終了します")

#!/usr/bin/env python3
"""
実行済みコマンドの結果を直接表示
"""

import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_log_viewer import AILogViewer


def main():
    viewer = AILogViewer()

    print("=== 実行済みコマンドの結果 ===")
    print(f"確認時刻: {datetime.now()}")
    print("")

    # 待機
    print("10秒待機中...")
    time.sleep(10)

    # 最新のコマンドログを確認
    print("\n【最新のSlack関連コマンド実行結果】")
    print("-" * 80)

    latest_logs = viewer.get_latest_command_logs(30)

    # 重要なコマンドを探す
    important_commands = [
        "final_diagnosis_results",
        "check_test_message",
        "instant_status_check",
        "auto_fix_slack",
        "check_current_status",
    ]

    found_results = {}

    for log in latest_logs:
        for cmd in important_commands:
            if cmd in log["task"] and cmd not in found_results:
                found_results[cmd] = log

    # 結果表示
    for cmd_name, log in found_results.items():
        print(f"\n📋 {cmd_name}")
        print(f"   時刻: {log['timestamp']}")
        print(f"   状態: {'✅ 成功' if log['exit_code'] == 0 else '❌ 失敗'}")

        if log.get("path"):
            try:
                content = viewer.read_log(log["path"])
                if content:
                    # 重要な部分を抽出
                    lines = content.split("\n")
                    important_lines = []

                    for i, line in enumerate(lines):
                        if any(
                            keyword in line
                            for keyword in [
                                "✅ 動作中",
                                "❌ 停止中",
                                "✅ 過去3分のメッセージ数:",
                                "⭐ このメッセージは処理対象",
                                "タスク化",
                                "主要問題:",
                                "Workerは活発に動作中",
                                "エラー数",
                                "問題の特定",
                            ]
                        ):
                            important_lines.append(line)
                            # 次の数行も含める
                            for j in range(1, 4):
                                if i + j < len(lines):
                                    important_lines.append(lines[i + j])

                    if important_lines:
                        print("   重要な結果:")
                        for line in important_lines[:10]:  # 最大10行
                            print(f"     {line}")
            except Exception as e:
                print(f"   ログ読み取りエラー: {str(e)}")

    # 現在の状態サマリー
    print("\n【現在の状態サマリー】")
    print("-" * 80)

    # 最新の状態を判定
    worker_status = "不明"
    message_status = "不明"
    task_status = "不明"

    for cmd_name, log in found_results.items():
        if log.get("path"):
            try:
                content = viewer.read_log(log["path"])
                if "✅ 動作中" in content and "Slack Polling Worker" in content:
                    worker_status = "動作中"
                elif "❌ 停止中" in content and "Slack Polling Worker" in content:
                    worker_status = "停止中"

                if "✅ 過去3分のメッセージ数:" in content:
                    message_status = "受信確認"

                if "タスク化の記録あり" in content:
                    task_status = "タスク化確認"
                elif "タスク化の記録なし" in content:
                    task_status = "タスク化なし"
            except:
                pass

    print(f"Slack Polling Worker: {worker_status}")
    print(f"メッセージ受信: {message_status}")
    print(f"タスク作成: {task_status}")

    print("\n【診断結果】")
    if worker_status == "停止中":
        print("❌ Slack Polling Workerが動作していません")
        print("   → 自動修正コマンドが実行されているはずです")
    elif message_status != "受信確認":
        print("❌ Slackメッセージが受信できていません")
        print("   → Bot Token/権限の問題の可能性")
    elif task_status == "タスク化なし":
        print("⚠️  メッセージは受信しているがタスク化されていません")
        print("   → 処理ロジックの問題の可能性")
    else:
        print("✅ 基本的な機能は動作しているようです")

    print("\n確認完了！")


if __name__ == "__main__":
    main()

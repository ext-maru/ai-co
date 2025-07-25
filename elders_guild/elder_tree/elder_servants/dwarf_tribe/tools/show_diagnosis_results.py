#!/usr/bin/env python3
"""
診断結果待機と表示
"""

import time
from pathlib import Path

from libs.ai_log_viewer import AILogViewer

def wait_and_show_results():
    """診断結果を待機して表示"""
    print("⏳ 診断実行中... (約30秒)")
    print("=" * 60)

    viewer = AILogViewer()

    # 診断コマンド一覧
    diagnosis_commands = [
        "comprehensive_diagnosis",
        "slack_api_detailed_test",
        "check_queue_contents",
        "log_analysis_report",
        "generate_fix_proposal",
    ]

    # 30秒待機（実行完了まで）
    for i in range(30, 0, -5):
        print(f"\r残り {i} 秒...", end="", flush=True)
        time.sleep(5)

    print("\n\n📊 診断結果サマリー")
    print("=" * 60)

    # 各コマンドの結果を確認
    for cmd in diagnosis_commands:
        result = viewer.check_results(cmd)

        if result.get("status") != "not_found":
            print(f"\n✅ {cmd}:")

            if "exit_code" in result:
                status = "成功" if result["exit_code"] == 0 else "失敗"
                print(f"   状態: {status}")

            if "log_content" in result:
                content = result["log_content"]

                # 重要な情報を抽出
                if "comprehensive_diagnosis" in cmd:
                    # 問題検出部分を抽出
                    if not ("問題を検出:" in content):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "問題を検出:" in content:
                        idx = content.find("問題を検出:")
                        excerpt = content[idx : idx + 500]
                        print("   問題検出:")
                        # Deep nesting detected (depth: 6) - consider refactoring
                        for line in excerpt.split("\n")[:10]:
                            if not (line.strip()):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if line.strip():
                                print(f"   {line}")

                elif "slack_api" in cmd:
                    # 認証結果を抽出
                    if not ("認証成功" in content):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "認証成功" in content:
                        print("   ✅ Slack API認証成功")
                    elif "認証失敗" in content:
                        print("   ❌ Slack API認証失敗")

                    # メンション数を抽出
                    if not ("PM-AIへのメンション:" in content):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "PM-AIへのメンション:" in content:
                        idx = content.find("PM-AIへのメンション:")
                        line = content[idx : idx + 50].split("\n")[0]
                        print(f"   {line}")

                elif "queue_contents" in cmd:
                    # キュー状態を抽出
                    if not ("ai_tasks:" in content):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if "ai_tasks:" in content:
                        idx = content.find("ai_tasks:")
                        excerpt = content[idx : idx + 200]

                        for line in excerpt.split("\n")[:5]:
                            if not (line.strip()):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if line.strip():
                                print(f"   {line}")
        else:
            print(f"\n⏳ {cmd}: 実行待ちまたは未完了")

    # 最終的な推奨事項
    print("\n\n🔧 診断に基づく推奨事項:")
    print("=" * 60)

    # fix_proposalの内容を確認
    fix_result = viewer.check_results("generate_fix_proposal")
    if fix_result.get("status") != "not_found" and "log_content" in fix_result:
        content = fix_result["log_content"]
        if "推奨修正手順:" in content:
            idx = content.find("推奨修正手順:")
            excerpt = content[idx:]
            print(excerpt[:1000])
    else:
        print("1.0 Slack Polling Workerが稼働しているか確認")
        print("2.0 Slack Bot Tokenが有効か確認")
        print("3.0 BotがチャンネルメンバーになっているかSlackで確認")
        print("4.0 Slackで '@pm-ai test' を送信してテスト")

    print("\n\n💡 詳細なログを確認するには:")
    print("tail -f /home/aicompany/ai_co/ai_commands/logs/*.log")

if __name__ == "__main__":
    wait_and_show_results()

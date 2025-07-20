#!/usr/bin/env python3
"""
Slack PM-AI診断結果レポート生成と通知
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from datetime import datetime

from libs.slack_notifier import SlackNotifier


def generate_diagnosis_report():
    """診断結果レポート生成"""
    print("📋 診断結果レポート生成")
    print("=" * 60)

    report = []
    report.append("🔍 Slack PM-AI診断レポート")
    report.append(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # 1. プロセス状態
    import subprocess

    ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    slack_running = "slack_polling_worker.py" in ps_result.stdout

    report.append("1️⃣ プロセス状態:")
    report.append(f"   Slack Polling Worker: {'✅ 稼働中' if slack_running else '❌ 停止'}")

    # 2. 最新ログ確認
    log_path = Path("/home/aicompany/ai_co/logs/slack_polling_worker.log")
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines

        errors = [
            line for line in recent_lines if "ERROR" in line or "error" in line.lower()
        ]
        mentions = [
            line
            for line in recent_lines
            if "メンション" in line or "mention" in line.lower()
        ]

        report.append("")
        report.append("2️⃣ ログ分析:")
        report.append(f"   エラー数: {len(errors)}")
        report.append(f"   メンション処理: {len(mentions)}件")

        if errors:
            report.append("   最新エラー:")
            for err in errors[-2:]:
                report.append(f"   - {err.strip()[:80]}")

    # 3. キュー状態
    queue_result = subprocess.run(
        ["sudo", "rabbitmqctl", "list_queues", "name", "messages"],
        capture_output=True,
        text=True,
    )

    if queue_result.returncode == 0:
        report.append("")
        report.append("3️⃣ キュー状態:")
        for line in queue_result.stdout.strip().split("\n"):
            if "ai_tasks" in line:
                parts = line.split("\t")
                if len(parts) == 2:
                    count = int(parts[1])
                    report.append(f"   ai_tasks: {count}件")
                    if count > 0:
                        report.append(f"   ⚠️  未処理タスクあり")

    # 4. 推奨アクション
    report.append("")
    report.append("4️⃣ 推奨アクション:")

    if not slack_running:
        report.append("   → Slack Polling Worker再起動が必要")
        report.append("   → tmux new-window -t ai_company -n slack_polling")

    if errors:
        report.append("   → エラー原因の調査が必要")
        report.append("   → Bot Token/Channel ID確認")

    if not mentions:
        report.append("   → Slackで @pm-ai をメンションしてテスト")

    # レポート出力
    report_text = "\n".join(report)
    print(report_text)

    # Slack通知
    try:
        notifier = SlackNotifier()
        notifier.send_message(report_text)
        print("\n✅ Slackに診断レポートを送信しました")
    except Exception as e:
        print(f"\n⚠️  Slack通知失敗: {str(e)}")

    # ファイル保存
    report_file = Path("/home/aicompany/ai_co/diagnosis_report.txt")
    with open(report_file, "w") as f:
        f.write(report_text)
    print(f"\n📄 レポート保存: {report_file}")


if __name__ == "__main__":
    generate_diagnosis_report()

#!/usr/bin/env python3
"""
Slack診断ログの監視
数秒ごとに更新を確認
"""

import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.ai_command_helper import AICommandHelper
from libs.ai_log_viewer import AILogViewer


def main():
    """mainメソッド"""
    helper = AICommandHelper()
    viewer = AILogViewer()

    print("=== Slack診断ログ監視 ===")
    print(f"開始時刻: {datetime.now()}")
    print("\n数秒後に結果が表示されます...\n")

    # 10秒待つ（AI Command Executorの実行を待つ）
    time.sleep(10)

    # 最新のログを確認
    print("最新の実行ログ:")
    print("-" * 60)

    # コマンドログ確認
    latest_logs = viewer.get_latest_command_logs(5)
    for log in latest_logs:
        if "slack" in log["task"].lower():
            print(f"\n📋 {log['task']} ({log['timestamp']})")
            print(f"   Exit Code: {log['exit_code']}")
            if log["exit_code"] == 0:
                print("   ✅ 成功")
            else:
                print("   ❌ 失敗")

    # 詳細ログ取得
    monitor_script = """#!/bin/bash
cd /home/aicompany/ai_co

echo "=== 最新のSlack関連ログ ==="
echo ""

# 1. 最新のコマンド実行ログ
echo "1. 最新のコマンドログ:"
ls -lt ai_commands/logs/*slack*.log 2>/dev/null | head -5

echo ""
echo "2. check_results_nowの結果:"
if [ -f ai_commands/logs/check_slack_auto*.log ]; then
    LATEST_LOG=$(ls -t ai_commands/logs/check_slack_auto*.log 2>/dev/null | head -1)
    echo "ファイル: $LATEST_LOG"
    echo "内容（問題特定部分）:"
    grep -A 10 "問題の特定" "$LATEST_LOG" 2>/dev/null | head -20
fi

echo ""
echo "3. Polling Worker状態:"
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ Slack Polling Worker動作中"
    echo "最新ログ:"
    tail -10 logs/slack_polling_worker.log 2>/dev/null
else
    echo "❌ Slack Polling Worker停止中"
fi

echo ""
echo "4. 処理されたメッセージ:"
if [ -f db/slack_messages.db ]; then
    sqlite3 db/slack_messages.db "SELECT COUNT(*) as total FROM processed_messages \
        WHERE text LIKE '%pm-ai%';" 2>/dev/null
fi
"""

    cmd_id = helper.create_bash_command(monitor_script, "monitor_slack_logs")
    print(f"\nログ監視コマンドを作成: {cmd_id}")

    # 結果待ち
    time.sleep(10)

    result = helper.check_results("monitor_slack_logs")
    if result:
        log_content = helper.get_latest_log("monitor_slack_logs")
        if log_content:
            print("\n=== 監視結果 ===")
            print("=" * 80)
            print(log_content)
            print("=" * 80)

    print("\n診断完了！")
    print("\n次のアクション:")
    print("1. Slack Polling Workerが停止している場合 → 起動が必要")
    print("2. メッセージが取得できていない場合 → Bot Token/権限確認")
    print(
        "3. メッセージは取得できているがタスク化されない場合 → ワーカーのログ詳細確認"
    )


if __name__ == "__main__":
    main()

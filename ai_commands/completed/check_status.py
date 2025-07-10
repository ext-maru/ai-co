#!/usr/bin/env python3
"""
システム状態確認
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper
import time

helper = AICommandHelper()

# 状態確認コマンド
status_check = """#!/bin/bash
cd /home/aicompany/ai_co

echo "🔍 Elders Guild システム状態確認"
echo "==============================="
echo ""

# 10秒待機（起動処理完了待ち）
echo "⏳ 起動処理の完了を待機中..."
sleep 10

echo ""
echo "📊 ワーカープロセス状態:"
echo "------------------------"
ps aux | grep -E "(pm_worker|task_worker|result_worker|polling_worker|ai_command_executor)" | grep -v grep | while read line; do
    echo "$line" | awk '{print "✅", $11, "PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}'
done

echo ""
echo "🐰 RabbitMQ状態:"
echo "----------------"
sudo rabbitmqctl status | grep -A 5 "Status" | head -n 6 || echo "RabbitMQ状態取得失敗"

echo ""
echo "📝 最新ログ確認:"
echo "---------------"

# PMWorkerのログ（最新5行）
echo "PMWorker:"
tail -n 5 logs/pm_worker.log | sed 's/^/  /'

echo ""

# エラーチェック
echo "⚠️  エラーチェック:"
echo "-----------------"
grep -i error logs/pm_worker.log | tail -n 3 | sed 's/^/  /' || echo "  エラーなし"

echo ""
echo "✅ 状態確認完了"
echo ""
echo "📋 Slackチャンネルを確認してください:"
echo "  - #ai-company-notifications (再起動通知)"
echo "  - #ai-company-scaling (スケーリングテスト)"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=status_check,
    command_id="check_system_status"
)

print("✅ システム状態確認コマンドを作成しました")
print("手動再起動の15秒後に自動実行されます")

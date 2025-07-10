#!/usr/bin/env python3
"""
Elders Guild システム手動再起動
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# 手動再起動コマンド
manual_restart = """#!/bin/bash
cd /home/aicompany/ai_co

echo "🔧 Elders Guild 手動再起動"
echo "======================="
echo ""

# 現在のプロセス状態確認
echo "📊 現在のワーカー状態:"
echo "-----------------------"
ps aux | grep -E "(pm_worker|task_worker|result_worker|polling_worker)" | grep -v grep || echo "実行中のワーカーなし"

echo ""
echo "🛑 プロセス停止中..."

# 全ワーカーを停止
pkill -f "pm_worker.py" 2>/dev/null
pkill -f "task_worker.py" 2>/dev/null
pkill -f "result_worker.py" 2>/dev/null
pkill -f "polling_worker.py" 2>/dev/null
pkill -f "ai_command_executor.py" 2>/dev/null

# 少し待機
sleep 2

# 残っているプロセスを強制終了
pkill -9 -f "pm_worker.py" 2>/dev/null
pkill -9 -f "task_worker.py" 2>/dev/null
pkill -9 -f "result_worker.py" 2>/dev/null
pkill -9 -f "polling_worker.py" 2>/dev/null
pkill -9 -f "ai_command_executor.py" 2>/dev/null

echo "✅ プロセス停止完了"
echo ""

# RabbitMQの状態確認
echo "🐰 RabbitMQ状態確認:"
sudo systemctl status rabbitmq-server --no-pager | head -n 5 || echo "RabbitMQ状態確認失敗"

# RabbitMQが停止していたら起動
if ! sudo systemctl is-active --quiet rabbitmq-server; then
    echo "RabbitMQ起動中..."
    sudo systemctl start rabbitmq-server
    sleep 3
fi

echo ""
echo "🚀 ワーカー起動中..."
echo ""

# 各ワーカーを起動
source venv/bin/activate

# PMWorker（チャンネル別通知対応版）
echo "1. PMWorker起動..."
nohup python3 workers/pm_worker.py > logs/pm_worker.log 2>&1 &
PM_PID=$!
echo "   PID: $PM_PID"

sleep 2

# TaskWorker
echo "2. TaskWorker起動..."
nohup python3 workers/task_worker.py > logs/task_worker.log 2>&1 &
TASK_PID=$!
echo "   PID: $TASK_PID"

sleep 1

# ResultWorker
echo "3. ResultWorker起動..."
nohup python3 workers/result_worker.py > logs/result_worker.log 2>&1 &
RESULT_PID=$!
echo "   PID: $RESULT_PID"

sleep 1

# PollingWorker
echo "4. PollingWorker起動..."
nohup python3 workers/polling_worker.py > logs/polling_worker.log 2>&1 &
POLL_PID=$!
echo "   PID: $POLL_PID"

sleep 1

# AI Command Executor
echo "5. AI Command Executor起動..."
nohup python3 ai_command_executor.py > logs/ai_command_executor.log 2>&1 &
CMD_PID=$!
echo "   PID: $CMD_PID"

sleep 3

echo ""
echo "📊 起動確認:"
echo "------------"
ps aux | grep -E "(pm_worker|task_worker|result_worker|polling_worker|ai_command_executor)" | grep -v grep

echo ""
echo "✅ システム再起動完了！"
echo ""

# Slack通知テスト
echo "📨 Slack通知テスト送信中..."
python3 -c "
from libs.slack_channel_notifier import SlackChannelNotifier
from datetime import datetime

notifier = SlackChannelNotifier()

# システム再起動通知
notifier.send_to_channel(
    '#ai-company-notifications',
    f'🔄 Elders Guild システム再起動完了\\n時刻: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}\\nPMWorker: チャンネル別通知対応版'
)

# スケーリング通知動作確認
notifier.send_scaling_notification(
    action='up',
    current_workers=0,
    target_workers=1,
    queue_length=0,
    task_id='restart_test'
)

print('✅ Slack通知送信完了')
"

echo ""
echo "🎉 全ての起動処理が完了しました！"
echo ""
echo "ログ確認:"
echo "  tail -f logs/pm_worker.log"
echo "  tail -f logs/task_worker.log"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=manual_restart,
    command_id="manual_restart_system"
)

print("✅ 手動再起動コマンドを作成しました")
print("6秒後に自動実行されます...")
print("")
print("実行内容:")
print("1. 全ワーカープロセスの停止")
print("2. RabbitMQ状態確認")
print("3. 全ワーカーの起動")
print("4. Slack通知テスト")

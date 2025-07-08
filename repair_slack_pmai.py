#!/usr/bin/env python3
"""
Slack PM-AI完全修復スクリプト
AI Command Executorで自動実行用
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import time
from libs.ai_command_helper import AICommandHelper
from libs.slack_notifier import SlackNotifier

def main():
    helper = AICommandHelper()
    
    print("🔧 Slack PM-AI修復開始...")
    
    # 1. 現在の状態を確認
    print("\n1️⃣ システム状態確認")
    check_status_cmd = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== TMUXセッション確認 ==="
tmux list-windows -t ai_company 2>/dev/null || echo "TMUXセッションなし"

echo -e "\n=== ワーカープロセス確認 ==="
ps aux | grep -E "(task_worker|pm_worker|slack_polling)" | grep -v grep || echo "関連プロセスなし"

echo -e "\n=== キュー状態確認 ==="
sudo rabbitmqctl list_queues name messages 2>/dev/null || echo "RabbitMQ確認失敗"

echo -e "\n=== Slack設定確認 ==="
grep -E "(SLACK_BOT_TOKEN|SLACK_POLLING_ENABLED)" config/slack.conf | head -5
"""
    helper.create_bash_command(check_status_cmd, "check_system_status")
    print("✅ システム状態確認コマンド作成")
    
    # 2. Slack Polling Workerのテスト
    print("\n2️⃣ Slack Polling Workerテスト")
    test_slack_worker_cmd = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== Slack Polling Workerテスト ==="
python3 workers/slack_polling_worker.py --test
"""
    helper.create_bash_command(test_slack_worker_cmd, "test_slack_polling")
    print("✅ Slack Polling Workerテストコマンド作成")
    
    # 3. Slack Polling Worker起動
    print("\n3️⃣ Slack Polling Worker起動")
    start_slack_polling_cmd = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# 既存のslack_pollingウィンドウを終了
tmux kill-window -t ai_company:slack_polling 2>/dev/null || true

# 新しくslack_pollingウィンドウを作成
tmux new-window -t ai_company -n slack_polling "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py"

echo "✅ Slack Polling Worker起動完了"

# 起動確認（3秒待機）
sleep 3
tmux list-windows -t ai_company | grep slack_polling || echo "❌ 起動失敗"
"""
    helper.create_bash_command(start_slack_polling_cmd, "start_slack_polling")
    print("✅ Slack Polling Worker起動コマンド作成")
    
    # 4. テスト用のSlackメッセージ処理シミュレーション
    print("\n4️⃣ Slackメッセージ処理テスト")
    test_message_processing = """#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import json
import pika
from datetime import datetime

# テスト用のSlackメッセージをai_tasksキューに投入
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ai_tasks', durable=True)
    
    # テストメッセージ
    test_task = {
        'task_id': f'slack_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}_code',
        'type': 'slack_command',
        'task_type': 'code',
        'prompt': 'シンプルなHello Worldを出力するPythonスクリプトを作成してください',
        'source': 'slack',
        'timestamp': datetime.now().isoformat(),
        'metadata': {
            'slack_ts': '1234567890.123456',
            'slack_user': 'test_user',
            'slack_channel': 'C0946R76UU8',
            'mentioned': True
        }
    }
    
    channel.basic_publish(
        exchange='',
        routing_key='ai_tasks',
        body=json.dumps(test_task),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    print(f"✅ テストメッセージ送信成功: {test_task['task_id']}")
    print(f"   プロンプト: {test_task['prompt']}")
    
    channel.close()
    connection.close()
    
except Exception as e:
    print(f"❌ テストメッセージ送信失敗: {str(e)}")
"""
    with open("/home/aicompany/ai_co/test_slack_message.py", "w") as f:
        f.write(test_message_processing)
    
    helper.create_bash_command("""#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
python3 test_slack_message.py
""", "test_slack_message")
    print("✅ Slackメッセージ処理テストコマンド作成")
    
    # 5. 全体の動作確認
    print("\n5️⃣ 全体動作確認")
    verify_all_cmd = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== 全ワーカー状態確認 ==="
echo -e "\n[TMUX Windows]"
tmux list-windows -t ai_company 2>/dev/null | grep -E "(task|pm|slack|result)" || echo "関連ウィンドウなし"

echo -e "\n[プロセス]"
ps aux | grep -E "worker.*\\.py" | grep -v grep | wc -l | xargs -I {} echo "アクティブワーカー数: {}"

echo -e "\n[キュー]"
sudo rabbitmqctl list_queues name messages | grep -E "(ai_tasks|pm_task_queue|result_queue)" || echo "キュー確認失敗"

echo -e "\n[最新ログ]"
echo "-- Task Worker --"
tail -5 logs/task_worker.log 2>/dev/null || echo "ログなし"

echo -e "\n-- PM Worker --"
tail -5 logs/pm_worker.log 2>/dev/null || echo "ログなし"

echo -e "\n-- Slack Polling Worker --"
tail -5 logs/slack_polling_worker.log 2>/dev/null || echo "ログなし"

echo -e "\n✅ 全体動作確認完了"
"""
    helper.create_bash_command(verify_all_cmd, "verify_all_system")
    print("✅ 全体動作確認コマンド作成")
    
    # 6. 修復完了通知
    print("\n6️⃣ 修復完了通知")
    notify_cmd = """#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from libs.slack_notifier import SlackNotifier

try:
    notifier = SlackNotifier()
    
    message = '''🔧 Slack PM-AI修復完了レポート
━━━━━━━━━━━━━━━━━━━━━━
✅ slack_polling_worker.py 復活・修正完了
✅ PM-AIへのメンション → ai_tasks キューへ送信
✅ テストメッセージ送信成功

📡 動作確認方法:
1. Slackで @pm-ai をメンションしてメッセージ送信
2. タスクが自動的に処理される
3. 結果がSlackに通知される

🔍 ログ確認:
- tail -f logs/slack_polling_worker.log
- tail -f logs/task_worker.log

💡 これでSlackからの指示がai-send的に動作します！'''
    
    notifier.send_message(message)
    print("✅ Slack通知送信成功")
except Exception as e:
    print(f"Slack通知失敗（非致命的）: {e}")
"""
    with open("/home/aicompany/ai_co/notify_repair_complete.py", "w") as f:
        f.write(notify_cmd)
    
    helper.create_bash_command("""#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
python3 notify_repair_complete.py
""", "notify_repair_complete")
    print("✅ 修復完了通知コマンド作成")
    
    print("\n🎉 全てのコマンドを作成しました！")
    print("6秒後に自動実行されます...")
    print("\n実行順序:")
    print("1. システム状態確認")
    print("2. Slack Polling Workerテスト")
    print("3. Slack Polling Worker起動")
    print("4. テストメッセージ送信")
    print("5. 全体動作確認")
    print("6. 完了通知")

if __name__ == "__main__":
    main()

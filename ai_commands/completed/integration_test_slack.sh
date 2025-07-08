#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🧪 統合テスト開始"
echo "=================="

# テストメッセージ送信
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")

import json
import pika
from datetime import datetime

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# 複数のテストメッセージ
test_messages = [
    {
        'prompt': 'フィボナッチ数列を計算するPython関数を作成してください',
        'type': 'code'
    },
    {
        'prompt': 'AI Companyの現在の状態をレポートしてください',
        'type': 'general'
    }
]

for i, msg in enumerate(test_messages):
    task = {
        'task_id': f'slack_integration_test_{i}_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{msg["type"]}',
        'type': 'slack_command',
        'task_type': msg['type'],
        'prompt': msg['prompt'],
        'source': 'slack_integration_test',
        'timestamp': datetime.now().isoformat(),
        'metadata': {
            'slack_ts': f'{time.time()}',
            'slack_user': 'integration_test',
            'slack_channel': 'test_channel',
            'mentioned': True
        }
    }
    
    channel.basic_publish(
        exchange='',
        routing_key='ai_tasks',
        body=json.dumps(task),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    print(f"✅ テストメッセージ{i+1}送信: {task['task_id']}")

channel.close()
connection.close()
EOF

echo -e "
📊 キュー状態確認"
sudo rabbitmqctl list_queues name messages | grep -E "(ai_tasks|result_queue)"

echo -e "
✅ 統合テスト完了"

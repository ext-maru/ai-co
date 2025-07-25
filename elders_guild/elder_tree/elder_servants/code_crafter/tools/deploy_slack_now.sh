#!/bin/bash
# Slack通知改善の完全自動デプロイ

cd /home/aicompany/ai_co

echo "🔄 Slack通知改善をデプロイ中..."

# 1. Result Workerを停止
echo "📍 Result Worker停止中..."
pkill -f "result_worker.py" || true
sleep 2

# 2. 新しいResult Workerを起動
echo "✨ 新しいResult Worker起動中..."
source venv/bin/activate
nohup python3 workers/result_worker.py > logs/result_worker.log 2>&1 &
WORKER_PID=$!
echo "✅ Result Worker起動 (PID: $WORKER_PID)"

# 3. 10秒待機（起動待ち）
echo "⏳ 起動待機中..."
sleep 10

# 4. テストメッセージ送信
echo "📨 テストメッセージ送信中..."
python3 - << 'EOF'
import pika
import json
from datetime import datetime

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    message = {
        "task_id": f"slack_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "task_type": "slack_improvement_test",
        "status": "completed",
        "worker_id": "worker-1",
        "rag_applied": True,
        "prompt": "Slack通知フォーマットを改善してください。現在のメッセージが長すぎて見切れたり、各項目がわかりにくいという問題があります。より簡潔で見やすいフォーマットに変更し、AI系コマンド（gf、ai-gitなど）を活用した実用的な通知にしてください。",
        "response": "Slack通知フォーマットを改善しました。主な変更点：\n\n1. **メイン通知を簡潔に**: 重要情報のみを表示し、見切れを防止\n2. **詳細はスレッドで**: プロンプト全文やレスポンス詳細はスレッドに分離\n3. **視覚的改善**: 絵文字とフォーマットで読みやすく\n4. **AI系コマンド活用**: gf、ai-git、ai-logsなどの実用的なコマンドを提供\n\n新しいフォーマットでは、メイン通知は5-10行程度に収まり、詳細情報はスレッドで確認できます。これにより、Slackのタイムラインがすっきりし、必要な情報にすぐアクセスできるようになりました。",
        "files_created": [
            "/home/aicompany/ai_co/workers/result_worker.py",
            "/home/aicompany/ai_co/libs/slack_notifier.py"
        ],
        "duration": 12.5
    }

    channel.basic_publish(
        exchange='',
        routing_key='results',
        body=json.dumps(message)
    )

    print(f"✅ テストメッセージ送信完了: {message['task_id']}")
    connection.close()
except Exception as e:
    print(f"❌ エラー: {e}")
EOF

# 5. ログ確認
echo ""
echo "📄 最新ログ:"
tail -n 20 logs/result_worker.log

echo ""
echo "🎉 デプロイ完了！"
echo "📱 Slackで新しい通知フォーマットを確認してください"
echo ""
echo "💡 エラー通知のテストを送信するには："
echo "   python3 test_error_notification.py"

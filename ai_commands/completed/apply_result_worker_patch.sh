#!/bin/bash
# ResultWorker日本語化パッチ適用

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🌏 ResultWorkerの日本語化を開始..."
echo ""

# パッチ適用
python3 scripts/patch_result_worker_japanese.py

echo ""
echo "🔄 ResultWorkerを再起動..."

# 現在のResultWorkerを停止
pkill -f "result_worker.py" 2>/dev/null

# 5秒待機
sleep 5

# ResultWorkerを再起動
cd /home/aicompany/ai_co
nohup python3 workers/result_worker.py > /dev/null 2>&1 &

echo "✅ ResultWorker再起動完了"
echo ""
echo "📝 テストタスクを送信..."

# テストタスク送信
python3 -c "
import sys
sys.path.insert(0, '/home/aicompany/ai_co')
from libs.task_sender import TaskSender

sender = TaskSender()
result = sender.send_task(
    prompt='日本語化テスト: 今日の日付と時刻を教えて',
    task_type='general'
)
print(f'テストタスクID: {result[\"task_id\"]}')
"

echo ""
echo "✅ 完了！数秒後にSlackで日本語の通知が表示されます"

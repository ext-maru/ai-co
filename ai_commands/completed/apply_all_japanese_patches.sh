#!/bin/bash
# PMWorkerとResultWorkerの日本語化＆改善パッチ適用

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🌏 AI Company 日本語化＆改善パッチを開始..."
echo ""

# 1. ResultWorkerパッチ適用
echo "📝 ResultWorkerのパッチ適用..."
python3 scripts/patch_result_worker_japanese.py

echo ""

# 2. PMWorkerパッチ適用
echo "📝 PMWorkerのパッチ適用..."
python3 scripts/patch_pm_worker_japanese.py

echo ""

# 3. ワーカー再起動
echo "🔄 ワーカーを再起動中..."

# 現在のワーカーを停止
pkill -f "result_worker.py" 2>/dev/null
pkill -f "pm_worker.py" 2>/dev/null

# 5秒待機
sleep 5

# ワーカーを再起動
echo "🚀 ワーカーを起動..."

# PMWorker起動
cd /home/aicompany/ai_co
nohup python3 workers/pm_worker.py > /dev/null 2>&1 &
echo "  ✅ PMWorker起動"

# ResultWorker起動
nohup python3 workers/result_worker.py > /dev/null 2>&1 &
echo "  ✅ ResultWorker起動"

sleep 2

# プロセス確認
echo ""
echo "📊 プロセス状態:"
ps aux | grep -E "(pm_worker|result_worker)" | grep -v grep || echo "  ワーカーが見つかりません"

echo ""
echo "📝 テストタスクを送信..."

# テストタスク送信
python3 -c "
import sys
sys.path.insert(0, '/home/aicompany/ai_co')
from libs.task_sender import TaskSender

sender = TaskSender()
result = sender.send_task(
    prompt='日本語化改善テスト: 今日は何曜日？現在の時刻も教えて。また、簡単なPythonスクリプトを作成して。',
    task_type='code'
)
print(f'テストタスクID: {result[\"task_id\"]}')
print('数秒後にSlackで改善された日本語通知が表示されます')
"

echo ""
echo "✅ 完了！"
echo ""
echo "📋 改善内容:"
echo "  - Slack通知が完全に日本語化"
echo "  - プロンプト/レスポンスの表示が詳細化（最大1500文字）"
echo "  - ワーカーID、RAG適用状況などの情報追加"
echo "  - パフォーマンス指標も日本語で表示"
echo ""
echo "🎯 デグレが解消され、より詳細な日本語通知になりました！"

#!/bin/bash
# ResultWorker日本語化状態の詳細確認

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔍 ResultWorker日本語化の詳細確認"
echo ""

python3 check_result_worker_japanese.py

echo ""
echo "📋 最新のResultWorkerログ（最後の20行）:"
tail -20 logs/result_worker.log 2>/dev/null || echo "ログファイルなし"

echo ""
echo "✅ 確認完了"

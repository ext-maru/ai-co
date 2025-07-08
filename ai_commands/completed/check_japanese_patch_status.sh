#!/bin/bash
# 日本語化パッチの状態確認（即座に実行）

cd /home/aicompany/ai_co

echo "🔍 日本語化パッチの適用状態を確認..."
echo "================================="
echo ""

# 1. 日本語メッセージ定義の確認
echo "📄 日本語メッセージ定義:"
if grep -q "MESSAGES_JA" workers/result_worker.py 2>/dev/null; then
    echo "  ✅ ResultWorker: 日本語メッセージ定義あり"
else
    echo "  ❌ ResultWorker: 日本語メッセージ定義なし"
fi

echo ""

# 2. PMWorkerの送信メソッド確認
echo "📤 PMWorker送信機能:"
if grep -q "_send_to_result_worker" workers/pm_worker.py 2>/dev/null; then
    echo "  ✅ PMWorker: ResultWorker転送機能あり"
else
    echo "  ❌ PMWorker: ResultWorker転送機能なし"
fi

echo ""

# 3. 実行中のワーカー確認
echo "🏃 実行中のワーカー:"
ps aux | grep "result_worker.py" | grep -v grep && echo "  ✅ ResultWorker: 実行中" || echo "  ❌ ResultWorker: 停止中"
ps aux | grep "pm_worker.py" | grep -v grep && echo "  ✅ PMWorker: 実行中" || echo "  ❌ PMWorker: 停止中"

echo ""

# 4. 最新のSlack通知内容を確認（もしログがあれば）
echo "📨 最新のSlack通知:"
if [ -f logs/result_worker.log ]; then
    grep -A5 "Slack notification" logs/result_worker.log | tail -10 || echo "  通知ログなし"
else
    echo "  ログファイルなし"
fi

echo ""
echo "================================="
echo "✅ 確認完了"
echo ""
echo "💡 ヒント:"
echo "  - パッチが未適用の場合: apply_all_japanese_patches.sh を実行"
echo "  - ワーカーが停止中の場合: ai-restart を実行"
echo "  - テストタスク送信: ai-send '日本語テスト' general"

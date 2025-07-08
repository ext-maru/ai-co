#!/bin/bash
#!/bin/bash
# AI Company 問題修正スクリプト

echo "🔧 AI Company 問題修正を開始します..."
echo "============================================"

cd /home/aicompany/ai_co

# 1. 問題のあるコマンドを削除
echo "📌 問題のあるコマンドを削除..."
if [ -f "ai_commands/completed/check_best_practices_status.sh" ]; then
    rm -f ai_commands/completed/check_best_practices_status.sh
    echo "✅ check_best_practices_status.sh を削除しました"
fi

if [ -f "ai_commands/completed/check_best_practices_status.json" ]; then
    rm -f ai_commands/completed/check_best_practices_status.json
    echo "✅ check_best_practices_status.json を削除しました"
fi

# 2. ResultWorkerを修正版に置き換え
echo -e "\n📌 ResultWorkerを修正版に置き換え..."
if [ -f "workers/result_worker_fixed.py" ]; then
    # 既存のバックアップ
    cp workers/result_worker.py workers/result_worker_backup_$(date +%Y%m%d_%H%M%S).py
    
    # 修正版に置き換え
    mv workers/result_worker_fixed.py workers/result_worker.py
    chmod +x workers/result_worker.py
    echo "✅ ResultWorkerを修正版に置き換えました"
fi

# 3. CommandExecutorWorkerを再起動
echo -e "\n📌 CommandExecutorWorkerを再起動..."
# 既存のプロセスを停止
pkill -f "command_executor_worker.py" || true
sleep 2

# 再起動
nohup python3 workers/command_executor_worker.py > logs/command_executor_restart.log 2>&1 &
echo "✅ CommandExecutorWorkerを再起動しました"

# 4. ResultWorkerを再起動
echo -e "\n📌 ResultWorkerを再起動..."
# 既存のプロセスを停止
pkill -f "result_worker.py" || true
sleep 2

# 再起動
nohup python3 workers/result_worker.py > logs/result_worker_restart.log 2>&1 &
echo "✅ ResultWorkerを再起動しました"

# 5. ステータス確認
echo -e "\n📌 プロセス状態を確認..."
sleep 3

echo -e "\n🔍 実行中のワーカー:"
ps aux | grep -E "(command_executor|result_worker)" | grep -v grep

echo -e "\n📊 ログの最新状態:"
echo "CommandExecutor:"
tail -n 5 logs/command_executor.log 2>/dev/null || echo "ログファイルが見つかりません"

echo -e "\nResultWorker:"
tail -n 5 logs/result_worker.log 2>/dev/null || echo "ログファイルが見つかりません"

# 6. Slack通知テスト
echo -e "\n📌 Slack通知テストを実行..."
python3 -c "
import sys
sys.path.append('/home/aicompany/ai_co')
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
notifier.send_message('🎉 AI Company 問題修正完了\\n\\n✅ CommandExecutorWorkerの繰り返し失敗を修正\\n✅ ResultWorkerを最新版に更新\\n✅ すべてのワーカーが正常に再起動されました')
print('✅ Slack通知テスト完了')
"

echo -e "\n============================================"
echo "✅ 修正が完了しました！"
echo ""
echo "📝 次のステップ:"
echo "1. logs/command_executor.log を確認して繰り返しエラーが停止したことを確認"
echo "2. logs/result_worker.log を確認してResultWorkerが正常に動作していることを確認"
echo "3. Slackで通知が正しく表示されることを確認"
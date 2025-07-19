#!/bin/bash
#!/bin/bash
# AI Company 状態確認スクリプト

echo "📊 AI Company 現在の状態確認"
echo "============================================"

cd /home/aicompany/ai_co

echo "🔍 実行中のワーカー:"
ps aux | grep -E "(command_executor|result_worker|pm_worker)" | grep -v grep | awk '{print $11, $12, $13}' | sort | uniq

echo -e "\n📋 AI Commandsの状態:"
echo "Pending: $(ls -1 ai_commands/pending/*.json 2>/dev/null | wc -l) 件"
echo "Running: $(ls -1 ai_commands/running/*.json 2>/dev/null | wc -l) 件"
echo "Completed: $(ls -1 ai_commands/completed/*.json 2>/dev/null | wc -l) 件"

echo -e "\n🚨 最新のエラーログ (command_executor):"
tail -n 10 logs/command_executor.log 2>/dev/null | grep -E "(ERROR|FAILED)" | tail -n 3

echo -e "\n✅ 最新の成功ログ (result_worker):"
tail -n 10 logs/result_worker.log 2>/dev/null | grep -E "(Result processed|SUCCESS)" | tail -n 3

echo -e "\n📝 問題のあるコマンドの確認:"
if [ -f "ai_commands/completed/check_best_practices_status.sh" ]; then
    echo "⚠️ check_best_practices_status.sh がまだ存在します"
else
    echo "✅ check_best_practices_status.sh は削除されています"
fi

echo -e "\n============================================"
echo "✅ 状態確認完了"

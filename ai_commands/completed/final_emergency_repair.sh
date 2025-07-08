#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔧 緊急修復開始"
echo "================"

# 1. 現在のプロセスを確認
echo ""
echo "1️⃣ 現在の状態:"
ps aux | grep -E "[c]ommand_executor|[w]atchdog" || echo "プロセスなし"

# 2. 古いセッションをクリーンアップ
echo ""
echo "2️⃣ 古いセッションをクリーンアップ:"
tmux kill-session -t command_executor 2>/dev/null || true
tmux kill-session -t executor_watchdog 2>/dev/null || true

# 3. Command Executorを起動
echo ""
echo "3️⃣ Command Executor起動:"
tmux new-session -d -s command_executor 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/command_executor_worker.py'
sleep 3

# 4. Watchdog起動
echo ""
echo "4️⃣ Watchdog起動:"
tmux new-session -d -s executor_watchdog 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/executor_watchdog.py'
sleep 2

# 5. 起動確認
echo ""
echo "5️⃣ 起動確認:"
ps aux | grep -E "[c]ommand_executor|[w]atchdog"
echo ""
tmux list-sessions | grep -E "command_executor|watchdog"

# 6. pendingファイル確認
echo ""
echo "6️⃣ Pendingファイル:"
ls -la /home/aicompany/ai_co/ai_commands/pending | head -10

echo ""
echo "✅ 修復完了"

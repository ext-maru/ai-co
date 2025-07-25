#!/bin/bash
# Claude CLI用実行スクリプト

echo "🔧 AI Company ai-restart 修正を実行します"
echo "========================================"

# 1. 新しいai-restartスクリプトを作成
echo "📝 新しいai-restartを作成中..."
sudo tee /usr/local/bin/ai-restart > /dev/null << 'EOF'
#!/bin/bash
echo "=================================================="
echo "🚀 AI Company システム再起動 - $(date '+%H:%M:%S')"
echo "=================================================="

# システム停止
echo -e "\n--- システム停止 ---"
echo "ℹ️  現在のシステムを停止しています..."
tmux kill-session -t ai_company 2>/dev/null && echo "✅ tmuxセッション停止完了" || echo "ℹ️  tmuxセッションは既に停止しています"
pkill -f "worker.py" 2>/dev/null
pkill -f "task_worker" 2>/dev/null
pkill -f "pm_worker" 2>/dev/null
pkill -f "result_worker" 2>/dev/null
rm -f /tmp/ai_command_executor.pid 2>/dev/null
echo "✅ プロセス停止完了"

# 3秒待機
echo -e "\nℹ️  3秒待機中..."
sleep 3

# システム起動
echo -e "\n--- システム起動 ---"
echo "ℹ️  システムを起動しています..."
cd /home/aicompany/ai_co
bash scripts/start_company.sh

echo -e "\n--- 再起動完了 ---"
echo "✅ システム再起動が完了しました！"
EOF

# 実行権限を付与
sudo chmod +x /usr/local/bin/ai-restart
echo "✅ ai-restart作成完了"

# 2. start_company.shを修正
echo -e "\n📝 start_company.shを修正中..."
cd /home/aicompany/ai_co/scripts
cp start_company.sh start_company.sh.backup_$(date +%Y%m%d_%H%M%S)
sed -i '/TestGeneratorWorker/,/C-m/d' start_company.sh
echo "✅ start_company.sh修正完了"

# 3. ai-startも修正
echo -e "\n📝 ai-startを作成中..."
sudo tee /usr/local/bin/ai-start > /dev/null << 'EOF'
#!/bin/bash
echo "🏢 AI Company を起動中..."
cd /home/aicompany/ai_co
if tmux has-session -t ai_company 2>/dev/null; then
    echo "⚠️  既にAI Companyが起動しています"
    exit 0
fi
bash scripts/start_company.sh
EOF
sudo chmod +x /usr/local/bin/ai-start
echo "✅ ai-start作成完了"

# 4. ai-stopも修正
echo -e "\n📝 ai-stopを作成中..."
sudo tee /usr/local/bin/ai-stop > /dev/null << 'EOF'
#!/bin/bash
echo "🛑 AI Company を停止中..."
tmux kill-session -t ai_company 2>/dev/null && echo "✅ tmuxセッション停止完了" || echo "ℹ️  tmuxセッションは既に停止しています"
pkill -f "worker.py" 2>/dev/null
rm -f /tmp/ai_command_executor.pid 2>/dev/null
echo "✅ AI Company 停止完了"
EOF
sudo chmod +x /usr/local/bin/ai-stop
echo "✅ ai-stop作成完了"

# 5. 動作確認
echo -e "\n🧪 動作確認..."
echo "ai-restart --help:"
ai-restart --help 2>&1 || echo "（ヘルプはありません）"

echo -e "\n✨ 修正完了！"
echo "テスト実行: ai-restart"

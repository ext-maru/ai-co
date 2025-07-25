#!/bin/bash
# PMWorkerをGit Flow対応版に更新するスクリプト

cd /home/aicompany/ai_co

echo "🔄 PMWorkerのGit Flow対応更新を開始..."

# 1. 現在のPMWorkerをバックアップ
if [ -f "workers/pm_worker.py" ]; then
    backup_file="workers/pm_worker.py.backup.$(date +%Y%m%d_%H%M%S)"
    cp workers/pm_worker.py "$backup_file"
    echo "✅ バックアップ作成: $backup_file"
fi

# 2. Git Flow対応版に置き換え
if [ -f "workers/pm_worker_gitflow.py" ]; then
    mv workers/pm_worker_gitflow.py workers/pm_worker.py
    echo "✅ PMWorkerをGit Flow対応版に更新"
else
    echo "❌ Git Flow対応版が見つかりません"
    exit 1
fi

# 3. PMWorkerを再起動
echo "🔄 PMWorkerを再起動中..."

# tmuxセッション内でPMWorkerを再起動
if tmux has-session -t ai_company 2>/dev/null; then
    # PMWorkerのプロセスを停止
    pkill -f "pm_worker.py" || true
    sleep 2

    # 新しいPMWorkerを起動
    tmux send-keys -t ai_company:1 "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/pm_worker.py" C-m
    echo "✅ PMWorker再起動完了"
else
    echo "⚠️ tmuxセッションが見つかりません。手動で再起動してください"
fi

# 4. Git Flow状態を確認
echo ""
echo "📊 Git Flow状態確認:"
git branch --show-current
git branch -a | grep -E "(main|master|develop)"

echo ""
echo "✅ PMWorkerのGit Flow対応更新が完了しました！"
echo ""
echo "🌊 これからのGit Flow:"
echo "  - AIタスク実行時: auto/task_XXX ブランチで作業"
echo "  - 完了後: 自動的に develop へマージ"
echo "  - リリース時: ai-git release で main へ"

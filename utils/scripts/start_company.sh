#!/bin/bash

# ヘルプ表示
show_help() {
    cat << EOF
start_company.sh - AI Company システム起動コマンド

使用方法:
    start_company.sh [オプション]

説明:
    AI Company システムを起動します。tmuxセッションを作成し、
    以下のコンポーネントを起動します:
    - PMワーカー
    - タスクワーカー (2つ)
    - 結果ワーカー
    - ダッシュボード (status.sh)
    - ログ監視

オプション:
    --help, -h          このヘルプを表示
    --status           システム状態を確認
    --stop             システムを停止

セッション接続:
    tmux attach -t ai_company

注意:
    - RabbitMQが事前に起動している必要があります
    - Python仮想環境は自動的にアクティベートされます
EOF
}

# 引数チェック
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

if [ "$1" = "--status" ]; then
    echo "🔍 AI Company システム状態確認"
    if tmux has-session -t ai_company 2>/dev/null; then
        echo "✅ tmuxセッション 'ai_company' が実行中"
        tmux list-windows -t ai_company
    else
        echo "❌ tmuxセッション 'ai_company' が見つかりません"
    fi
    exit 0
fi

if [ "$1" = "--stop" ]; then
    echo "🛑 AI Company システムを停止中..."
    tmux kill-session -t ai_company 2>/dev/null
    echo "✅ システムを停止しました"
    exit 0
fi

SESSION="ai_company"
PROJECT_DIR="$HOME/ai_co"

tmux kill-session -t $SESSION 2>/dev/null

echo "🏢 AI Company を起動中..."

tmux new-session -d -s $SESSION -n "dashboard"
tmux send-keys -t $SESSION:dashboard "cd $PROJECT_DIR && clear" C-m
tmux send-keys -t $SESSION:dashboard "watch -n 2 '$PROJECT_DIR/utils/scripts/status.sh'" C-m

# PMワーカー起動（追加）
tmux new-window -t $SESSION -n "pm-worker"
tmux send-keys -t $SESSION:pm-worker "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:pm-worker "python3 core/workers/pm_worker.py" C-m

# 既存ワーカー起動
tmux new-window -t $SESSION -n "worker-1"
tmux send-keys -t $SESSION:worker-1 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-1 "python3 core/workers/task_worker.py worker-1" C-m

tmux new-window -t $SESSION -n "worker-2"
tmux send-keys -t $SESSION:worker-2 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-2 "python3 core/workers/task_worker.py worker-2" C-m

tmux new-window -t $SESSION -n "result-worker"
tmux send-keys -t $SESSION:result-worker "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:result-worker "python3 core/workers/result_worker.py" C-m

tmux new-window -t $SESSION -n "logs"
tmux send-keys -t $SESSION:logs "cd $PROJECT_DIR/logs" C-m
tmux send-keys -t $SESSION:logs "tail -f *.log" C-m

echo "✅ AI Company 起動完了！"
echo "接続: tmux attach -t $SESSION"


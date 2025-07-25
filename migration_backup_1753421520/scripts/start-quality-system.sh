#!/bin/bash
# 品質管理システムの起動スクリプト

set -e

echo "🚀 AI Company 品質管理システムを起動します..."

# プロジェクトディレクトリ
PROJECT_DIR="/home/aicompany/ai_co"
cd "$PROJECT_DIR"

# 仮想環境の有効化
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ 仮想環境を有効化しました"
else
    echo "⚠️ 仮想環境が見つかりません"
fi

# 既存のワーカーを停止
echo "🛑 既存のワーカーを停止..."
pkill -f "pm_worker.py" || true
pkill -f "task_worker.py" || true
sleep 2

# tmuxセッション確認
if ! tmux has-session -t ai_quality 2>/dev/null; then
    echo "📺 tmuxセッション 'ai_quality' を作成..."
    tmux new-session -d -s ai_quality
fi

# 品質管理PMワーカーを起動
echo "🎯 品質管理PMワーカーを起動..."
tmux send-keys -t ai_quality:0 "cd $PROJECT_DIR && python3 workers/quality_pm_worker.py" C-m

# 新しいペインで品質対応TaskWorkerを起動
echo "📝 品質対応TaskWorkerを起動..."
tmux split-window -t ai_quality:0 -h
tmux send-keys -t ai_quality:0.1 "cd $PROJECT_DIR && python3 workers/quality_task_worker.py" C-m

# 既存のResultWorkerも起動（Slack通知用）
echo "📢 ResultWorkerを起動..."
tmux split-window -t ai_quality:0 -v
tmux send-keys -t ai_quality:0.2 "cd $PROJECT_DIR && python3 workers/result_worker.py" C-m

echo ""
echo "✅ 品質管理システムの起動が完了しました！"
echo ""
echo "📊 システム構成:"
echo "  - 品質管理PMワーカー: タスク結果の品質をチェック"
echo "  - 品質対応TaskWorker: フィードバックを受けて改善"
echo "  - ResultWorker: Slack通知"
echo ""
echo "🔍 ログ確認:"
echo "  tmux attach -t ai_quality"
echo ""
echo "📝 使用方法:"
echo "  ai-send \"要件\" code  # タスクを送信"
echo "  → PMが品質チェック → 不十分なら自動で再実行"
echo "  → 最大3回まで品質改善を試行"
echo ""
echo "📈 品質基準:"
echo "  - エラーハンドリングの実装"
echo "  - ログ出力の実装"
echo "  - AI Company規約の遵守"
echo "  - Slack通知の実装"
echo "  - docstring/コメントの追加"

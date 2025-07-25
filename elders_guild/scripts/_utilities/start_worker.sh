#!/bin/bash
# 🚀 AI Company 統一ワーカー起動スクリプト
# 4賢者システム提供

set -e

# プロジェクトルート設定
PROJECT_ROOT="/home/aicompany/ai_co"
cd "$PROJECT_ROOT"

# Python環境設定
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
source venv/bin/activate

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法: $0 <worker_script> [worker_args...]"
    echo "例: $0 workers/pm_worker.py --worker-id pm-001"
    exit 1
fi

WORKER_SCRIPT="$1"
shift  # 最初の引数を削除

# ワーカースクリプト存在確認
if [ ! -f "$WORKER_SCRIPT" ]; then
    echo "❌ エラー: $WORKER_SCRIPT が見つかりません"
    exit 1
fi

echo "🚀 ワーカー起動: $WORKER_SCRIPT"
echo "📂 作業ディレクトリ: $(pwd)"
echo "🐍 Python パス: $PYTHONPATH"

# ワーカー実行
python3 "$WORKER_SCRIPT" "$@"

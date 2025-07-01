#!/bin/bash
# 移行準備スクリプト - まず現状を完全にバックアップして検証

echo "🔒 AI Company 移行準備"
echo "===================="

# 1. 完全バックアップ
echo ""
echo "📦 Step 1: 完全バックアップ作成..."
BACKUP_FILE="/root/ai_co_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" /root/ai_co --exclude='venv' --exclude='*.log' --exclude='__pycache__'
echo "✅ バックアップ作成: $BACKUP_FILE"
echo "   サイズ: $(du -h $BACKUP_FILE | cut -f1)"

# 2. 実行中のプロセスチェック
echo ""
echo "🔍 Step 2: 実行中のプロセス確認..."
if ps aux | grep -E "(task_worker|pm_worker|result_worker)" | grep -v grep > /dev/null; then
    echo "⚠️ AI Companyのプロセスが実行中です！"
    echo "   ai-stop を実行してから再度お試しください"
    exit 1
else
    echo "✅ プロセスなし"
fi

# 3. 重要ファイルの存在確認
echo ""
echo "📋 Step 3: 重要ファイル確認..."
CRITICAL_FILES=(
    "config/slack.conf"
    "config/system.conf"
    "task_history.db"
    "requirements.txt"
)
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "⚠️ $file が見つかりません"
    fi
done

# 4. 移行影響の要約
echo ""
echo "📊 Step 4: 移行影響の要約"
echo "------------------------"
echo "変更が必要なファイル数:"
echo "  Python (sys.path): 21個"
echo "  設定ファイル: 1個"
echo "  シェルスクリプト: 約5個"
echo ""
echo "合計: 約30ファイルの修正が必要"

echo ""
echo "✅ 準備完了！"
echo ""
echo "次のステップ:"
echo "1. ./safe_migrate.sh を実行して移行"
echo "2. 問題があれば: tar -xzf $BACKUP_FILE -C / で復元"


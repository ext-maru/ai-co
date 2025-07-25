#!/bin/bash
# Git Branch Cleanup Script - エルダーズギルド
# ブランチの整理とクリーンアップを実行

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🧹 Git Branch Cleanup Script - エルダーズギルド"
echo "================================================"
echo ""

# 現在のブランチ数を表示
TOTAL_BRANCHES=$(git branch -a | grep -v HEAD | wc -l)
echo "📊 現在のブランチ総数: $TOTAL_BRANCHES"
echo ""

# Step 1: マージ済みローカルブランチの削除
echo "🗑️  Step 1: マージ済みローカルブランチの削除"
echo "----------------------------------------------"
MERGED_BRANCHES=$(git branch --merged main | grep -v "^\*" | grep -v "main" | wc -l)
if [ "$MERGED_BRANCHES" -gt 0 ]; then
    echo "マージ済みブランチ: $MERGED_BRANCHES 個"
    git branch --merged main | grep -v "^\*" | grep -v "main" | head -10
    echo ""
    read -p "これらのブランチを削除しますか? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch --merged main | grep -v "^\*" | grep -v "main" | xargs -r git branch -d
        echo "✅ マージ済みブランチを削除しました"
    fi
else
    echo "✨ マージ済みの削除可能なブランチはありません"
fi
echo ""

# Step 2: リモートで削除されたブランチの同期
echo "🔄 Step 2: リモートで削除されたブランチの同期"
echo "----------------------------------------------"
PRUNE_COUNT=$(git remote prune origin --dry-run 2>&1 | grep -c "would prune" || true)
if [ "$PRUNE_COUNT" -gt 0 ]; then
    echo "削除可能なリモート参照: $PRUNE_COUNT 個"
    git remote prune origin --dry-run
    echo ""
    read -p "これらの参照を削除しますか? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote prune origin
        echo "✅ リモート参照を同期しました"
    fi
else
    echo "✨ 削除可能なリモート参照はありません"
fi
echo ""

# Step 3: 古いブランチの確認
echo "📅 Step 3: 古いブランチの確認 (30日以上)"
echo "----------------------------------------------"
# 30日以上前のブランチを表示
OLD_BRANCHES=$(git for-each-ref --format='%(refname:short) %(committerdate:relative)' refs/heads/ | grep -E "(months|years) ago" | wc -l)
if [ "$OLD_BRANCHES" -gt 0 ]; then
    echo "30日以上前のブランチ: $OLD_BRANCHES 個"
    git for-each-ref --format='%(refname:short) %(committerdate:relative)' refs/heads/ | grep -E "(months|years) ago" | head -10
    echo ""
    echo "⚠️  これらのブランチは手動で確認後、必要に応じて削除してください"
else
    echo "✨ 30日以上前のブランチはありません"
fi
echo ""

# Step 4: auto-fixブランチの確認
echo "🤖 Step 4: auto-fixブランチの確認"
echo "----------------------------------------------"
AUTO_FIX_COUNT=$(git branch | grep -c "auto-fix" || true)
if [ "$AUTO_FIX_COUNT" -gt 0 ]; then
    echo "auto-fixブランチ: $AUTO_FIX_COUNT 個"
    git branch | grep "auto-fix" | head -10
    echo ""
    echo "💡 ヒント: マージ済みのauto-fixブランチは Step 1 で削除されます"
else
    echo "✨ auto-fixブランチはありません"
fi
echo ""

# 最終統計
echo "📊 最終統計"
echo "----------------------------------------------"
NEW_TOTAL=$(git branch -a | grep -v HEAD | wc -l)
CLEANED=$((TOTAL_BRANCHES - NEW_TOTAL))
echo "削除されたブランチ: $CLEANED 個"
echo "現在のブランチ総数: $NEW_TOTAL 個"
echo ""
echo "✅ クリーンアップ完了！"
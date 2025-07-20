#!/bin/bash
# Git Branch Aggressive Cleanup Script - エルダーズギルド
# より積極的なブランチクリーンアップを実行

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔥 Git Branch Aggressive Cleanup Script - エルダーズギルド"
echo "=========================================================="
echo ""

# 現在のブランチ数を表示
LOCAL_BRANCHES=$(git branch | wc -l)
REMOTE_BRANCHES=$(git branch -r | wc -l)
echo "📊 現在のブランチ数:"
echo "  - ローカル: $LOCAL_BRANCHES"
echo "  - リモート: $REMOTE_BRANCHES"
echo ""

# 詳細な分析
echo "📋 ブランチ分析"
echo "----------------------------------------------"
echo "auto-fixブランチ: $(git branch | grep -c "auto-fix" || echo "0")"
echo "featureブランチ: $(git branch | grep -c "feature" || echo "0")"
echo "その他: $(git branch | grep -v "auto-fix" | grep -v "feature" | grep -v "main" | wc -l)"
echo ""

# auto-fixブランチの詳細確認
echo "🤖 auto-fixブランチの状態確認"
echo "----------------------------------------------"
for branch in $(git branch | grep "auto-fix" | sed 's/^[ *]*//' | head -10); do
    COMMITS=$(git log main..$branch --oneline 2>/dev/null | wc -l)
    LAST_COMMIT=$(git log -1 --format="%cr" $branch)
    echo "  $branch: $COMMITS コミット差分, 最終更新: $LAST_COMMIT"
done
echo ""

# 削除候補のブランチをリストアップ
echo "🗑️  削除候補ブランチ"
echo "----------------------------------------------"

# 1週間以上前のauto-fixブランチ
echo "■ 1週間以上前のauto-fixブランチ:"
OLD_AUTO_FIX=$(git for-each-ref --format='%(refname:short) %(committerdate:relative)' refs/heads/ | grep "auto-fix" | grep -E "(week|weeks|month|months|year|years) ago" | cut -d' ' -f1)
if [ -n "$OLD_AUTO_FIX" ]; then
    echo "$OLD_AUTO_FIX" | nl -s ". "
else
    echo "  なし"
fi
echo ""

# マージ済みだが削除されていないブランチ
echo "■ マージ済みブランチ:"
MERGED=$(git branch --merged main | grep -v "^\*" | grep -v "main")
if [ -n "$MERGED" ]; then
    echo "$MERGED" | nl -s ". "
else
    echo "  なし"
fi
echo ""

# インタラクティブモード
if [ "${1:-}" != "--force" ]; then
    echo "⚠️  削除を実行しますか？"
    echo "  1) 1週間以上前のauto-fixブランチを削除"
    echo "  2) マージ済みブランチを削除"
    echo "  3) 両方削除"
    echo "  4) キャンセル"
    read -p "選択 (1-4): " choice
else
    choice="3"
fi

case $choice in
    1)
        if [ -n "$OLD_AUTO_FIX" ]; then
            echo "$OLD_AUTO_FIX" | xargs git branch -D
            echo "✅ 古いauto-fixブランチを削除しました"
        fi
        ;;
    2)
        if [ -n "$MERGED" ]; then
            echo "$MERGED" | xargs git branch -d
            echo "✅ マージ済みブランチを削除しました"
        fi
        ;;
    3)
        if [ -n "$OLD_AUTO_FIX" ]; then
            echo "$OLD_AUTO_FIX" | xargs git branch -D
            echo "✅ 古いauto-fixブランチを削除しました"
        fi
        if [ -n "$MERGED" ]; then
            echo "$MERGED" | xargs git branch -d 2>/dev/null || true
            echo "✅ マージ済みブランチを削除しました"
        fi
        ;;
    *)
        echo "❌ キャンセルしました"
        exit 0
        ;;
esac

# リモートも同期
echo ""
echo "🔄 リモート参照を同期中..."
git remote prune origin
echo "✅ リモート参照を同期しました"

# 最終統計
echo ""
echo "📊 最終統計"
echo "----------------------------------------------"
NEW_LOCAL=$(git branch | wc -l)
NEW_REMOTE=$(git branch -r | wc -l)
echo "削除されたローカルブランチ: $((LOCAL_BRANCHES - NEW_LOCAL))"
echo "現在のブランチ数:"
echo "  - ローカル: $NEW_LOCAL"
echo "  - リモート: $NEW_REMOTE"
echo ""
echo "✅ 積極的クリーンアップ完了！"
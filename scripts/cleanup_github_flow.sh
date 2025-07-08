#!/bin/bash
# GitHub Flow状態のクリーンアップ

set -e

echo "🧹 GitHub Flow状態のクリーンアップ"
echo "================================"

cd /home/aicompany/ai_co

# 古いfeatureブランチをクリーンアップ
echo "📝 古いfeatureブランチのクリーンアップ..."
git branch | grep "feature/" | xargs -r git branch -D

# 統計表示
echo "📊 現在のブランチ状況:"
git branch -a

echo "✅ GitHub Flowクリーンアップ完了"
#!/bin/bash
"""
🔧 PR自動化システム設定
GitHub Actions無効化状態でのPR自動処理設定
"""

echo "🚀 PR自動化システム設定開始"

# 環境確認
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN環境変数が設定されていません"
    echo "💡 設定方法: export GITHUB_TOKEN=your_token_here"
    exit 1
fi

echo "✅ GITHUB_TOKEN確認完了: ${GITHUB_TOKEN:0:10}..."

# スクリプト権限設定
chmod +x /home/aicompany/ai_co/scripts/simple_pr_creator.py
chmod +x /home/aicompany/ai_co/scripts/auto_pr_processor_improved.py
chmod +x /home/aicompany/ai_co/scripts/enhanced_auto_pr_cron.sh

echo "✅ スクリプト実行権限設定完了"

# ログディレクトリ作成
mkdir -p /home/aicompany/ai_co/logs/pr_automation

echo "✅ ログディレクトリ準備完了"

# テスト実行
echo "🔍 GitHub API接続テスト実行中..."
python3 /home/aicompany/ai_co/scripts/simple_pr_creator.py

if [ $? -eq 0 ]; then
    echo "✅ GitHub API接続テスト成功"
else
    echo "❌ GitHub API接続テスト失敗"
    exit 1
fi

# Cron設定案表示
echo ""
echo "📋 推奨Cron設定:"
echo "# PR自動処理 (毎日9:00)"
echo "0 9 * * * /home/aicompany/ai_co/scripts/enhanced_auto_pr_cron.sh"
echo ""
echo "# 設定方法:"
echo "crontab -e"
echo ""

echo "🎉 PR自動化システム設定完了!"
echo "💡 GitHub Actions無効化状態でもPR自動作成可能"

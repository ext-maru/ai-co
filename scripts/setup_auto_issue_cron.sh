#!/bin/bash
#
# Auto Issue Processor Cron Setup Script
# Auto Issue Processorの定期実行を設定する
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🤖 Auto Issue Processor Cron設定開始"

# 環境変数ファイルの作成
ENV_FILE="/home/aicompany/.auto_issue_env"
echo "📝 環境変数ファイルを作成: $ENV_FILE"

# 現在の環境変数をファイルに保存
cat > "$ENV_FILE" << EOF
# Auto Issue Processor環境変数
export GITHUB_TOKEN="${GITHUB_TOKEN}"
export GITHUB_REPO_OWNER="ext-maru"
export GITHUB_REPO_NAME="ai-co"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
EOF

# ファイル権限を設定（読み取り専用）
chmod 600 "$ENV_FILE"
echo "✅ 環境変数ファイル作成完了"

# Cronジョブの設定
echo "📅 Cronジョブを設定中..."

# 既存のcrontabを取得（エラーを無視）
crontab -l 2>/dev/null > /tmp/current_cron || true

# Auto Issue Processor関連のエントリを削除
grep -v "auto_issue_processor" /tmp/current_cron > /tmp/new_cron || true

# 新しいcronジョブを追加
# 毎時0分と30分に実行（1日48回）
cat >> /tmp/new_cron << EOF

# Auto Issue Processor - 30分ごとに実行
*/30 * * * * source $ENV_FILE && cd $PROJECT_ROOT && bash scripts/auto_issue_processor_cron.sh >> logs/cron_auto_issue.log 2>&1
EOF

# 新しいcrontabを設定
crontab /tmp/new_cron
rm -f /tmp/current_cron /tmp/new_cron

echo "✅ Cronジョブ設定完了"

# 設定の確認
echo ""
echo "📋 現在のCron設定:"
crontab -l | grep -A 1 -B 1 "auto_issue" || echo "（設定なし）"

echo ""
echo "🎯 設定完了！"
echo "   - 実行間隔: 30分ごと"
echo "   - ログファイル: $PROJECT_ROOT/logs/cron_auto_issue.log"
echo "   - 環境変数ファイル: $ENV_FILE"
echo ""
echo "💡 手動でテストする場合:"
echo "   source $ENV_FILE && cd $PROJECT_ROOT && bash scripts/auto_issue_processor_cron.sh"
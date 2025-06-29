#!/bin/bash
# Slack通知機能セットアップ

echo "📱 Slack通知機能セットアップ"
echo "================================"

# 1. 必要パッケージインストール
cd /root/ai_co && source venv/bin/activate
pip install requests

# 2. Slack設定ファイル作成
cat > /root/ai_co/config/slack.conf << 'SLACK_EOF'
# Slack通知設定
SLACK_WEBHOOK_URL=""
SLACK_CHANNEL="#ai-company"
SLACK_USERNAME="AI-Company-Bot"
SLACK_ICON=":robot_face:"
ENABLE_SLACK=false
SLACK_EOF

echo "✅ Slack設定ファイル作成: /root/ai_co/config/slack.conf"
echo ""
echo "📋 次のステップ:"
echo "1. SlackでWebhook URLを取得"
echo "2. /root/ai_co/config/slack.conf にWebhook URLを設定"
echo "3. ENABLE_SLACK=true に変更"
echo ""
echo "Webhook URL取得方法:"
echo "  1. https://api.slack.com/apps でアプリ作成"
echo "  2. Incoming Webhooks を有効化"
echo "  3. Webhook URL をコピー"

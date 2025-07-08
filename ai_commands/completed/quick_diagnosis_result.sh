#!/bin/bash
# 診断結果の即時確認と提案
cd /home/aicompany/ai_co

echo "🔍 Slackメッセージ診断結果"
echo "=========================="

# 最新の診断ログを確認
echo "最新の診断ログ:"
ls -lt ai_commands/logs/*find_user*.log 2>/dev/null | head -3
ls -lt ai_commands/logs/*check_channel*.log 2>/dev/null | head -3

echo ""
echo "ログ内容確認中..."

# ユーザーメッセージログから重要な情報を抽出
if [ -f ai_commands/logs/find_user_messages_*.log ]; then
    echo ""
    echo "📨 ユーザーメッセージ情報:"
    grep -E "(メッセージ取得|PM-AIへのメンション:|User:)" ai_commands/logs/find_user_messages_*.log | tail -10
fi

# チャンネル情報から重要な情報を抽出
if [ -f ai_commands/logs/check_channel_bot_*.log ]; then
    echo ""
    echo "📡 チャンネル・Bot情報:"
    grep -E "(Bot ID:|チャンネル名:|Botはチャンネルメンバー)" ai_commands/logs/check_channel_bot_*.log | tail -10
fi

echo ""
echo "詳細は15秒後に表示される診断レポートを確認してください"

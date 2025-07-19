#!/usr/bin/env python3
"""
Slack Bot をチャンネルに招待する手順
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Bot招待コマンド
invite_command = """#!/bin/bash
cd /home/aicompany/ai_co

echo "🤖 Slack Bot をチャンネルに招待する方法"
echo "======================================="
echo ""
echo "📋 方法1: Slackアプリから直接招待（推奨）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Slackで #ai-company-scaling チャンネルを開く"
echo ""
echo "2. チャンネル名をクリック → 'インテグレーション' タブ"
echo ""
echo "3. 'アプリを追加' をクリック"
echo ""
echo "4. あなたのBotアプリを選択して追加"
echo ""
echo "5. 同様に #ai-company-health チャンネルにも追加"
echo ""
echo ""
echo "📋 方法2: メンションで招待"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 各チャンネルで以下を入力:"
echo "   @your-bot-name"
echo ""
echo "2. 'このチャンネルに追加' をクリック"
echo ""
echo ""
echo "📋 方法3: スラッシュコマンドで招待"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. チャンネルで以下を入力:"
echo "   /invite @your-bot-name"
echo ""
echo ""
echo "🔍 現在の設定状況:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Bot情報を表示
python3 -c "
import requests

# トークン読み込み
token = None
with open('/home/aicompany/ai_co/config/slack.conf', 'r') as f:
    for line in f:
        if 'SLACK_BOT_TOKEN=' in line:
            token = line.split('=', 1)[1].strip().strip('\"')
            break

if token and token.startswith('xoxb-'):
    headers = {'Authorization': f'Bearer {token}'}

    # Bot情報取得
    response = requests.get(
        'https://slack.com/api/auth.test',
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            print(f'Bot名: @{data.get(\"user\", \"unknown\")}')
            print(f'Bot ID: {data.get(\"user_id\", \"unknown\")}')
            print('')
            print('👆 このBot名を使って招待してください')
else:
    print('Bot Token未設定')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Botをチャンネルに追加したら、再度テストを実行:"
echo "   python3 ai_commands/pending/test_slack_channels.py"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=invite_command, command_id="slack_bot_invite_guide"
)

print("✅ Slack Bot招待ガイドを作成しました")
print("6秒後に自動実行されます...")

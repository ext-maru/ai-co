#!/usr/bin/env python3
"""
Slack Bot Token更新スクリプト
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Token更新コマンド
update_command = """#!/bin/bash
cd /home/aicompany/ai_co

echo "🔑 Slack Bot Token 更新手順"
echo "==========================="
echo ""
echo "1. 以下のURLにアクセス:"
echo "   https://api.slack.com/apps"
echo ""
echo "2. OAuth & Permissions → Bot Token Scopes で以下を追加:"
echo "   ✅ chat:write"
echo "   ✅ chat:write.public"
echo "   ✅ channels:read (推奨)"
echo "   ✅ channels:join (推奨)"
echo ""
echo "3. 'Reinstall to Workspace' をクリック"
echo ""
echo "4. 新しいBot User OAuth Token (xoxb-...) をコピー"
echo ""
echo "5. 以下のファイルを編集:"
echo "   vi /home/aicompany/ai_co/config/slack.conf"
echo ""
echo "   SLACK_BOT_TOKEN=\"xoxb-新しいトークン\""
echo ""
echo "6. PMWorkerを再起動:"
echo "   ai-restart"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 現在の設定:"
grep "SLACK_BOT_TOKEN" /home/aicompany/ai_co/config/slack.conf || echo "Bot Token未設定"
echo ""

# 簡易的な権限チェック
echo "🔍 Bot Token権限チェック:"
python3 -c "
import requests
import os

# 設定ファイルからトークンを読み込む
token = None
config_file = '/home/aicompany/ai_co/config/slack.conf'
with open(config_file, 'r') as f:
    for line in f:
        if 'SLACK_BOT_TOKEN=' in line:
            token = line.split('=', 1)[1].strip().strip('\"')
            break

if token and token.startswith('xoxb-'):
    headers = {'Authorization': f'Bearer {token}'}

    # auth.test で基本情報を確認
    response = requests.post(
        'https://slack.com/api/auth.test',
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            print(f'✅ Bot接続成功: {data.get(\"bot_id\")}')
            print(f'   チーム: {data.get(\"team\")}')
            print(f'   ユーザー: {data.get(\"user\")}')

            # 権限チェック
            print('')
            print('📋 権限チェック中...')

            # テストメッセージ送信を試みる
            test_response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers=headers,
                json={
                    'channel': '#ai-company-scaling',
                    'text': '🔑 権限テスト: このメッセージが表示されれば権限は正常です'
                }
            )

            test_data = test_response.json()
            if test_data.get('ok'):
                print('✅ chat:write 権限: OK')
                print('✅ メッセージ送信テスト成功')
            else:
                print(f'❌ メッセージ送信失敗: {test_data.get(\"error\")}')
                if test_data.get('error') == 'missing_scope':
                    print('   → 必要な権限が不足しています')
                elif test_data.get('error') == 'channel_not_found':
                    print('   → チャンネルが見つかりません')
                elif test_data.get('error') == 'not_in_channel':
                    print('   → Botがチャンネルに参加していません')
        else:
            print(f'❌ Bot認証失敗: {data.get(\"error\")}')
    else:
        print('❌ Slack API接続エラー')
else:
    print('⚠️ Bot Tokenが設定されていません')
    print('上記の手順に従ってTokenを設定してください')
"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=update_command, command_id="update_slack_bot_token"
)

print("✅ Slack Bot Token更新ガイドを作成しました")
print("6秒後に自動実行されます...")

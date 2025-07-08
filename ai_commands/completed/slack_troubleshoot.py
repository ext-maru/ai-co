#!/usr/bin/env python3
"""
Slack設定トラブルシューティング
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# トラブルシューティングコマンド
troubleshoot_command = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔧 Slack設定トラブルシューティング"
echo "==================================="
echo ""

# 診断スクリプト
python3 -c "
import requests
import json

print('📋 ステップ1: Bot Token確認')
print('-' * 40)

# トークン読み込み
bot_token = None
webhook_url = None

with open('/home/aicompany/ai_co/config/slack.conf', 'r') as f:
    for line in f:
        if 'SLACK_BOT_TOKEN=' in line:
            bot_token = line.split('=', 1)[1].strip().strip('\"')
        elif 'SLACK_WEBHOOK_URL=' in line:
            webhook_url = line.split('=', 1)[1].strip().strip('\"')

print(f'Bot Token: {'設定済み' if bot_token and bot_token.startswith('xoxb-') else '❌ 未設定'}')
print(f'Webhook URL: {'設定済み' if webhook_url else '❌ 未設定'}')

if not bot_token or not bot_token.startswith('xoxb-'):
    print('')
    print('❌ Bot Tokenが正しく設定されていません')
    print('')
    print('解決方法:')
    print('1. https://api.slack.com/apps にアクセス')
    print('2. OAuth & Permissions → Bot User OAuth Token をコピー')
    print('3. /home/aicompany/ai_co/config/slack.conf を編集')
    print('   SLACK_BOT_TOKEN=\"xoxb-...\"')
else:
    print('')
    print('📋 ステップ2: Bot接続テスト')
    print('-' * 40)
    
    headers = {'Authorization': f'Bearer {bot_token}'}
    
    # 認証テスト
    auth_response = requests.post(
        'https://slack.com/api/auth.test',
        headers=headers
    )
    
    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        if auth_data.get('ok'):
            print(f'✅ Bot認証成功')
            print(f'   Bot名: @{auth_data.get('user')}')
            print(f'   Team: {auth_data.get('team')}')
            
            # チャンネル一覧取得
            print('')
            print('📋 ステップ3: チャンネル参加状況確認')
            print('-' * 40)
            
            channels_response = requests.post(
                'https://slack.com/api/conversations.list',
                headers=headers,
                data={'types': 'public_channel,private_channel'}
            )
            
            if channels_response.status_code == 200:
                channels_data = channels_response.json()
                if channels_data.get('ok'):
                    bot_user_id = auth_data.get('user_id')
                    channels = channels_data.get('channels', [])
                    
                    scaling_channel = None
                    health_channel = None
                    
                    for channel in channels:
                        if channel.get('name') == 'ai-company-scaling':
                            scaling_channel = channel
                        elif channel.get('name') == 'ai-company-health':
                            health_channel = channel
                    
                    # 各チャンネルの状況確認
                    for ch_name, ch_data in [('ai-company-scaling', scaling_channel), 
                                              ('ai-company-health', health_channel)]:
                        if ch_data:
                            if ch_data.get('is_member'):
                                print(f'✅ #{ch_name}: 参加済み')
                            else:
                                print(f'❌ #{ch_name}: 未参加')
                                print(f'   → Slackで @{auth_data.get('user')} をチャンネルに招待してください')
                        else:
                            print(f'❌ #{ch_name}: チャンネルが見つかりません')
                            print(f'   → Slackでチャンネルを作成してください')
                    
                    # テストメッセージ送信
                    print('')
                    print('📋 ステップ4: メッセージ送信テスト')
                    print('-' * 40)
                    
                    if scaling_channel and scaling_channel.get('is_member'):
                        test_msg = {
                            'channel': scaling_channel['id'],
                            'text': '🧪 テストメッセージ: Bot権限とチャンネル参加OK'
                        }
                        
                        test_response = requests.post(
                            'https://slack.com/api/chat.postMessage',
                            headers=headers,
                            json=test_msg
                        )
                        
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            if test_data.get('ok'):
                                print('✅ メッセージ送信成功！')
                                print('   #ai-company-scaling を確認してください')
                            else:
                                print(f'❌ 送信失敗: {test_data.get('error')}')
                                if test_data.get('error') == 'missing_scope':
                                    print('   → chat:write 権限を追加してください')
                    else:
                        print('⚠️ テスト送信スキップ（チャンネル未参加）')
                        
                else:
                    print('❌ チャンネル一覧取得失敗')
                    print('   → channels:read 権限を追加してください')
        else:
            print(f'❌ Bot認証失敗: {auth_data.get('error')}')
            print('   → Bot Tokenが無効です。新しいTokenを取得してください')
    else:
        print('❌ Slack API接続エラー')

print('')
print('=' * 50)
print('')
print('📋 まとめ:')
print('')
print('1. Bot Tokenが設定されていることを確認')
print('2. 必要な権限を追加:')
print('   - chat:write')
print('   - chat:write.public')
print('   - channels:read')
print('3. Botを各チャンネルに招待')
print('4. PMWorkerを再起動: ai-restart')
"
"""

# コマンドを作成
result = helper.create_bash_command(
    content=troubleshoot_command,
    command_id="slack_troubleshoot"
)

print("✅ Slackトラブルシューティングを作成しました")
print("6秒後に自動実行されます...")
print("\n実行結果を確認して、表示される手順に従ってください")

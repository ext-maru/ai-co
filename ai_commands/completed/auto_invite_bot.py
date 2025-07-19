#!/usr/bin/env python3
"""
Botをチャンネルに招待する自動スクリプト
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# Bot招待自動化コマンド
auto_invite = """#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🤖 Slack Bot 自動招待スクリプト"
echo "==============================="
echo ""

python3 -c "
import requests
import time

token = 'xoxb-9133957021265-9120858383298-GzfwMNHREdN7oU4Amd6rVGHv'
headers = {'Authorization': f'Bearer {token}'}

# Bot情報取得
auth_resp = requests.post('https://slack.com/api/auth.test', headers=headers)
auth_data = auth_resp.json()

if auth_data.get('ok'):
    bot_user_id = auth_data.get('user_id')
    bot_name = auth_data.get('user')
    print(f'Bot情報: @{bot_name} ({bot_user_id})')
    print('')

    # チャンネル一覧取得
    channels_resp = requests.get(
        'https://slack.com/api/conversations.list',
        headers=headers,
        params={'types': 'public_channel', 'limit': 1000}
    )

    if channels_resp.status_code == 200:
        channels_data = channels_resp.json()

        if channels_data.get('ok'):
            channels = channels_data.get('channels', [])

            # 対象チャンネルを探す
            target_channels = {
                'ai-company-scaling': None,
                'ai-company-health': None
            }

            for channel in channels:
                name = channel.get('name')
                if name in target_channels:
                    target_channels[name] = channel

            # 各チャンネルの状況確認と参加試行
            for ch_name, ch_data in target_channels.items():
                if ch_data:
                    ch_id = ch_data['id']
                    is_member = ch_data.get('is_member', False)

                    print(f'#{ch_name}:')

                    if is_member:
                        print(f'  ✅ 既に参加済み')
                    else:
                        print(f'  ⚠️ 未参加 - 参加を試みます...')

                        # チャンネルに参加
                        join_resp = requests.post(
                            'https://slack.com/api/conversations.join',
                            headers=headers,
                            json={'channel': ch_id}
                        )

                        join_data = join_resp.json()
                        if join_data.get('ok'):
                            print(f'  ✅ 参加成功！')
                        else:
                            error = join_data.get('error')
                            print(f'  ❌ 参加失敗: {error}')

                            if error == 'missing_scope':
                                print('     → channels:join 権限が必要です')
                            elif error == 'is_archived':
                                print('     → チャンネルがアーカイブされています')
                else:
                    print(f'#{ch_name}: ❌ チャンネルが見つかりません')
                    print('  → Slackでチャンネルを作成してください')

                print('')

            # 最終テスト
            print('📨 最終動作確認...')
            time.sleep(1)

            from libs.slack_channel_notifier import SlackChannelNotifier
            notifier = SlackChannelNotifier()

            # 各チャンネルにテスト送信
            success_count = 0

            if target_channels.get('ai-company-scaling'):
                if notifier.send_scaling_notification(
                    action='up',
                    current_workers=1,
                    target_workers=2,
                    queue_length=5,
                    task_id='setup_complete'
                ):
                    success_count += 1
                    print('✅ スケーリング通知: 成功')
                else:
                    print('❌ スケーリング通知: 失敗')

            if target_channels.get('ai-company-health'):
                if notifier.send_health_notification(
                    worker_id='setup_test',
                    action='セットアップ完了',
                    issues=[],
                    success=True
                ):
                    success_count += 1
                    print('✅ ヘルスチェック通知: 成功')
                else:
                    print('❌ ヘルスチェック通知: 失敗')

            print('')
            print('=' * 50)
            if success_count == 2:
                print('🎉 セットアップ完了！')
                print('')
                print('次のステップ:')
                print('1. PMWorkerを再起動: ai-restart')
                print('2. 各チャンネルで通知を確認')
                print('')
                print('⚠️ セキュリティ重要:')
                print('Bot Tokenが露出したため、後で必ず再生成してください')
            else:
                print('⚠️ 一部の設定が未完了です')
                print('手動でBotを各チャンネルに招待してください')
        else:
            print(f'❌ チャンネル一覧取得失敗: {channels_data.get(\"error\")}')
else:
    print(f'❌ Bot認証失敗: {auth_data.get(\"error\")}')
"
"""

# コマンドを作成
result = helper.create_bash_command(content=auto_invite, command_id="auto_invite_bot")

print("✅ Bot自動招待スクリプトを作成しました")
print("6秒後に自動実行されます...")

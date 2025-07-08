#!/usr/bin/env python3
"""
Slack設定を環境変数から更新
"""
import json
import os
from pathlib import Path

# 環境変数から値を取得
bot_token = os.environ.get('SLACK_BOT_TOKEN', '')
channel_id = os.environ.get('SLACK_CHANNEL_IDS', os.environ.get('SLACK_POLLING_CHANNEL_ID', ''))
webhook_url = os.environ.get('SLACK_WEBHOOK_URL', '')

# 設定ファイルを読み込み
config_path = Path('config/slack_config.json')
with open(config_path) as f:
    config = json.load(f)

# 実際の値で更新
if bot_token:
    config['bot_token'] = bot_token
    print(f"✅ Bot Token更新: {bot_token[:20]}...")

if channel_id:
    config['polling_channel_id'] = channel_id
    print(f"✅ Channel ID更新: {channel_id}")

if webhook_url:
    config['webhook_url'] = webhook_url
    print(f"✅ Webhook URL更新: {webhook_url[:40]}...")

# 設定を保存
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ Slack設定が正常に更新されました！")
#!/usr/bin/env python3
"""
AI-PM用のSlack設定ガイドとチェックツール
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.env_config import get_config


def print_setup_guide():
    """Slack App設定ガイドを表示"""
    print("🤖 AI-PM Slack App セットアップガイド")
    print("=" * 60)
    print("\n1. Slack Appの作成:")
    print("   - https://api.slack.com/apps にアクセス")
    print("   - 'Create New App' → 'From scratch'")
    print("   - App名: AI-PM")
    print("   - ワークスペースを選択")

    print("\n2. Bot Token Scopesの設定:")
    print("   OAuth & Permissions → Scopes → Bot Token Scopes")
    print("   必須スコープ:")
    print("   - channels:history")
    print("   - channels:read")
    print("   - chat:write")
    print("   - chat:write.public")
    print("   - groups:history")
    print("   - groups:read")
    print("   - im:history")
    print("   - im:read")
    print("   - im:write")
    print("   - app_mentions:read")
    print("   - users:read")

    print("\n3. Event Subscriptionsの設定:")
    print("   Event Subscriptions → Enable Events")
    print("   Subscribe to bot events:")
    print("   - app_mention")
    print("   - message.channels")
    print("   - message.groups")
    print("   - message.im")

    print("\n4. Socket Modeの設定（推奨）:")
    print("   Socket Mode → Enable Socket Mode")
    print("   Generate App-Level Token:")
    print("   - Token Name: socket-mode-token")
    print("   - Scope: connections:write")

    print("\n5. トークンの取得:")
    print("   - Bot User OAuth Token (xoxb-...)")
    print("   - App-Level Token (xapp-...)")

    print("\n6. インストール:")
    print("   OAuth & Permissions → Install to Workspace")

    print("\n7. チャンネルに招待:")
    print("   Slackで: /invite @AI-PM")


def check_current_config():
    """現在の設定をチェック"""
    print("\n\n📋 現在の設定状態:")
    print("=" * 60)

    config = get_config()
    slack_config = config.get_slack_config()

    # Bot Token
    bot_token = slack_config.get("bot_token")
    if bot_token and bot_token.startswith("xoxb-"):
        print(f"✅ Bot Token: 設定済み ({bot_token[:12]}...)")
    else:
        print("❌ Bot Token: 未設定または無効")

    # App Token
    app_token = slack_config.get("app_token")
    if app_token and app_token.startswith("xapp-"):
        print(f"✅ App Token: 設定済み ({app_token[:12]}...)")
    else:
        print("⚠️  App Token: 未設定（Socket Mode使用時は必須）")

    # Team ID
    team_id = slack_config.get("team_id")
    if team_id:
        print(f"✅ Team ID: {team_id}")
    else:
        print("❌ Team ID: 未設定")

    # Channel IDs
    channel_ids = slack_config.get("channel_ids")
    if channel_ids:
        print(f"✅ Channel IDs: {channel_ids}")
    else:
        print("❌ Channel IDs: 未設定")


def generate_env_template():
    """環境変数テンプレートを生成"""
    print("\n\n📝 .envファイルに追加する内容:")
    print("=" * 60)
    print(
        """
# AI-PM Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_TEAM_ID=T093XU50M7T
SLACK_CHANNEL_IDS=C0946R76UU8

# Socket Mode設定
SLACK_SOCKET_MODE_ENABLED=true

# メンション必須設定
SLACK_REQUIRE_MENTION=true
"""
    )


def test_slack_connection():
    """Slack接続テスト"""
    print("\n\n🧪 接続テスト:")
    print("=" * 60)

    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        config = get_config()
        bot_token = config.SLACK_BOT_TOKEN

        if not bot_token or not bot_token.startswith("xoxb-"):
            print("❌ Bot Tokenが設定されていません")
            return

        client = WebClient(token=bot_token)

        # 認証テスト
        try:
            response = client.auth_test()
            print(f"✅ 認証成功: {response['user']} (@{response['user_id']})")
            print(f"   Team: {response['team']} ({response['team_id']})")
        except SlackApiError as e:
            print(f"❌ 認証失敗: {e.response['error']}")
            return

        # チャンネル情報取得テスト
        channel_id = config.SLACK_CHANNEL_IDS
        if channel_id:
            try:
                response = client.conversations_info(channel=channel_id)
                channel = response["channel"]
                print(f"✅ チャンネル情報取得成功: #{channel['name']}")

                # Bot参加状態チェック
                if channel.get("is_member"):
                    print("   ✅ Botはチャンネルに参加済み")
                else:
                    print("   ⚠️  Botはチャンネルに未参加 → /invite @AI-PM")

            except SlackApiError as e:
                print(f"❌ チャンネル情報取得失敗: {e.response['error']}")

    except ImportError:
        print("⚠️  slack_sdk がインストールされていません")
        print("   pip install slack-sdk")


if __name__ == "__main__":
    print_setup_guide()
    check_current_config()
    generate_env_template()
    test_slack_connection()

    print("\n\n💡 ヒント:")
    print("- Socket Modeを使用すると、Webhookエンドポイントの設定が不要")
    print("- リアルタイムイベント処理にはSocket Modeが推奨")
    print("- プライベートチャンネルを使う場合は、groups:* スコープも必要")

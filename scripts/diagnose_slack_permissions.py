#!/usr/bin/env python3
"""
Slack権限診断ツール
現在のBot Tokenで利用可能な権限を確認
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.env_config import get_config

def diagnose_permissions():
    """Slack権限を診断"""
    print("🔍 Slack権限診断")
    print("=" * 60)
    
    config = get_config()
    bot_token = config.SLACK_BOT_TOKEN
    
    if not bot_token:
        print("❌ Bot Tokenが設定されていません")
        return
    
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    except ImportError:
        print("❌ slack_sdk がインストールされていません")
        print("   実行: pip3 install slack-sdk")
        return
    
    client = WebClient(token=bot_token)
    
    # 認証テスト
    print("\n📋 認証情報:")
    try:
        auth_info = client.auth_test()
        print(f"✅ Bot名: {auth_info['user']} (@{auth_info['user_id']})")
        print(f"✅ Team: {auth_info['team']} ({auth_info['team_id']})")
    except SlackApiError as e:
        print(f"❌ 認証失敗: {e.response['error']}")
        return
    
    # 権限テスト
    print("\n📋 権限テスト:")
    
    # チャンネル履歴読み取り
    channel_id = config.SLACK_CHANNEL_IDS or config.SLACK_POLLING_CHANNEL_ID
    
    tests = [
        {
            "name": "チャンネル履歴読み取り",
            "method": lambda: client.conversations_history(channel=channel_id, limit=1),
            "scope": "channels:history"
        },
        {
            "name": "チャンネル情報取得",
            "method": lambda: client.conversations_info(channel=channel_id),
            "scope": "channels:read"
        },
        {
            "name": "メッセージ送信",
            "method": lambda: client.chat_postMessage(channel=channel_id, text="権限テスト", dry_run=True),
            "scope": "chat:write"
        },
        {
            "name": "ユーザー情報取得",
            "method": lambda: client.users_info(user=auth_info['user_id']),
            "scope": "users:read"
        }
    ]
    
    missing_scopes = []
    
    for test in tests:
        try:
            test["method"]()
            print(f"✅ {test['name']}: OK")
        except SlackApiError as e:
            error = e.response['error']
            if error == 'missing_scope':
                print(f"❌ {test['name']}: 権限不足 ({test['scope']})")
                missing_scopes.append(test['scope'])
            else:
                print(f"❌ {test['name']}: {error}")
    
    # Socket Mode確認
    print("\n📋 Socket Mode設定:")
    app_token = config.SLACK_APP_TOKEN
    if app_token and app_token.startswith('xapp-'):
        print(f"✅ App Token: 設定済み")
        print(f"✅ Socket Mode: {'有効' if config.get_bool_env('SLACK_SOCKET_MODE_ENABLED') else '無効'}")
    else:
        print("❌ App Token: 未設定")
    
    # 推奨事項
    if missing_scopes:
        print(f"\n⚠️  不足している権限:")
        print("1. https://api.slack.com/apps → あなたのアプリ")
        print("2. OAuth & Permissions → Bot Token Scopes")
        print("3. 以下の権限を追加:")
        for scope in missing_scopes:
            print(f"   - {scope}")
        print("4. 'Install to Workspace' で再インストール")
        print("5. 新しいBot Tokenを.envファイルに更新")
    
    # 現在のトークンタイプを判定
    print(f"\n📋 トークン診断:")
    print(f"Bot Token形式: {'✅ 正しい' if bot_token.startswith('xoxb-') else '❌ 不正'}")
    
    # 古いトークンの可能性をチェック
    if 'xoxb-9133957021265-9120858383298' in bot_token:
        print("⚠️  古いBot Tokenを使用している可能性があります")
        print("   最新のBot Tokenに更新してください")

if __name__ == "__main__":
    diagnose_permissions()
    
    print("\n\n💡 Bot Token更新手順:")
    print("1. https://api.slack.com/apps")
    print("2. OAuth & Permissions → Install to Workspace")
    print("3. 新しいBot Token (xoxb-...) をコピー")
    print("4. .envファイルのSLACK_BOT_TOKENを更新")
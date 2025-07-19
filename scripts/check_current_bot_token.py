#!/usr/bin/env python3
"""
現在のBot Tokenの状態確認
権限追加後の新しいトークンが必要かチェック
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.env_config import get_config


def check_bot_token():
    """Bot Tokenの状態確認"""
    print("🔍 現在のBot Token状態確認")
    print("=" * 60)

    config = get_config()
    current_token = config.SLACK_BOT_TOKEN

    print(f"📋 現在のBot Token: {current_token[:20]}...")
    print(f"📋 App Token: {'設定済み' if config.SLACK_APP_TOKEN else '未設定'}")

    # トークンの形式確認
    if current_token and current_token.startswith("xoxb-"):
        print("✅ Bot Token形式: 正しい")

        # トークンの日付部分を解析
        parts = current_token.split("-")
        if len(parts) >= 3:
            team_id = parts[1]
            app_id = parts[2]
            print(f"📊 Team ID部分: {team_id}")
            print(f"📊 App ID部分: {app_id}")
    else:
        print("❌ Bot Token形式: 不正")

    print("\n🔄 権限追加後の新しいBot Token取得手順:")
    print("1. https://api.slack.com/apps → PM-AI アプリ")
    print("2. OAuth & Permissions ページ")
    print("3. 「Install to Workspace」をクリック")
    print("4. 権限を再承認")
    print("5. 新しい「Bot User OAuth Token」をコピー")
    print("\n💡 権限追加後は必ず再インストールが必要です")
    print("   再インストールしないと新しい権限が有効になりません")


if __name__ == "__main__":
    check_bot_token()

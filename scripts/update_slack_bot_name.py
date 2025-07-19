#!/usr/bin/env python3
"""
Slack Bot名を更新（AI-PM → PM-AI）
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🤖 Slack Bot名の更新")
print("=" * 60)
print("\n正しいBot名: @PM-AI")
print("\n更新が必要な箇所:")
print("1. Slackアプリ設定:")
print("   - App Home → Display Name: PM-AI")
print("   - App Home → Default Username: pm-ai")
print("\n2. チャンネルへの招待:")
print("   /invite @pm-ai")
print("\n3. メンションテスト:")
print("   @pm-ai こんにちは")

# 設定ファイルのBot名も更新
env_vars = {"SLACK_BOT_NAME": "pm-ai", "SLACK_BOT_DISPLAY_NAME": "PM-AI"}

print("\n📝 環境変数に追加する設定:")
for key, value in env_vars.items():
    print(f"{key}={value}")

print("\n💡 ヒント:")
print("- Slackアプリの設定でBot名を「PM-AI」に変更してください")
print("- チャンネルでは @pm-ai でメンションします")
print("- 既に @AI-PM で招待済みの場合は、自動的に名前が更新されます")

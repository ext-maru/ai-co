#!/usr/bin/env python3
"""
Slackメッセージ履歴を直接確認
ユーザーのメッセージを探す
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import json
from datetime import datetime, timedelta

import requests

from core import get_config


def find_user_messages():
    """ユーザーのメッセージを探す"""
    print("🔍 Slackメッセージ履歴確認")
    print("=" * 60)

    config = get_config()
    bot_token = config.get("slack.bot_token", "")
    channel_id = config.get("slack.polling_channel_id", "")

    if not bot_token or not channel_id:
        print("❌ Slack設定エラー")
        return

    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    # Bot ID取得
    print("1️⃣ Bot情報取得...")
    auth_resp = requests.get("https://slack.com/api/auth.test", headers=headers)

    bot_id = None
    if auth_resp.status_code == 200:
        auth_data = auth_resp.json()
        if auth_data.get("ok"):
            bot_id = auth_data.get("user_id")
            print(f"✅ Bot ID: {bot_id}")
            print(f"✅ Bot名: {auth_data.get('user')}")

    # 過去2時間のメッセージを取得
    print("\n2️⃣ 過去2時間のメッセージ取得...")
    oldest = (datetime.now() - timedelta(hours=2)).timestamp()

    params = {"channel": channel_id, "oldest": str(oldest), "limit": 100}  # 最大100件

    try:
        response = requests.get(
            "https://slack.com/api/conversations.history",
            headers=headers,
            params=params,
        )

        if response.status_code != 200:
            print(f"❌ API接続エラー: {response.status_code}")
            return

        data = response.json()
        if not data.get("ok"):
            print(f"❌ APIエラー: {data.get('error')}")
            return

        messages = data.get("messages", [])
        print(f"✅ {len(messages)}件のメッセージ取得\n")

        # ユーザーメッセージのみ抽出（Bot以外）
        user_messages = []
        mention_messages = []

        for msg in messages:
            # Botメッセージは除外
            if msg.get("bot_id") or msg.get("subtype") == "bot_message":
                continue

            text = msg.get("text", "")
            ts = msg.get("ts", "")
            user = msg.get("user", "unknown")

            # タイムスタンプを日時に変換
            msg_time = datetime.fromtimestamp(float(ts))

            user_msg = {"time": msg_time, "user": user, "text": text, "ts": ts}

            user_messages.append(user_msg)

            # メンション付きメッセージ
            if bot_id and f"<@{bot_id}>" in text:
                mention_messages.append(user_msg)

        # 結果表示
        print("=" * 60)
        print("📨 ユーザーメッセージ一覧（新しい順）:")
        print("=" * 60)

        for i, msg in enumerate(user_messages[:20], 1):  # 最新20件
            print(f"\n{i}. {msg['time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   User: {msg['user']}")
            print(f"   Text: {msg['text'][:200]}")

            # メンション確認
            if bot_id and f"<@{bot_id}>" in msg["text"]:
                print(f"   ✅ PM-AIへのメンション含む")

        # メンション付きメッセージのサマリー
        print("\n\n" + "=" * 60)
        print(f"📌 PM-AIへのメンション: {len(mention_messages)}件")
        print("=" * 60)

        if mention_messages:
            for i, msg in enumerate(mention_messages[:10], 1):
                clean_text = msg["text"].replace(f"<@{bot_id}>", "").strip()
                print(f"\n{i}. {msg['time'].strftime('%H:%M:%S')}")
                print(f"   内容: {clean_text[:100]}")
                print(f"   TS: {msg['ts']}")
        else:
            print("\n⚠️  PM-AIへのメンションが見つかりません")
            print("   Slackで @pm-ai をメンションしてメッセージを送信してください")

        # ユーザー別集計
        print("\n\n" + "=" * 60)
        print("👥 ユーザー別メッセージ数:")
        print("=" * 60)

        user_count = {}
        for msg in user_messages:
            user = msg["user"]
            user_count[user] = user_count.get(user, 0) + 1

        for user, count in sorted(user_count.items(), key=lambda x: x[1], reverse=True):
            print(f"User {user}: {count}件")

        # チャンネル情報も確認
        print("\n\n" + "=" * 60)
        print("📡 チャンネル情報:")
        print("=" * 60)

        ch_resp = requests.get(
            "https://slack.com/api/conversations.info",
            headers=headers,
            params={"channel": channel_id},
        )

        if ch_resp.status_code == 200:
            ch_data = ch_resp.json()
            if ch_data.get("ok"):
                channel = ch_data.get("channel", {})
                print(f"チャンネル名: #{channel.get('name', 'unknown')}")
                print(f"チャンネルID: {channel_id}")
                print(f"メンバー数: {channel.get('num_members', 0)}")

    except Exception as e:
        print(f"\n❌ エラー: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    find_user_messages()

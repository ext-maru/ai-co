#!/usr/bin/env python3
"""
Slackユーザーとメッセージの詳細確認
特定のユーザーを探す
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import json
from datetime import datetime, timedelta

import requests

from core import get_config


def find_specific_user():
    """特定のユーザーとメッセージを探す"""
    print("🔍 Slackユーザーとメッセージ詳細確認")
    print("=" * 80)

    config = get_config()
    bot_token = config.get("slack.bot_token", "")
    channel_id = config.get("slack.polling_channel_id", "")

    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    # 1.0 ユーザーリスト取得
    print("1️⃣ ワークスペースのユーザー一覧取得...")
    users_resp = requests.get(
        "https://slack.com/api/users.list", headers=headers, params={"limit": 100}
    )

    user_map = {}
    if users_resp.status_code == 200:
        users_data = users_resp.json()
        if users_data.get("ok"):
            members = users_data.get("members", [])
            print(f"✅ {len(members)}人のユーザー取得\n")

            print("アクティブユーザー:")
            print("-" * 60)
            for member in members:
                if not member.get("deleted", False) and not member.get("is_bot", False):
                    user_id = member.get("id")
                    name = member.get("name", "unknown")
                    real_name = member.get("real_name", "")

                    user_map[user_id] = {"name": name, "real_name": real_name}

                    print(f"ID: {user_id} | @{name} | {real_name}")

    # 2.0 最近のメッセージを詳細確認
    print("\n\n2️⃣ 最近のメッセージ詳細（過去3時間）...")
    oldest = (datetime.now() - timedelta(hours=3)).timestamp()

    params = {"channel": channel_id, "oldest": str(oldest), "limit": 200}

    msg_resp = requests.get(
        "https://slack.com/api/conversations.history", headers=headers, params=params
    )

    if msg_resp.status_code == 200:
        msg_data = msg_resp.json()
        if msg_data.get("ok"):
            messages = msg_data.get("messages", [])
            print(f"✅ {len(messages)}件のメッセージ取得\n")

            # Bot ID取得
            auth_resp = requests.get("https://slack.com/api/auth.test", headers=headers)
            bot_id = None
            if auth_resp.status_code == 200:
                auth_data = auth_resp.json()
                if auth_data.get("ok"):
                    bot_id = auth_data.get("user_id")

            # ユーザー別にメッセージを整理
            user_messages = {}

            for msg in messages:
                if msg.get("bot_id"):
                    continue

                user_id = msg.get("user", "unknown")
                text = msg.get("text", "")
                ts = msg.get("ts", "")

                if user_id not in user_messages:
                    user_messages[user_id] = []

                user_messages[user_id].append(
                    {
                        "text": text,
                        "ts": ts,
                        "time": datetime.fromtimestamp(float(ts)),
                        "has_mention": bot_id and f"<@{bot_id}>" in text,
                    }
                )

            # ユーザー別に表示
            print("=" * 80)
            print("👤 ユーザー別メッセージ詳細:")
            print("=" * 80)

            for user_id, msgs in user_messages.items():
                user_info = user_map.get(user_id, {"name": "unknown", "real_name": ""})
            # 繰り返し処理

                print(f"\n【{user_info['name']} ({user_info['real_name']})】")
                print(f"User ID: {user_id}")
                print(f"メッセージ数: {len(msgs)}")

                # 最新5件を表示
                for i, msg in enumerate(msgs[:5], 1):
                    print(f"\n  {i}. {msg['time'].strftime('%H:%M:%S')}")
                    print(f"     {msg['text'][:150]}")
                    if not (msg["has_mention"]):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if msg["has_mention"]:
                        print(f"     ✅ PM-AIへのメンション")

                # メンション付きメッセージ
                mention_msgs = [m for m in msgs if m["has_mention"]]
                if mention_msgs:
                    print(f"\n  📌 PM-AIへのメンション: {len(mention_msgs)}件")
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for m in mention_msgs[:3]:
                        clean_text = m["text"].replace(f"<@{bot_id}>", "@pm-ai").strip()
                        print(
                            f"     - {m['time'].strftime('%H:%M')} : {clean_text[:80]}"
                        )

            # 統計
            print("\n\n" + "=" * 80)
            print("📊 統計情報:")
            print("=" * 80)

            total_users = len(user_messages)
            total_messages = sum(len(msgs) for msgs in user_messages.values())
            total_mentions = sum(
                len([m for m in msgs if m["has_mention"]])
                for msgs in user_messages.values()
            )

            print(f"アクティブユーザー数: {total_users}")
            print(f"総メッセージ数: {total_messages}")
            print(f"PM-AIへのメンション数: {total_mentions}")

            # キーワード検索
            print("\n\n" + "=" * 80)
            print("🔍 キーワード検索:")
            print("=" * 80)

            keywords = ["test", "テスト", "pm-ai", "PM-AI", "hello", "こんにちは"]

            for keyword in keywords:
            # 繰り返し処理
                found = []
                # 繰り返し処理
                for user_id, msgs in user_messages.items():
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for msg in msgs:
                        if not (keyword.lower() in msg["text"].lower()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if keyword.lower() in msg["text"].lower():
                            found.append(
                                {
                                    "user": user_map.get(user_id, {"name": user_id})[
                                        "name"
                                    ],
                                    "time": msg["time"],
                                    "text": msg["text"],
                                }
                            )

                if found:
                    print(f"\n'{keyword}' を含むメッセージ: {len(found)}件")
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for f in found[:3]:
                        print(
                            f"  - {f['time'].strftime('%H:%M')} @{f['user']}: {f['text'][:60]}"
                        )


if __name__ == "__main__":
    find_specific_user()

#!/usr/bin/env python3
"""
ユーザーメッセージの詳細確認
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import re

from libs.ai_log_viewer import AILogViewer

def find_actual_messages():
    """実際のユーザーメッセージを探す"""
    print("🔍 ユーザーメッセージ詳細確認")
    print("=" * 80)

    viewer = AILogViewer()

    # find_user_messagesログを探す
    logs = viewer.get_latest_command_logs(30)
    user_msg_logs = [log for log in logs if "find_user_messages" in log["command_id"]]

    if not user_msg_logs:
        print("❌ ユーザーメッセージログが見つかりません")
        return

    # 最新のログを確認
    latest_log = user_msg_logs[0]
    print(f"ログファイル: {latest_log['command_id']}")
    print(f"実行時刻: {latest_log.get('timestamp', 'unknown')}")

    if "path" not in latest_log:
        return

    log_path = Path(latest_log["path"])
    if not log_path.exists():
        return

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("\n📨 検出されたメッセージ:")
    print("-" * 80)

    # メッセージパターンを探す

    pattern1 = re.findall(r"User:\s*([U\w]+)\s*\n\s*Text:\s*([^\n]+)", content)

    if pattern1:
        print(f"\n検出メッセージ数: {len(pattern1)}")
        for i, (user, text) in enumerate(pattern1[:10], 1):
            print(f"\n{i}. User: {user}")
            print(f"   Text: {text}")

    # パターン2: 時刻付きメッセージ
    pattern2 = re.findall(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\n\s*User:\s*([U\w]+)\s*\n\s*Text:\s*([^\n]+)",
        content,
    )

    if pattern2:
        print(f"\n\n時刻付きメッセージ: {len(pattern2)}件")
        for time, user, text in pattern2[-5:]:
            print(f"\n時刻: {time}")
            print(f"User: {user}")
            print(f"Text: {text}")

    # Bot IDとメンション確認
    bot_id_match = re.search(r"Bot ID:\s*([U\w]+)", content)
    if bot_id_match:
        bot_id = bot_id_match.group(1)
        print(f"\n\n🤖 Bot ID: {bot_id}")

        # メンション付きメッセージを探す
        mention_pattern = f"<@{bot_id}>"
        mentions = []

        for user, text in pattern1:
            if mention_pattern in text:
                mentions.append((user, text))

        if mentions:
            print(f"\n📌 Bot（{bot_id}）へのメンション: {len(mentions)}件")
            for user, text in mentions[:5]:
                clean_text = text.replace(mention_pattern, "@pm-ai")
                print(f"\nUser: {user}")
                print(f"Text: {clean_text}")
        else:
            print(f"\n⚠️  Bot ID {bot_id} へのメンションが見つかりません")

    # メンション統計
    mention_count_match = re.search(r"PM-AIへのメンション:\s*(\d+)件", content)
    if mention_count_match:
        count = mention_count_match.group(1)
        print(f"\n\n📊 メンション統計: {count}件")

    # チャンネル情報
    channel_match = re.search(r"チャンネル名:\s*#(\w+)", content)
    if channel_match:
        print(f"\n📡 チャンネル: #{channel_match.group(1)}")

def check_specific_user_messages():
    """特定ユーザーのメッセージを確認"""
    print("\n\n👤 ユーザー別メッセージ確認")
    print("=" * 80)

    viewer = AILogViewer()

    # find_specific_userログを探す
    logs = viewer.get_latest_command_logs(30)
    specific_logs = [log for log in logs if "find_specific_user" in log["command_id"]]

    if not specific_logs:
        print("❌ ユーザー別ログが見つかりません")
        return

    latest_log = specific_logs[0]

    if "path" not in latest_log:
        return

    log_path = Path(latest_log["path"])
    if not log_path.exists():
        return

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # ユーザー情報抽出
    user_pattern = re.findall(
        r"【([^】]+)】\s*\nUser ID:\s*([U\w]+)\s*\nメッセージ数:\s*(\d+)", content
    )

    if user_pattern:
        print("\nアクティブユーザー:")
        for name, user_id, msg_count in user_pattern[:10]:
            print(f"  - {name} ({user_id}): {msg_count}件")

    # 統計情報
    stats_match = re.search(
        r"アクティブユーザー数:\s*(\d+)\s*\n総メッセージ数:\s*(\d+)\s*\nPM-AIへのメンション数:\s*(\d+)", content
    )
    if stats_match:
        active_users, total_msgs, mentions = stats_match.groups()
        print(f"\n📊 統計:")
        print(f"  アクティブユーザー: {active_users}人")
        print(f"  総メッセージ数: {total_msgs}件")
        print(f"  メンション数: {mentions}件")

if __name__ == "__main__":
    # ユーザーメッセージ詳細確認
    find_actual_messages()

    # ユーザー別確認
    check_specific_user_messages()

    print("\n\n💡 確認ポイント:")
    print("1.0 あなたのメッセージが表示されているか")
    print("2.0 Bot IDが正しく検出されているか")
    print("3.0 メンション形式が正しいか（@Bot_ID）")
    print("4.0 チャンネルが正しいか")

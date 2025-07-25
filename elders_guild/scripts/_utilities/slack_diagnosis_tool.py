#!/usr/bin/env python3
"""
Slack PM-AI 診断専用スクリプト
全ての処理をログに出力して、どこで止まっているか特定する
"""

import json
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import get_config

# ログファイル
LOG_FILE = PROJECT_ROOT / "slack_diagnosis.log"


def log(message)timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
"""詳細ログ出力"""
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(LOG_FILE, "a") as f:
        f.write(log_message + "\n")


def diagnose_slack()log("=== Slack PM-AI 診断開始 ===")
"""Slack連携の診断"""

    # 1.0 設定読み込み
    log("1.0 設定読み込み")
    try:
        config = get_config()
        bot_token = config.get("slack.bot_token", "")
        channel_id = config.get("slack.polling_channel_id", "")
        require_mention = config.get("slack.require_mention", True)

        log(f"  Bot Token: {'設定あり' if bot_token else '設定なし'}")
        log(f"  Token先頭: {bot_token[:20]}..." if bot_token else "  Token: なし")
        log(f"  Channel ID: {channel_id}")
        log(f"  メンション必須: {require_mention}")

        if not bot_token:
            log("  ❌ Bot Tokenが設定されていません")
            return
        if not channel_id:
            log("  ❌ Channel IDが設定されていません")
            return

    except Exception as e:
        log(f"  ❌ 設定読み込みエラー: {str(e)}")
        return

    # 2.0 Bot認証テスト
    log("\n2.0 Bot認証テスト")
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }

    try:
        url = "https://slack.com/api/auth.test"
        log(f"  API呼び出し: {url}")

        response = requests.get(url, headers=headers)
        log(f"  HTTP Status: {response.status_code}")
        log(f"  Response Headers: {dict(response.headers)}")

        data = response.json()
        log(f"  Response Body: {json.dumps(data, indent}")

        if data.get("ok"):
            bot_user_id = data.get("user_id")
            log(f"  ✅ Bot認証成功")
            log(f"  Bot User ID: {bot_user_id}")
            log(f"  Bot Name: {data.get('user')}")
            log(f"  Team: {data.get('team')}")
        else:
            log(f"  ❌ Bot認証失敗: {data.get('error')}")
            return

    except Exception as e:
        log(f"  ❌ API呼び出しエラー: {str(e)}")
        return

    # 3.0 チャンネル情報取得
    log("\n3.0 チャンネル情報取得")
    try:
        url = "https://slack.com/api/conversations.info"
        params = {"channel": channel_id}
        log(f"  API呼び出し: {url}")
        log(f"  パラメータ: {params}")

        response = requests.get(url, headers=headers, params=params)
        log(f"  HTTP Status: {response.status_code}")

        data = response.json()
        log(f"  Response: {json.dumps(data, indent}")

        if data.get("ok"):
            channel_info = data.get("channel", {})
            log(f"  ✅ チャンネル情報取得成功")
            log(f"  Channel Name: {channel_info.get('name')}")
            log(f"  Is Member: {channel_info.get('is_member')}")

            if not channel_info.get("is_member"):
                log(f"  ⚠️  Botがチャンネルメンバーではありません")
        else:
            log(f"  ❌ チャンネル情報取得失敗: {data.get('error')}")

    except Exception as e:
        log(f"  ❌ チャンネル情報取得エラー: {str(e)}")

    # 4.0 メッセージ履歴取得
    log("\n4.0 メッセージ履歴取得（過去5分）")
    try:
        oldest_timestamp = (datetime.now() - timedelta(minutes=5)).timestamp()

        url = "https://slack.com/api/conversations.history"
        params = {
            "channel": channel_id,
            "oldest": str(oldest_timestamp),
            "inclusive": False,
            "limit": 100,
        }
        log(f"  API呼び出し: {url}")
        log(f"  パラメータ: {json.dumps(params, indent}")

        response = requests.get(url, headers=headers, params=params)
        log(f"  HTTP Status: {response.status_code}")

        data = response.json()

        if data.get("ok"):
            messages = data.get("messages", [])
            log(f"  ✅ メッセージ取得成功: {len(messages)}件")

            # 各メッセージの詳細
            for i, msg in enumerate(messages):
                log(f"\n  メッセージ {i+1}:")
                log(f"    Timestamp: {msg.get('ts')}")
                log(f"    User: {msg.get('user', 'N/A')}")
                log(f"    Text: {msg.get('text', '')[:100]}...")
                log(f"    Bot ID: {msg.get('bot_id', 'なし')}")
                log(f"    Subtype: {msg.get('subtype', 'なし')}")

                # メンションチェック
                text = msg.get("text", "")
                has_bot_mention = f"<@{bot_user_id}>" in text if bot_user_id else False
                has_pmai_mention = "@pm-ai" in text.lower()

                log(f"    Bot IDメンション: {has_bot_mention}")
                log(f"    @pm-aiメンション: {has_pmai_mention}")

                if has_bot_mention or has_pmai_mention:
                    log(f"    ✅ メンション検出！")

        else:
            log(f"  ❌ メッセージ取得失敗: {data.get('error')}")

    except Exception as e:
        log(f"  ❌ メッセージ取得エラー: {str(e)}")

    # 5.0 データベース確認
    log("\n5.0 データベース確認")
    db_path = PROJECT_ROOT / "db" / "slack_messages.db"

    if db_path.exists():
        log(f"  ✅ DBファイル存在: {db_path}")
        try:
            with sqlite3connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM processed_messages")
                count = cursor.fetchone()[0]
                log(f"  処理済みメッセージ数: {count}")

                # 最新の処理済みメッセージ
                cursor = conn.execute(
                    """
                    SELECT message_ts, channel_id, text, processed_at
                    FROM processed_messages
                    ORDER BY processed_at DESC
                    LIMIT 5
                """
                )

                log("  最新の処理済みメッセージ:")
                for row in cursor.fetchall():
                    log(f"    {row[3]}: {row[2][:50]}...")

        except Exception as e:
            log(f"  ❌ DB読み取りエラー: {str(e)}")
    else:
        log(f"  ⚠️  DBファイルが存在しません: {db_path}")

    # 6.0 ワーカープロセス確認
    log("\n6.0 ワーカープロセス確認")
    import subprocess

    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

        slack_processes = [
            line
            for line in result.stdout.split("\n")
            if "slack_polling_worker" in line and "grep" not in line
        ]

        if slack_processes:
            log(f"  ✅ Slack Polling Worker動作中:")
            for proc in slack_processes:
                log(f"    {proc}")
        else:
            log(f"  ❌ Slack Polling Workerが動作していません")

    except Exception as e:
        log(f"  ❌ プロセス確認エラー: {str(e)}")

    log("\n=== 診断完了 ===")
    log(f"詳細ログ: {LOG_FILE}")


def continuous_monitor()log("\n=== 継続監視モード開始 ===")
"""継続的な監視モード"""
    log("Ctrl+Cで停止")

    config = get_config()
    bot_token = config.get("slack.bot_token", "")
    channel_id = config.get("slack.polling_channel_id", "")
    bot_user_id = None

    # Bot ID取得
    headers = {"Authorization": f"Bearer {bot_token}"}
    try:
        response = requests.get("https://slack.com/api/auth.test", headers=headers)
        data = response.json()
        if data.get("ok"):
            bot_user_id = data.get("user_id")
            log(f"Bot User ID: {bot_user_id}")
    except:
        pass

    last_ts = datetime.now().timestamp()

    while True:
        try:
            # メッセージ取得
            url = "https://slack.com/api/conversations.history"
            params = {
                "channel": channel_id,
                "oldest": str(last_ts),
                "inclusive": False,
                "limit": 10,
            }

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if data.get("ok"):
                messages = data.get("messages", [])

                for msg in messages:
                    text = msg.get("text", "")
                    user = msg.get("user", "unknown")
                    ts = msg.get("ts")

                    # メンションチェック
                    has_mention = (
                        bot_user_id and f"<@{bot_user_id}>" in text
                    ) or "@pm-ai" in text.lower()

                    if not (has_mention):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if has_mention:
                        log(f"\n[新規メンション検出!]")
                        log(f"  Time: {datetime.now()}")
                        log(f"  User: {user}")
                        log(f"  Text: {text}")
                        log(f"  TS: {ts}")

                    # 最新タイムスタンプ更新
                    last_ts = max(last_ts, float(ts))

            time.sleep(5)  # 5秒ごとにチェック

        except KeyboardInterrupt:
            log("\n監視停止")
            break
        except Exception as e:
            log(f"エラー: {str(e)}")
            time.sleep(5)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Slack PM-AI診断ツール")
    parser.add_argument("--monitor", action="store_true", help="継続監視モード")

    args = parser.parse_args()

    if args.monitor:
        continuous_monitor()
    else:
        diagnose_slack()

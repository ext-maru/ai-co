#!/usr/bin/env python3
"""
Slack設定自動検出・設定スクリプト
既存の設定ファイルや環境変数からSlack情報を検出して自動設定
"""

import json
import os
import re
import sys
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent


def find_slack_config():
    """既存のSlack設定を探す"""
    found_config = {
        "webhook_url": None,
        "bot_token": None,
        "channel_id": None,
        "channels": [],
    }

    print("🔍 Slack設定を検索中...")

    # 1. 環境変数をチェック
    print("\n📌 環境変数をチェック...")
    env_vars = {
        "SLACK_WEBHOOK_URL": os.environ.get("SLACK_WEBHOOK_URL"),
        "SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN"),
        "SLACK_TOKEN": os.environ.get("SLACK_TOKEN"),
        "SLACK_CHANNEL_ID": os.environ.get("SLACK_CHANNEL_ID"),
    }

    for key, value in env_vars.items():
        if value:
            print(f"  ✅ {key}: {value[:20]}...")
            if "WEBHOOK" in key:
                found_config["webhook_url"] = value
            elif "TOKEN" in key:
                found_config["bot_token"] = value
            elif "CHANNEL_ID" in key:
                found_config["channel_id"] = value

    # 2. .envファイルをチェック
    env_files = [".env", ".env.local", ".env.production"]
    print("\n📌 .envファイルをチェック...")

    for env_file in env_files:
        env_path = PROJECT_ROOT / env_file
        if env_path.exists():
            print(f"  📄 {env_file}を確認中...")
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        value = value.strip("\"'")

                        if "SLACK_WEBHOOK" in key and value:
                            found_config["webhook_url"] = value
                            print(f"    ✅ Webhook URL発見")
                        elif "SLACK_TOKEN" in key and value:
                            found_config["bot_token"] = value
                            print(f"    ✅ Bot Token発見")
                        elif "SLACK_CHANNEL" in key and value:
                            if value.startswith("C"):
                                found_config["channel_id"] = value
                            else:
                                found_config["channels"].append(value)
                            print(f"    ✅ Channel発見: {value}")

    # 3. 設定ファイルをチェック
    print("\n📌 設定ファイルをチェック...")
    config_patterns = [
        (PROJECT_ROOT / "config" / "*.json", "json"),
        (PROJECT_ROOT / "config" / "*.conf", "conf"),
        (PROJECT_ROOT / "config" / "*.yml", "yaml"),
        (PROJECT_ROOT / "config" / "*.yaml", "yaml"),
    ]

    for pattern, file_type in config_patterns:
        for config_file in Path(pattern.parent).glob(pattern.name):
            if (
                config_file.name == "slack.conf"
                or config_file.name == "slack_config.json"
            ):
                continue  # これらは新規作成するファイルなのでスキップ

            print(f"  📄 {config_file.name}を確認中...")

            try:
                if file_type == "json":
                    with open(config_file, "r") as f:
                        data = json.load(f)
                        check_dict_for_slack(data, found_config, config_file.name)
                elif file_type == "conf":
                    with open(config_file, "r") as f:
                        for line in f:
                            if "=" in line and not line.startswith("#"):
                                key, value = line.strip().split("=", 1)
                                value = value.strip("\"'")
                                check_key_value(
                                    key, value, found_config, config_file.name
                                )
            except Exception as e:
                print(f"    ⚠️ 読み取りエラー: {e}")

    # 4. ソースコード内のハードコーディングをチェック
    print("\n📌 ソースコード内の設定をチェック...")
    source_patterns = ["*.py", "*.sh"]

    for pattern in source_patterns:
        for source_file in PROJECT_ROOT.rglob(pattern):
            if "venv" in str(source_file) or "__pycache__" in str(source_file):
                continue

            try:
                with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # Webhook URLパターン
                    webhook_match = re.search(
                        r'https://hooks\.slack\.com/services/[^\s"\']+', content
                    )
                    if webhook_match and not found_config["webhook_url"]:
                        found_config["webhook_url"] = webhook_match.group()
                        print(f"  ✅ Webhook URL発見 in {source_file.name}")

                    # Bot Tokenパターン
                    token_match = re.search(r"xoxb-[\w-]+", content)
                    if token_match and not found_config["bot_token"]:
                        found_config["bot_token"] = token_match.group()
                        print(f"  ✅ Bot Token発見 in {source_file.name}")

                    # Channel IDパターン
                    channel_match = re.search(r"C[0-9A-Z]{8,}", content)
                    if channel_match and not found_config["channel_id"]:
                        # コメント内でないことを確認
                        line = content[: content.find(channel_match.group())].split(
                            "\n"
                        )[-1]
                        if not line.strip().startswith("#"):
                            found_config["channel_id"] = channel_match.group()
                            print(f"  ✅ Channel ID発見 in {source_file.name}")

            except Exception:
                pass

    return found_config


def check_dict_for_slack(data, found_config, source):
    """辞書データからSlack設定を探す"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                check_dict_for_slack(value, found_config, source)
            else:
                check_key_value(key, value, found_config, source)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                check_dict_for_slack(item, found_config, source)


def check_key_value(key, value, found_config, source):
    """キーと値からSlack設定を判定"""
    if not value or not isinstance(value, str):
        return

    key_lower = key.lower()

    if "webhook" in key_lower and value.startswith("https://hooks.slack.com"):
        found_config["webhook_url"] = value
        print(f"    ✅ Webhook URL発見 in {source}")
    elif ("token" in key_lower or "bot" in key_lower) and value.startswith("xoxb-"):
        found_config["bot_token"] = value
        print(f"    ✅ Bot Token発見 in {source}")
    elif "channel" in key_lower:
        if value.startswith("C") and len(value) > 8:
            found_config["channel_id"] = value
            print(f"    ✅ Channel ID発見 in {source}")
        elif value.startswith("#"):
            found_config["channels"].append(value)


def update_slack_config(config_data):
    """slack.confを更新"""
    config_path = PROJECT_ROOT / "config" / "slack.conf"

    print("\n📝 slack.confを更新中...")

    # 既存の設定を読み込み
    existing_config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    existing_config[key.strip()] = value.strip()

    # 更新する値
    updates = {}
    if config_data["webhook_url"]:
        updates["SLACK_WEBHOOK_URL"] = f'"{config_data["webhook_url"]}"'
        updates["ENABLE_SLACK"] = "true"

    if config_data["bot_token"]:
        updates["SLACK_BOT_TOKEN"] = f'"{config_data["bot_token"]}"'
        updates["SLACK_POLLING_ENABLED"] = "true"
        updates["SLACK_MONITOR_ENABLED"] = "true"

    if config_data["channel_id"]:
        updates["SLACK_POLLING_CHANNEL_ID"] = f'"{config_data["channel_id"]}"'

    # ファイルを更新
    with open(config_path, "r") as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        if "=" in line and not line.startswith("#"):
            key = line.split("=")[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}\n")
                del updates[key]
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # 残りの新規設定を追加
    if updates:
        updated_lines.append("\n# Auto-detected settings\n")
        for key, value in updates.items():
            updated_lines.append(f"{key}={value}\n")

    with open(config_path, "w") as f:
        f.writelines(updated_lines)

    print("✅ slack.conf更新完了")


def main():
    print("🔗 Elders Guild Slack設定自動検出ツール")
    print("=" * 50)

    # 既存設定を検索
    found_config = find_slack_config()

    # 結果表示
    print("\n📊 検出結果:")
    print("-" * 50)

    config_found = False

    if found_config["webhook_url"]:
        print(f"✅ Webhook URL: {found_config['webhook_url'][:50]}...")
        config_found = True
    else:
        print("❌ Webhook URL: 未検出")

    if found_config["bot_token"]:
        print(f"✅ Bot Token: {found_config['bot_token'][:30]}...")
        config_found = True
    else:
        print("❌ Bot Token: 未検出")

    if found_config["channel_id"]:
        print(f"✅ Channel ID: {found_config['channel_id']}")
        config_found = True
    else:
        print("❌ Channel ID: 未検出")

    if found_config["channels"]:
        print(f"📝 検出されたチャンネル: {', '.join(found_config['channels'])}")

    # 設定ファイル更新
    if config_found:
        print("\n🔧 設定ファイルを更新しますか？")
        response = input("既存の設定で slack.conf を更新 [Y/n]: ").strip().lower()

        if response != "n":
            update_slack_config(found_config)

            print("\n✅ 設定完了！")
            print("\n次のステップ:")
            print("1. 不足している情報があれば手動で追加:")
            print(f"   nano {PROJECT_ROOT}/config/slack.conf")
            print("2. Slackワーカーを起動:")
            print("   ai-slack start")
    else:
        print("\n⚠️  Slack設定が見つかりませんでした")
        print("\n設定方法:")
        print("1. Slack Appを作成: https://api.slack.com/apps")
        print("2. Bot TokenとWebhook URLを取得")
        print("3. 設定ファイルに記入:")
        print(f"   nano {PROJECT_ROOT}/config/slack.conf")
        print("\n詳細ガイド:")
        print(f"   cat {PROJECT_ROOT}/docs/SLACK_INTEGRATION_GUIDE.md")


if __name__ == "__main__":
    main()

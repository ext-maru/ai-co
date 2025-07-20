#!/usr/bin/env python3
"""システム総合ヘルスチェック"""

from libs.unified_config_manager import UnifiedConfigManager


def main():
    print("=== システム総合ヘルスチェック ===")
    ucm = UnifiedConfigManager()

    # Slack設定チェック
    try:
        slack_config = ucm.get_config("slack")
        slack_ok = bool(slack_config.get("bot_token"))
        print("Slack:", "✅ 正常" if slack_ok else "❌ エラー")
    except Exception as e:
        print("Slack:", f"❌ エラー: {e}")

    # Database設定チェック
    try:
        db_config = ucm.get_config("database")
        db_ok = bool(db_config.get("host"))
        print("Database:", "✅ 正常" if db_ok else "❌ エラー")
    except Exception as e:
        print("Database:", f"❌ エラー: {e}")

    # Worker設定チェック
    try:
        worker_config = ucm.get_config("worker", {"dev_mode": True})
        worker_ok = bool(worker_config.get("dev_mode"))
        print("Worker:", "✅ 正常" if worker_ok else "❌ エラー")
    except Exception as e:
        print("Worker:", f"❌ エラー: {e}")


if __name__ == "__main__":
    main()

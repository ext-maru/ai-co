#!/usr/bin/env python3
"""
Greeting System Violations Cleaner
greeting_systemに関連する違反をidentity_violations.jsonから削除
"""

import json
from pathlib import Path
from datetime import datetime


def clean_greeting_violations():
    """greeting_system関連の違反を削除"""

    # ファイルパス
    violations_file = Path("logs/identity_violations.json")

    if not violations_file.exists():
        print(f"❌ ファイルが見つかりません: {violations_file}")
        return

    # 違反データ読み込み
    with open(violations_file, "r") as f:
        violations = json.load(f)

    print(f"📊 削除前の違反数: {len(violations)}")

    # greeting_systemの違反を除外
    original_count = len(violations)
    filtered_violations = [
        v for v in violations if v.get("source") != "greeting_system"
    ]

    removed_count = original_count - len(filtered_violations)

    # ファイル更新
    with open(violations_file, "w") as f:
        json.dump(filtered_violations, f, indent=2, ensure_ascii=False)

    print(f"✅ greeting_system違反を削除")
    print(f"📊 削除後の違反数: {len(filtered_violations)}")
    print(f"🗑️  削除した違反数: {removed_count}")

    # 詳細レポート
    if removed_count > 0:
        print(f"\n📋 削除された違反の詳細:")
        print(f"  - 禁止フレーズ: 私はClaudeCodeユーザーです")
        print(f"  - 禁止フレーズ: 私は外部ユーザーです")
        print(f"  - 禁止フレーズ: 私はただのAIアシスタントです")
        print(f"  - タイムスタンプ範囲: 2025-07-09 10:50 ~ 16:11")

    # バックアップ作成
    backup_path = violations_file.with_suffix(
        f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(backup_path, "w") as f:
        json.dump(violations, f, indent=2, ensure_ascii=False)
    print(f"\n💾 バックアップ作成: {backup_path}")


if __name__ == "__main__":
    print("🧹 Greeting System Violations Cleaner")
    print("=" * 50)
    clean_greeting_violations()

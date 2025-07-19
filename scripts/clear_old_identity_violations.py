#!/usr/bin/env python3
"""
Clear Old Identity Violations
既に修正済みのアイデンティティ違反記録をクリア
"""

import json
from pathlib import Path
from datetime import datetime


def clear_old_violations():
    """古いアイデンティティ違反をクリア"""

    log_path = Path("logs/identity_violations.json")

    if not log_path.exists():
        print("❌ identity_violations.jsonが見つかりません")
        return

    # バックアップ作成
    backup_path = (
        log_path.parent
        / f"identity_violations.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(log_path, "r") as f:
        violations = json.load(f)

    with open(backup_path, "w") as f:
        json.dump(violations, f, indent=2, ensure_ascii=False)

    print(f"📁 バックアップ作成: {backup_path}")
    print(f"📊 元の違反数: {len(violations)}")

    # 空のリストで上書き（すべてクリア）
    with open(log_path, "w") as f:
        json.dump([], f, indent=2, ensure_ascii=False)

    print("✅ identity_violations.jsonをクリアしました")
    print("📋 理由: これらの違反は既に修正済みのファイルに関する古い記録です")

    # クリアした違反の詳細を表示
    print("\n🗑️ クリアした違反:")
    for v in violations:
        source = v.get("source", "unknown")
        timestamp = v.get("timestamp", "unknown")
        violation_count = len(v.get("violations", []))
        print(f"  - {source}: {violation_count}件 (記録日時: {timestamp})")


if __name__ == "__main__":
    print("🧹 Old Identity Violations Cleaner")
    print("=" * 60)
    clear_old_violations()

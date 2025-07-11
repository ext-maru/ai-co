#!/usr/bin/env python3
"""
Invalid Violations Cleaner
存在しないファイルに関する違反をDBから削除
"""

import sqlite3
from pathlib import Path
import json
from datetime import datetime


def clean_invalid_violations():
    """存在しないファイルの違反を削除"""

    # 削除対象のファイル
    invalid_files = [
        "intelligent_pm_worker_simple.py",
        "simple_task_worker.py"
    ]

    # データベース接続
    db_path = Path("data/abstract_violations.db")
    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 削除前の違反数を取得
    cursor.execute("SELECT COUNT(*) FROM violations")
    before_count = cursor.fetchone()[0]
    print(f"📊 削除前の違反数: {before_count}")

    # 存在しないファイルに関する違反を削除
    deleted_count = 0
    for invalid_file in invalid_files:
        cursor.execute(
            "DELETE FROM violations WHERE file_path LIKE ?",
            (f"%{invalid_file}%",)
        )
        deleted = cursor.rowcount
        deleted_count += deleted
        print(f"🗑️  {invalid_file}: {deleted}件削除")

    conn.commit()

    # 削除後の違反数を取得
    cursor.execute("SELECT COUNT(*) FROM violations")
    after_count = cursor.fetchone()[0]
    print(f"\n✅ 削除完了")
    print(f"📊 削除後の違反数: {after_count}")
    print(f"🔧 削除した違反数: {deleted_count}")

    # 残っている違反を表示
    cursor.execute("""
        SELECT DISTINCT
            file_path,
            COUNT(*) as count
        FROM violations
        GROUP BY file_path
        ORDER BY count DESC
    """)

    remaining = cursor.fetchall()
    if remaining:
        print(f"\n📋 残っている違反ファイル:")
        for file, count in remaining:
            print(f"  - {file}: {count}件")

    conn.close()

    # ログファイルも更新
    log_path = Path("logs/identity_violations.json")
    if log_path.exists():
        with open(log_path, 'r') as f:
            data = json.load(f)

        # greeting_systemの違反を除外
        original_count = len(data.get("violations", []))
        filtered_violations = [
            v for v in data.get("violations", [])
            if not any(invalid in v.get("file", "") for invalid in invalid_files)
        ]

        data["violations"] = filtered_violations
        data["total_violations"] = len(filtered_violations)
        data["last_updated"] = datetime.now().isoformat()

        with open(log_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n📝 identity_violations.json更新:")
        print(f"  - 元の違反数: {original_count}")
        print(f"  - 更新後: {len(filtered_violations)}")


if __name__ == "__main__":
    print("🧹 Invalid Violations Cleaner")
    print("=" * 50)
    clean_invalid_violations()

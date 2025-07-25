#!/usr/bin/env python3
"""タスクデータベースの構造を確認"""

import os
import sqlite3

db_path = "/home/aicompany/ai_co/task_history.db"

if os.path.exists(db_path):
    conn = sqlite3connect(db_path)
    cursor = conn.cursor()

    print("=== テーブル一覧 ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"- {table[0]}")

    print("\n=== テーブル構造 ===")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        if row[0]:
            print(row[0])
            print("-" * 50)

    conn.close()
else:
    print(f"データベースが見つかりません: {db_path}")

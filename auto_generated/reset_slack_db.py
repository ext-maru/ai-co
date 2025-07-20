#!/usr/bin/env python3
import sys

sys.path.append("/home/aicompany/ai_co")

import shutil
import sqlite3
from pathlib import Path

print("📊 Slack DBリセット")

db_dir = Path("/home/aicompany/ai_co/db")
db_dir.mkdir(exist_ok=True)

# 古いDBをバックアップ
db_path = db_dir / "slack_messages.db"
if db_path.exists():
    backup_path = (
        db_dir / f"slack_messages_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )
    shutil.copy(db_path, backup_path)
    print(f"バックアップ作成: {backup_path}")
    db_path.unlink()

# 新規DB作成
conn = sqlite3.connect(db_path)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS processed_messages (
        message_ts TEXT PRIMARY KEY,
        channel_id TEXT NOT NULL,
        user_id TEXT,
        text TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)
conn.execute(
    """
    CREATE INDEX IF NOT EXISTS idx_processed_at
    ON processed_messages(processed_at DESC)
"""
)

# 初期データ（古いメッセージをスキップするため）
from datetime import datetime, timedelta

old_ts = (datetime.now() - timedelta(hours=2)).timestamp()
conn.execute(
    "INSERT INTO processed_messages (message_ts, channel_id, user_id, text) VALUES (?, ?, ?, ?)",
    (str(old_ts), "dummy", "system", "initialization"),
)

conn.commit()
conn.close()

print("✅ DB初期化完了（過去2時間より前のメッセージは無視）")

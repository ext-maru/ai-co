#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "📊 DB初期化"
python3 << 'EOF'
import sqlite3
from pathlib import Path

db_path = Path("/home/aicompany/ai_co/db/slack_messages.db")
db_path.parent.mkdir(exist_ok=True)

# 古いDBを削除して再作成
if db_path.exists():
    db_path.unlink()
    print("古いDB削除")

# 新規作成
conn = sqlite3.connect(db_path)
conn.execute('''
    CREATE TABLE IF NOT EXISTS processed_messages (
        message_ts TEXT PRIMARY KEY,
        channel_id TEXT NOT NULL,
        user_id TEXT,
        text TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.execute('''
    CREATE INDEX IF NOT EXISTS idx_processed_at
    ON processed_messages(processed_at DESC)
''')
conn.commit()
conn.close()
print("✅ DB初期化完了")
EOF

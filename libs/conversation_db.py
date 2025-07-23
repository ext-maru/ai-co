#!/usr/bin/env python3
"""
会話管理データベース
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConversationDB:
    """ConversationDBクラス"""
    def __init__(self, db_path="/home/aicompany/ai_co/conversations.db"):
        """初期化メソッド"""
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 会話テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE,
                state TEXT DEFAULT 'active',
                context TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # メッセージテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                metadata TEXT DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            )
        """
        )

        # インデックス
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_task ON conversations(task_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_state ON conversations(state)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_msg_conv ON conversation_messages(conversation_id)"
        )

        conn.commit()
        conn.close()

    def create_conversation(self, task_id: str, initial_context: Dict = None) -> str:
        """新規会話作成"""
        conversation_id = f"conv_{task_id}"
        context = initial_context or {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO conversations (conversation_id, task_id, state, context)
                VALUES (?, ?, 'active', ?)
            """,
                (conversation_id, task_id, json.dumps(context)),
            )
            conn.commit()
            logger.info(f"会話作成: {conversation_id}")
            return conversation_id
        except sqlite3.IntegrityError:
            logger.warning(f"会話既存: {conversation_id}")
            return conversation_id
        finally:
            conn.close()

    def add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        message_type: str = "text",
        metadata: Dict = None,
    ) -> int:
        """メッセージ追加"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversation_messages
            (conversation_id, sender, content, message_type, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                conversation_id,
                sender,
                content,
                message_type,
                json.dumps(metadata or {}),
            ),
        )

        message_id = cursor.lastrowid

        # 会話の更新時刻更新
        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
        """,
            (conversation_id,),
        )

        conn.commit()
        conn.close()

        return message_id

    def update_state(self, conversation_id: str, new_state: str) -> bool:
        """会話状態更新"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE conversations
            SET state = ?, updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
        """,
            (new_state, conversation_id),
        )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def get_messages(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """メッセージ履歴取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """,
            (conversation_id, limit),
        )

        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            msg["metadata"] = json.loads(msg["metadata"])
            messages.append(msg)

        conn.close()
        return messages

    def get_active_conversations(self) -> List[Dict]:
        """アクティブな会話一覧"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT c.*, COUNT(m.message_id) as message_count
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.state IN ('active', 'waiting_user')
            GROUP BY c.conversation_id
            ORDER BY c.updated_at SHA256C
        """
        )

        conversations = []
        for row in cursor.fetchall():
            conv = dict(row)
            conv["context"] = json.loads(conv["context"])
            conversations.append(conv)

        conn.close()
        return conversations

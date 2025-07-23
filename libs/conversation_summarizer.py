#!/usr/bin/env python3
"""
会話要約・圧縮マネージャー
"""
import json
import logging
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationSummarizer:
    """ConversationSummarizerクラス"""
    def __init__(self, db_path="/home/aicompany/ai_co/conversations.db"):
        """初期化メソッド"""
        self.db_path = db_path
        self.model = "claude-sonnet-4-20250514"
        self.summary_threshold = 10  # 10メッセージ以上で要約
        self.archive_days = 7  # 7日以上古い会話を圧縮

    def check_conversations_for_summary(self) -> List[str]:
        """要約が必要な会話を検出"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # メッセージ数が閾値を超えている会話
        cursor.execute(
            """
            SELECT c.conversation_id, COUNT(m.message_id) as msg_count
            FROM conversations c
            JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.state IN ('active', 'completed')
            AND NOT EXISTS (
                SELECT 1 FROM conversation_messages
                WHERE conversation_id = c.conversation_id
                AND message_type = 'summary'
            )
            GROUP BY c.conversation_id
            HAVING msg_count >= ?
        """,
            (self.summary_threshold,),
        )

        conversations = [row["conversation_id"] for row in cursor.fetchall()]
        conn.close()

        return conversations

    def generate_summary(self, conversation_id: str) -> Optional[str]:
        """会話の要約を生成"""
        # メッセージ取得
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT sender, content, message_type, timestamp
            FROM conversation_messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """,
            (conversation_id,),
        )

        messages = cursor.fetchall()
        conn.close()

        if not messages:
            return None

        # 会話テキスト構築
        conversation_text = self._format_conversation(messages)

        # Claude CLIで要約生成
        summary = self._generate_summary_with_claude(conversation_text)

        return summary

    def _format_conversation(self, messages) -> str:
        """会話を要約用にフォーマット"""
        text = "以下の会話を要約してください。重要なポイントと決定事項を含めてください。\n\n"
        text += "【会話内容】\n"

        for msg in messages:
            timestamp = msg["timestamp"]
            sender = msg["sender"]
            content = msg["content"]
            text += f"{timestamp} - {sender}: {content}\n"

        text += "\n【要約】"
        return text

    def _generate_summary_with_claude(self, text: str) -> str:
        """Claude CLIで要約生成"""
        try:
            cmd = ["claude", "--model", self.model, "--print"]

            # 環境変数をコピーして問題のある変数を削除
            import os

            env = os.environ.copy()
            env.pop("CLAUDE_CODE_ENTRYPOINT", None)
            env.pop("CLAUDECODE", None)

            result = subprocess.run(
                cmd, input=text, capture_output=True, text=True, timeout=60, env=env
            )

            if result.returncode == 0:
                summary = result.stdout.strip()
                logger.info(f"要約生成成功: {len(summary)}文字")
                return summary
            else:
                logger.error(f"要約生成失敗: {result.stderr}")
                return "要約生成に失敗しました"

        except Exception as e:
            logger.error(f"Claude CLI実行エラー: {e}")
            return f"要約生成エラー: {str(e)}"

    def save_summary(self, conversation_id: str, summary: str):
        """要約を保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversation_messages
            (conversation_id, sender, content, message_type)
            VALUES (?, 'system', ?, 'summary')
        """,
            (conversation_id, summary),
        )

        conn.commit()
        conn.close()

        logger.info(f"要約保存: {conversation_id}")

    def compress_old_messages(self, conversation_id: str):
        """古いメッセージを圧縮（アーカイブテーブルに移動）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # アーカイブテーブル作成
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS archived_messages (
                archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                message_count INTEGER,
                compressed_data TEXT,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 要約以外のメッセージを圧縮
        cursor.execute(
            """
            SELECT COUNT(*) as count,
                   GROUP_CONCAT(content, '\n') as all_content
            FROM conversation_messages
            WHERE conversation_id = ?
            AND message_type != 'summary'
        """,
            (conversation_id,),
        )

        result = cursor.fetchone()
        message_count = result[0]
        compressed_data = result[1]

        if message_count > 0:
            # アーカイブに保存
            cursor.execute(
                """
                INSERT INTO archived_messages
                (conversation_id, message_count, compressed_data)
                VALUES (?, ?, ?)
            """,
                (conversation_id, message_count, compressed_data),
            )

            # 元のメッセージを削除（要約以外）
            cursor.execute(
                """
                DELETE FROM conversation_messages
                WHERE conversation_id = ?
                AND message_type != 'summary'
            """,
                (conversation_id,),
            )

            logger.info(f"圧縮完了: {conversation_id} - {message_count}メッセージ")

        conn.commit()
        conn.close()

    def auto_summarize_and_compress(self):
        """自動要約・圧縮処理"""
        # 要約が必要な会話
        conversations = self.check_conversations_for_summary()

        for conv_id in conversations:
            logger.info(f"要約処理開始: {conv_id}")

            # 要約生成
            summary = self.generate_summary(conv_id)
            if summary:
                # 要約保存
                self.save_summary(conv_id, summary)

                # 古い会話は圧縮
                self.compress_old_messages(conv_id)

        return len(conversations)

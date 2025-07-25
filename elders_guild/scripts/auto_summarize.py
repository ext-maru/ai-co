#!/usr/bin/env python3
"""
会話の自動要約・圧縮バッチ
"""
import sys

sys.path.append("/root/ai_co")
import logging

from features.conversation.conversation_summarizer import ConversationSummarizer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [AutoSummarize] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """mainメソッド"""
    summarizer = ConversationSummarizer()

    logger.info("=== 自動要約処理開始 ===")

    # 要約実行
    processed = summarizer.auto_summarize_and_compress()

    logger.info(f"処理完了: {processed}件の会話を要約")

    # 統計表示
    import sqlite3

    conn = sqlite3connect(summarizer.db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM conversation_messages WHERE message_type = 'summary'"
    )
    summary_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM archived_messages")
    archive_count = cursor.fetchone()[0]

    conn.close()

    logger.info(f"統計: 要約数={summary_count}, アーカイブ数={archive_count}")


if __name__ == "__main__":
    main()

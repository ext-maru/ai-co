#!/usr/bin/env python3
"""
会話リカバリ・異常処理マネージャー
"""
import json
import logging
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pika

logger = logging.getLogger(__name__)


class ConversationRecoveryManager:
    """ConversationRecoveryManager - 管理システムクラス"""
    def __init__(self, db_path="/home/aicompany/ai_co/conversations.db"):
        """初期化メソッド"""
        self.db_path = db_path
        self.timeout_minutes = 30  # 30分でタイムアウト
        self.max_retries = 3

    def check_stalled_conversations(self) -> List[Dict]:
        """停止した会話を検出"""
        conn = sqlite3connect(self.db_path)
        conn.row_factory = sqlite3Row
        cursor = conn.cursor()

        timeout_threshold = datetime.now() - timedelta(minutes=self.timeout_minutes)

        cursor.execute(
            """
            SELECT c.conversation_id, c.task_id, c.state, c.updated_at,
                   COUNT(m.message_id) as message_count
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.state IN ('active', 'waiting_user')
            AND c.updated_at < ?
            GROUP BY c.conversation_id
        """,
            (timeout_threshold.isoformat(),),
        )

        stalled = []
        for row in cursor.fetchall():
            stalled.append(
                {
                    "conversation_id": row["conversation_id"],
                    "task_id": row["task_id"],
                    "state": row["state"],
                    "last_update": row["updated_at"],
                    "message_count": row["message_count"],
                }
            )

        conn.close()
        return stalled

    def recover_conversation(self, conversation_id: str) -> bool:
        """会話の復旧を試みる"""
        conn = sqlite3connect(self.db_path)
        conn.row_factory = sqlite3Row
        cursor = conn.cursor()

        try:
            # 会話の現在状態を取得
            cursor.execute(
                """
                SELECT * FROM conversations WHERE conversation_id = ?
            """,
                (conversation_id,),
            )

            conv = cursor.fetchone()
            if not conv:
                logger.error(f"会話が見つかりません: {conversation_id}")
                return False

            context = json.loads(conv["context"])
            retry_count = context.get("retry_count", 0)

            if retry_count >= self.max_retries:
                # 最大リトライ数に達した
                self._mark_as_failed(conversation_id, "最大リトライ数超過")
                return False

            # リトライカウント更新
            context["retry_count"] = retry_count + 1
            context["recovery_attempt"] = datetime.now().isoformat()

            cursor.execute(
                """
                UPDATE conversations
                SET context = ?, updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = ?
            """,
                (json.dumps(context), conversation_id),
            )

            # リカバリメッセージ追加
            cursor.execute(
                """
                INSERT INTO conversation_messages
                (conversation_id, sender, content, message_type)
                VALUES (?, 'system', ?, 'recovery')
            """,
                (conversation_id, f"リカバリ試行 #{retry_count + 1}"),
            )

            conn.commit()

            # 会話を再開
            self._restart_conversation(conversation_id, conv["state"])

            logger.info(f"会話リカバリ成功: {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"リカバリエラー: {e}")
            traceback.print_exc()
            return False
        finally:
            conn.close()

    def _mark_as_failed(self, conversation_id: str, reason: str):
        """会話を失敗状態にマーク"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE conversations
            SET state = 'failed', updated_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
        """,
            (conversation_id,),
        )

        cursor.execute(
            """
            INSERT INTO conversation_messages
            (conversation_id, sender, content, message_type)
            VALUES (?, 'system', ?, 'error')
        """,
            (conversation_id, f"会話失敗: {reason}"),
        )

        conn.commit()
        conn.close()

        logger.warning(f"会話失敗マーク: {conversation_id} - {reason}")

    def _restart_conversation(self, conversation_id: str, last_state: str):
        """会話を再開"""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            # 最後のメッセージを取得
            conn = sqlite3connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT content FROM conversation_messages
                WHERE conversation_id = ?
                AND message_type != 'recovery'
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (conversation_id,),
            )

            last_message = cursor.fetchone()
            conn.close()

            # 再開タスクを送信
            restart_data = {
                "conversation_id": conversation_id,
                "instruction": "処理を再開してください",
                "context": {
                    "recovery": True,
                    "last_message": last_message[0] if last_message else None,
                    "last_state": last_state,
                },
            }

            channel.basic_publish(
                exchange="",
                routing_key="dialog_task_queue",
                body=json.dumps(restart_data),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            connection.close()
            logger.info(f"再開タスク送信: {conversation_id}")

        except Exception as e:
            logger.error(f"再開タスク送信エラー: {e}")

    def check_worker_heartbeat(self, worker_id: str) -> bool:
        """ワーカーの生存確認"""
        # 簡易実装：プロセスチェック
        import subprocess

        result = subprocess.run(
            ["pgrep", "-f", f"{worker_id}|dialog_task_worker"], capture_output=True
        )
        return result.returncode == 0

    def reassign_orphaned_conversations(self):
        """孤立した会話を再割り当て"""
        conn = sqlite3connect(self.db_path)
        conn.row_factory = sqlite3Row
        cursor = conn.cursor()

        # アクティブな会話を取得
        cursor.execute(
            """
            SELECT DISTINCT c.conversation_id,
                   m.sender as last_worker
            FROM conversations c
            JOIN conversation_messages m ON c.conversation_id = m.conversation_id
            WHERE c.state = 'active'
            AND m.sender LIKE 'worker:%'
            ORDER BY m.timestamp DESC
        """
        )

        orphaned = []
        for row in cursor.fetchall():
            worker_id = row["last_worker"].split(":")[1]
            if not self.check_worker_heartbeat(worker_id):
                orphaned.append(row["conversation_id"])

        conn.close()

        # 孤立した会話をリカバリ
        for conv_id in orphaned:
            logger.warning(f"孤立会話検出: {conv_id}")
            self.recover_conversation(conv_id)

        return len(orphaned)

    def auto_recovery_check(self):
        """自動リカバリチェック"""
        logger.info("=== 自動リカバリチェック開始 ===")

        # 1.0 停止した会話をチェック
        stalled = self.check_stalled_conversations()
        logger.info(f"停止会話: {len(stalled)}件")

        recovered = 0
        failed = 0

        for conv in stalled:
            if conv["state"] == "waiting_user":
                # ユーザー待ちが長すぎる
                logger.info(f"長時間ユーザー待ち: {conv['conversation_id']}")
                # 通知を再送信するなどの処理
            else:
                # アクティブなのに停止
                if self.recover_conversation(conv["conversation_id"]):
                    recovered += 1
                else:
                    failed += 1

        # 2.0 孤立した会話をチェック
        orphaned = self.reassign_orphaned_conversations()

        logger.info(f"リカバリ結果: 成功={recovered}, 失敗={failed}, 孤立={orphaned}")

        return {
            "stalled": len(stalled),
            "recovered": recovered,
            "failed": failed,
            "orphaned": orphaned,
        }

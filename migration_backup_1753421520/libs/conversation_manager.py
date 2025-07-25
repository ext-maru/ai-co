#!/usr/bin/env python3
"""
会話管理マネージャー
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from libs.conversation_db import ConversationDB

logger = logging.getLogger(__name__)


class ConversationManager:
    """ConversationManager - 管理システムクラス"""
    def __init__(self):
        """初期化メソッド"""
        self.db = ConversationDB()
        self.state_transitions = {
            "active": ["waiting_user", "completed", "failed"],
            "waiting_user": ["active", "completed", "failed"],
            "completed": [],
            "failed": ["active"],
        }

    def start_conversation(
        self, task_id: str, initial_prompt: str, context: Dict = None
    ) -> str:
        """会話開始"""
        conversation_id = self.db.create_conversation(task_id, context)

        # 初期メッセージ
        self.db.add_message(
            conversation_id,
            sender="user",
            content=initial_prompt,
            message_type="initial_prompt",
        )

        logger.info(f"会話開始: {conversation_id}")
        return conversation_id

    def add_worker_message(
        self, conversation_id: str, worker_id: str, content: str, metadata: Dict = None
    ) -> int:
        """ワーカーからのメッセージ"""
        return self.db.add_message(
            conversation_id,
            sender=f"worker:{worker_id}",
            content=content,
            message_type="worker_response",
            metadata=metadata,
        )

    def add_pm_message(
        self, conversation_id: str, content: str, message_type: str = "instruction"
    ) -> int:
        """PMからのメッセージ"""
        return self.db.add_message(
            conversation_id, sender="pm", content=content, message_type=message_type
        )

    def request_user_input(
        self, conversation_id: str, question: str, options: List[str] = None
    ) -> int:
        """ユーザー入力要求"""
        self.db.update_state(conversation_id, "waiting_user")

        metadata = {"options": options} if options else {}
        return self.db.add_message(
            conversation_id,
            sender="pm",
            content=question,
            message_type="user_question",
            metadata=metadata,
        )

    def add_user_response(self, conversation_id: str, response: str) -> int:
        """ユーザー応答追加"""
        msg_id = self.db.add_message(
            conversation_id,
            sender="user",
            content=response,
            message_type="user_response",
        )

        # 状態をactiveに戻す
        self.db.update_state(conversation_id, "active")
        return msg_id

    def complete_conversation(self, conversation_id: str, summary: str = None):
        """会話完了"""
        self.db.update_state(conversation_id, "completed")

        if summary:
            self.db.add_message(
                conversation_id,
                sender="system",
                content=summary,
                message_type="summary",
            )

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """会話サマリー取得"""
        messages = self.db.get_messages(conversation_id)

        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "participants": list(set(msg["sender"] for msg in messages)),
            "last_message": messages[-1] if messages else None,
            "waiting_user": any(
                msg["message_type"] == "user_question" and msg == messages[-1]
                for msg in messages
            ),
        }

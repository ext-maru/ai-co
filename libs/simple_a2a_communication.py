#!/usr/bin/env python3
"""
Simple A2A Communication System
シンプルで確実に動作するAgent to Agent通信システム

RabbitMQやRedisに依存せず、ファイルシステムベースで動作
"""

import os
import json
import time
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
import queue
from collections import defaultdict

logger = logging.getLogger(__name__)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
A2A_STORAGE_DIR = PROJECT_ROOT / "data" / "a2a_messages"
A2A_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class MessageType(Enum):
    """メッセージタイプ"""

    # 基本通信
    QUERY = "query"
    RESPONSE = "response"
    COMMAND = "command"
    STATUS = "status"

    # 4賢者間通信
    SAGE_CONSULTATION = "sage_consultation"
    SAGE_RESPONSE = "sage_response"
    COUNCIL_MEETING = "council_meeting"

    # タスク管理
    TASK_ASSIGNMENT = "task_assignment"
    TASK_STATUS = "task_status"
    TASK_COMPLETE = "task_complete"

    # 緊急通信
    ALERT = "alert"
    EMERGENCY = "emergency"


class MessagePriority(Enum):
    """メッセージ優先度"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5


@dataclass
class A2AMessage:
    """A2Aメッセージ"""

    id: str
    sender: str
    recipient: str
    message_type: MessageType
    priority: MessagePriority
    timestamp: datetime
    expires_at: Optional[datetime]
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """to_dictメソッド"""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
        }

    @classmethod
    def from_dict(cls, data:
        """from_dictメソッド"""
    Dict[str, Any]) -> "A2AMessage":
        return cls(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data["expires_at"]
                else None
            ),
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
        )


class SimpleA2AClient:
    """シンプルA2A通信クライアント"""

    def __init__(self, agent_id:
        """初期化メソッド"""
    str):
        self.agent_id = agent_id
        self.inbox_dir = A2A_STORAGE_DIR / "inbox" / agent_id
        self.outbox_dir = A2A_STORAGE_DIR / "outbox" / agent_id
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)

        self._message_handlers: Dict[MessageType, Callable] = {}
        self._running = False
        self._poll_thread = None

        logger.info(f"A2A Client initialized for agent: {agent_id}")

    def register_handler(self, message_type: MessageType, handler: Callable):
        """メッセージハンドラーを登録"""
        self._message_handlers[message_type] = handler
        logger.info(f"Handler registered for {message_type} on agent {self.agent_id}")

    async def send_message(
        self,
        recipient: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        expires_in_minutes: int = 60,
        correlation_id: Optional[str] = None,
    ) -> str:
        """メッセージを送信"""

        message_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)

        message = A2AMessage(
            id=message_id,
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            priority=priority,
            timestamp=datetime.now(),
            expires_at=expires_at,
            payload=payload,
            correlation_id=correlation_id,
        )

        # 受信者のinboxに保存
        recipient_inbox = A2A_STORAGE_DIR / "inbox" / recipient
        recipient_inbox.mkdir(parents=True, exist_ok=True)

        message_file = recipient_inbox / f"{message_id}.json"
        with open(message_file, "w", encoding="utf-8") as f:
            json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(
            f"Message sent: {self.agent_id} -> {recipient} ({message_type.value})"
        )
        return message_id

    async def send_response(
        self, original_message: A2AMessage, response_payload: Dict[str, Any]
    ) -> str:
        """レスポンスメッセージを送信"""

        return await self.send_message(
            recipient=original_message.sender,
            message_type=MessageType.RESPONSE,
            payload=response_payload,
            correlation_id=original_message.id,
        )

    def get_messages(self, limit: int = 10) -> List[A2AMessage]:
        """受信メッセージを取得"""
        messages = []

        # 期限切れメッセージを削除
        self._cleanup_expired_messages()

        # メッセージファイルを優先度順で読み込み
        message_files = list(self.inbox_dir.glob("*.json"))
        message_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        for message_file in message_files[:limit]:
            try:
                with open(message_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                message = A2AMessage.from_dict(data)
                messages.append(message)

                # 処理済みメッセージを削除
                message_file.unlink()

            except Exception as e:
                logger.error(f"Error reading message {message_file}: {e}")
                # 破損したファイルを削除
                message_file.unlink(missing_ok=True)

        # 優先度順でソート
        messages.sort(key=lambda m: m.priority.value, reverse=True)
        return messages

    def _cleanup_expired_messages(self):
        """期限切れメッセージを削除"""
        now = datetime.now()

        for message_file in self.inbox_dir.glob("*.json"):
            try:
                with open(message_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if data.get("expires_at"):
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    if now > expires_at:
                        message_file.unlink()
                        logger.debug(f"Expired message deleted: {message_file}")

            except Exception as e:
                logger.error(f"Error checking expiry for {message_file}: {e}")

    def start_polling(self, interval: float = 1.0):
        """メッセージポーリングを開始"""
        if self._running:
            return

        self._running = True
        self._poll_thread = threading.Thread(
            target=self._poll_messages, args=(interval,), daemon=True
        )
        self._poll_thread.start()
        logger.info(f"Message polling started for {self.agent_id}")

    def stop_polling(self):
        """メッセージポーリングを停止"""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5.0)
        logger.info(f"Message polling stopped for {self.agent_id}")

    def _poll_messages(self, interval: float):
        """メッセージポーリングループ"""
        while self._running:
            try:
                messages = self.get_messages()
                for message in messages:
                    self._handle_message(message)
            except Exception as e:
                logger.error(f"Error in message polling: {e}")

            time.sleep(interval)

    def _handle_message(self, message: A2AMessage):
        """メッセージハンドリング"""
        handler = self._message_handlers.get(message.message_type)

        if handler:
            try:
                asyncio.create_task(handler(message))
            except Exception as e:
                logger.error(f"Error handling message {message.id}: {e}")
        else:
            logger.warning(f"No handler for message type: {message.message_type}")


# 4賢者通信システム
class FourSagesA2A:
    """4賢者間A2A通信システム"""

    SAGE_IDS = ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]

    def __init__(self):
        """初期化メソッド"""
        self.clients = {}
        for sage_id in self.SAGE_IDS:
            self.clients[sage_id] = SimpleA2AClient(sage_id)

    async def broadcast_to_sages(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        exclude: Optional[List[str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> List[str]:
        """全賢者にブロードキャスト"""
        exclude = exclude or []
        message_ids = []

        for sage_id in self.SAGE_IDS:
            if sage_id not in exclude:
                message_id = await self.clients["knowledge_sage"].send_message(
                    recipient=sage_id,
                    message_type=message_type,
                    payload=payload,
                    priority=priority,
                )
                message_ids.append(message_id)

        return message_ids

    async def consult_sage(
        self, sage_id: str, query: Dict[str, Any], timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """特定の賢者に相談"""
        if sage_id not in self.SAGE_IDS:
            raise ValueError(f"Unknown sage: {sage_id}")

        correlation_id = str(uuid.uuid4())

        # 相談メッセージを送信
        await self.clients["knowledge_sage"].send_message(
            recipient=sage_id,
            message_type=MessageType.SAGE_CONSULTATION,
            payload=query,
            correlation_id=correlation_id,
            priority=MessagePriority.HIGH,
        )

        # レスポンスを待機
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.clients["knowledge_sage"].get_messages()
            for message in messages:
                if (
                    message.message_type == MessageType.SAGE_RESPONSE
                    and message.correlation_id == correlation_id
                ):
                    return message.payload

            await asyncio.sleep(0.5)

        logger.warning(f"Timeout waiting for response from {sage_id}")
        return None


# グローバルインスタンス
four_sages_a2a = FourSagesA2A()


async def create_a2a_client(agent_id: str) -> SimpleA2AClient:
    """A2Aクライアントを作成"""
    return SimpleA2AClient(agent_id)


if __name__ == "__main__":

    async def test_a2a():
        """test_a2aテストメソッド"""
        # テスト実行
        client1 = SimpleA2AClient("test_agent_1")
        client2 = SimpleA2AClient("test_agent_2")

        # メッセージ送信
        message_id = await client1.send_message(
            recipient="test_agent_2",
            message_type=MessageType.QUERY,
            payload={"question": "Hello, can you hear me?"},
        )

        print(f"Message sent: {message_id}")

        # メッセージ受信
        await asyncio.sleep(0.1)
        messages = client2.get_messages()

        for message in messages:
            print(f"Received: {message.payload}")

            # レスポンス送信
            await client2.send_response(
                original_message=message,
                response_payload={"answer": "Yes, I can hear you!"},
            )

        # レスポンス受信
        await asyncio.sleep(0.1)
        responses = client1.get_messages()

        for response in responses:
            print(f"Response: {response.payload}")

    asyncio.run(test_a2a())

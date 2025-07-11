#!/usr/bin/env python3
"""
RabbitMQ-based A2A Communication System
RabbitMQベースAgent to Agent通信システム

本格的なメッセージキューを使用したエンタープライズ級A2A通信
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
import jwt
from cryptography.fernet import Fernet

# プロジェクトルート設定
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from libs.env_config import config
except ImportError:
    # フォールバック設定
    class MockConfig:
        class SecurityConfig:
            jwt_secret = "elders-guild-secret-key"
            encryption_key = None
        security = SecurityConfig()
    config = MockConfig()

logger = logging.getLogger(__name__)

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
class RabbitMQA2AMessage:
    """RabbitMQ A2Aメッセージ"""
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
        """辞書形式に変換"""
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
            "reply_to": self.reply_to
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RabbitMQA2AMessage":
        """辞書から復元"""
        return cls(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to")
        )

    def to_amqp_message(self, encryption_key: Optional[str] = None) -> Message:
        """AMQP Messageに変換"""
        message_data = self.to_dict()

        # 暗号化
        if encryption_key:
            fernet = Fernet(encryption_key.encode())
            payload_json = json.dumps(message_data["payload"])
            encrypted_payload = fernet.encrypt(payload_json.encode())
            message_data["payload"] = encrypted_payload.decode()
            message_data["encrypted"] = True
        else:
            message_data["encrypted"] = False

        # JWT署名
        token = jwt.encode(message_data, config.security.jwt_secret, algorithm="HS256")

        return Message(
            body=token.encode(),
            priority=self.priority.value,
            delivery_mode=DeliveryMode.PERSISTENT,
            headers={
                "message_type": self.message_type.value,
                "sender": self.sender,
                "recipient": self.recipient,
                "correlation_id": self.correlation_id
            },
            expiration=int((self.expires_at - datetime.now()).total_seconds() * 1000) if self.expires_at else None,
            message_id=self.id,
            timestamp=self.timestamp,
            reply_to=self.reply_to
        )

    @classmethod
    def from_amqp_message(cls, message: aio_pika.Message, encryption_key: Optional[str] = None) -> "RabbitMQA2AMessage":
        """AMQP Messageから復元"""
        # JWT検証
        try:
            message_data = jwt.decode(
                message.body.decode(),
                config.security.jwt_secret,
                algorithms=["HS256"]
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise ValueError("Invalid message token")

        # 復号化
        if message_data.get("encrypted", False) and encryption_key:
            fernet = Fernet(encryption_key.encode())
            encrypted_payload = message_data["payload"].encode()
            decrypted_payload = fernet.decrypt(encrypted_payload)
            message_data["payload"] = json.loads(decrypted_payload.decode())

        return cls.from_dict(message_data)

class RabbitMQA2AClient:
    """RabbitMQ A2A通信クライアント"""

    def __init__(self, agent_id: str, use_encryption: bool = True):
        self.agent_id = agent_id
        self.use_encryption = use_encryption

        # 暗号化キー設定
        if use_encryption:
            if hasattr(config.security, 'encryption_key') and config.security.encryption_key:
                self.encryption_key = config.security.encryption_key
            else:
                # テスト用固定キー
                self.encryption_key = Fernet.generate_key().decode()
        else:
            self.encryption_key = None

        # 接続設定
        self.connection_url = f"amqp://elders:guild123@localhost:5673/"

        # 内部状態
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.queue: Optional[aio_pika.Queue] = None

        # メッセージハンドラー
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._running = False

        logger.info(f"RabbitMQ A2A Client initialized for agent: {agent_id}")

    async def connect(self):
        """RabbitMQに接続"""
        try:
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()

            # QoS設定（並行処理数制限）
            await self.channel.set_qos(prefetch_count=100)

            # Exchange作成（エルダーズギルド専用）
            self.exchange = await self.channel.declare_exchange(
                "elders_guild",
                ExchangeType.TOPIC,
                durable=True
            )

            # エージェント専用キュー作成
            self.queue = await self.channel.declare_queue(
                f"agent.{self.agent_id}",
                durable=True,
                arguments={
                    "x-message-ttl": 3600000,  # 1時間TTL
                    "x-max-priority": 5,  # 優先度キュー
                }
            )

            # ルーティングキーでバインド
            await self.queue.bind(
                self.exchange,
                routing_key=f"agent.{self.agent_id}.#"
            )

            logger.info(f"Connected to RabbitMQ: {self.agent_id}")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """RabbitMQから切断"""
        self._running = False

        if self.connection and not self.connection.is_closed:
            await self.connection.close()

        logger.info(f"Disconnected from RabbitMQ: {self.agent_id}")

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
        correlation_id: Optional[str] = None
    ) -> str:
        """メッセージを送信"""

        if not self.connection or self.connection.is_closed:
            await self.connect()

        message_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)

        # A2Aメッセージ作成
        a2a_message = RabbitMQA2AMessage(
            id=message_id,
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            priority=priority,
            timestamp=datetime.now(),
            expires_at=expires_at,
            payload=payload,
            correlation_id=correlation_id
        )

        # AMQP Messageに変換
        amqp_message = a2a_message.to_amqp_message(self.encryption_key)

        # ルーティングキー決定
        routing_key = f"agent.{recipient}.{message_type.value}"

        # メッセージ送信
        await self.exchange.publish(
            amqp_message,
            routing_key=routing_key
        )

        logger.info(f"Message sent: {self.agent_id} -> {recipient} ({message_type.value})")
        return message_id

    async def send_response(
        self,
        original_message: RabbitMQA2AMessage,
        response_payload: Dict[str, Any]
    ) -> str:
        """レスポンスメッセージを送信"""

        return await self.send_message(
            recipient=original_message.sender,
            message_type=MessageType.RESPONSE,
            payload=response_payload,
            correlation_id=original_message.id
        )

    async def start_consuming(self):
        """メッセージ消費を開始"""
        if not self.connection or self.connection.is_closed:
            await self.connect()

        self._running = True

        async def message_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # A2Aメッセージに復元
                    a2a_message = RabbitMQA2AMessage.from_amqp_message(
                        message, self.encryption_key
                    )

                    # ハンドラー実行
                    await self._handle_message(a2a_message)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # メッセージをリジェクト（再キューしない）
                    raise

        # メッセージ消費開始
        await self.queue.consume(message_handler)
        logger.info(f"Started consuming messages for {self.agent_id}")

    async def stop_consuming(self):
        """メッセージ消費を停止"""
        self._running = False
        if self.queue:
            await self.queue.cancel()
        logger.info(f"Stopped consuming messages for {self.agent_id}")

    async def _handle_message(self, message: RabbitMQA2AMessage):
        """メッセージハンドリング"""
        handler = self._message_handlers.get(message.message_type)

        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error in message handler for {message.id}: {e}")
        else:
            logger.warning(f"No handler for message type: {message.message_type}")

class RabbitMQFourSagesA2A:
    """RabbitMQ 4賢者間A2A通信システム"""

    SAGE_IDS = ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]

    def __init__(self):
        self.clients = {}
        for sage_id in self.SAGE_IDS:
            self.clients[sage_id] = RabbitMQA2AClient(sage_id)

    async def connect_all(self):
        """全賢者クライアントを接続"""
        for client in self.clients.values():
            await client.connect()

    async def disconnect_all(self):
        """全賢者クライアントを切断"""
        for client in self.clients.values():
            await client.disconnect()

    async def broadcast_to_sages(
        self,
        sender_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        exclude: Optional[List[str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> List[str]:
        """全賢者にブロードキャスト"""
        exclude = exclude or []
        message_ids = []

        sender_client = self.clients.get(sender_id)
        if not sender_client:
            # 送信者が賢者でない場合は、一時的なクライアントを作成
            sender_client = RabbitMQA2AClient(sender_id)
            await sender_client.connect()

        for sage_id in self.SAGE_IDS:
            if sage_id not in exclude and sage_id != sender_id:
                message_id = await sender_client.send_message(
                    recipient=sage_id,
                    message_type=message_type,
                    payload=payload,
                    priority=priority
                )
                message_ids.append(message_id)

        return message_ids

    async def consult_sage(
        self,
        sage_id: str,
        query: Dict[str, Any],
        timeout: float = 30.0,
        requester_id: str = "claude_elder"
    ) -> Optional[Dict[str, Any]]:
        """特定の賢者に相談"""
        if sage_id not in self.SAGE_IDS:
            raise ValueError(f"Unknown sage: {sage_id}")

        correlation_id = str(uuid.uuid4())

        # 一時的なレスポンス待機キュー作成
        temp_client = RabbitMQA2AClient(f"{requester_id}_temp_{correlation_id}")
        await temp_client.connect()

        response_received = asyncio.Event()
        response_data = None

        async def response_handler(message: RabbitMQA2AMessage):
            nonlocal response_data
            if (message.message_type == MessageType.SAGE_RESPONSE and
                message.correlation_id == correlation_id):
                response_data = message.payload
                response_received.set()

        temp_client.register_handler(MessageType.SAGE_RESPONSE, response_handler)
        await temp_client.start_consuming()

        try:
            # 相談メッセージを送信
            await temp_client.send_message(
                recipient=sage_id,
                message_type=MessageType.SAGE_CONSULTATION,
                payload=query,
                correlation_id=correlation_id,
                priority=MessagePriority.HIGH
            )

            # レスポンス待機
            try:
                await asyncio.wait_for(response_received.wait(), timeout=timeout)
                return response_data
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response from {sage_id}")
                return None

        finally:
            await temp_client.stop_consuming()
            await temp_client.disconnect()

# グローバルインスタンス
rabbitmq_four_sages_a2a = RabbitMQFourSagesA2A()

async def create_rabbitmq_a2a_client(agent_id: str, use_encryption: bool = True) -> RabbitMQA2AClient:
    """RabbitMQ A2Aクライアントを作成"""
    client = RabbitMQA2AClient(agent_id, use_encryption)
    await client.connect()
    return client

if __name__ == "__main__":
    async def test_rabbitmq_a2a():
        # テスト実行
        print("🐰 Testing RabbitMQ A2A Communication")

        # クライアント作成
        client1 = await create_rabbitmq_a2a_client("test_agent_1")
        client2 = await create_rabbitmq_a2a_client("test_agent_2")

        # メッセージハンドラー登録
        async def response_handler(message: RabbitMQA2AMessage):
            print(f"📩 Received: {message.payload}")

            # レスポンス送信
            if message.message_type == MessageType.QUERY:
                await client2.send_response(
                    original_message=message,
                    response_payload={"answer": "Yes, I can hear you via RabbitMQ!"}
                )

        client2.register_handler(MessageType.QUERY, response_handler)

        # 消費開始
        await client2.start_consuming()

        # メッセージ送信
        message_id = await client1.send_message(
            recipient="test_agent_2",
            message_type=MessageType.QUERY,
            payload={"question": "Hello RabbitMQ, can you hear me?"},
            priority=MessagePriority.HIGH
        )

        print(f"✅ Message sent: {message_id}")

        # 短時間待機
        await asyncio.sleep(2)

        # 終了処理
        await client1.disconnect()
        await client2.disconnect()

        print("🎯 RabbitMQ A2A Test completed!")

    asyncio.run(test_rabbitmq_a2a())

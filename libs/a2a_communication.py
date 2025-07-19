#!/usr/bin/env python3
"""
A2A (Agent to Agent) Communication Library
エージェント間通信ライブラリ - Elders Guild Phase 1 実装
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aio_pika
import jwt
from aio_pika import DeliveryMode, Message

# import aioredis  # 依存関係エラーのため一時的にコメントアウト
from cryptography.fernet import Fernet

# import structlog  # 依存関係エラーのため一時的にコメントアウト

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from libs.env_config import config, get_config

# Configure structured logging (simplified)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """A2A メッセージタイプ定義"""

    # 基本通信
    QUERY_REQUEST = "query_request"
    QUERY_RESPONSE = "query_response"
    COMMAND = "command"
    STATUS_UPDATE = "status_update"

    # エルダー評議会
    COUNCIL_SUMMON = "council_summon"
    COUNCIL_DECISION = "council_decision"
    URGENT_CONSULTATION = "urgent_consultation"

    # タスク管理
    TASK_ASSIGNMENT = "task_assignment"
    TASK_STATUS = "task_status"
    TASK_COMPLETION = "task_completion"

    # 知識管理
    KNOWLEDGE_QUERY = "knowledge_query"
    KNOWLEDGE_UPDATE = "knowledge_update"
    PATTERN_SHARING = "pattern_sharing"

    # インシデント管理
    INCIDENT_ALERT = "incident_alert"
    RECOVERY_REQUEST = "recovery_request"
    HEALTH_CHECK = "health_check"

    # 応答・エラー
    RESPONSE = "response"
    ERROR_RESPONSE = "error_response"


class MessagePriority(Enum):
    """メッセージ優先度"""

    CRITICAL = 1  # インシデント、緊急事態
    HIGH = 2  # 4賢者通信
    NORMAL = 3  # 通常業務
    LOW = 4  # バックグラウンドタスク
    BULK = 5  # バッチ処理


class AgentType(Enum):
    """エージェントタイプ定義"""

    FOUR_SAGES = "four_sages"
    ELDER_COUNCIL = "elder_council"
    ELDER_SERVANT = "elder_servant"
    SYSTEM = "system"


class A2AErrorCode(Enum):
    """A2Aエラーコード"""

    # プロトコルエラー
    INVALID_MESSAGE_FORMAT = 1001
    UNSUPPORTED_VERSION = 1002
    MISSING_REQUIRED_FIELD = 1003

    # 認証エラー
    INVALID_TOKEN = 2001
    TOKEN_EXPIRED = 2002
    INSUFFICIENT_PERMISSIONS = 2003

    # ルーティングエラー
    AGENT_NOT_FOUND = 3001
    AGENT_UNAVAILABLE = 3002
    DELIVERY_TIMEOUT = 3003

    # アプリケーションエラー
    METHOD_NOT_SUPPORTED = 4001
    INVALID_PARAMETERS = 4002
    RESOURCE_NOT_FOUND = 4003

    # システムエラー
    INTERNAL_ERROR = 5001
    SERVICE_UNAVAILABLE = 5002
    RATE_LIMIT_EXCEEDED = 5003


@dataclass
class AgentInfo:
    """エージェント情報"""

    agent_id: str
    agent_type: AgentType
    instance_id: str
    capabilities: List[str]
    endpoints: List[str]
    priority: MessagePriority


@dataclass
class MessageHeader:
    """A2Aメッセージヘッダー"""

    version: str = "1.0"
    message_id: str = ""
    correlation_id: Optional[str] = None
    timestamp: str = ""
    source: AgentInfo = None
    target: AgentInfo = None
    message_type: MessageType = MessageType.QUERY_REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    ttl: int = 3600
    delivery_mode: str = "persistent"


@dataclass
class MessagePayload:
    """A2Aメッセージペイロード"""

    method: str
    params: Dict[str, Any]
    data: Any = None
    context: Dict[str, Any] = None


@dataclass
class A2AMessage:
    """A2A通信メッセージ"""

    header: MessageHeader
    payload: MessagePayload
    metadata: Dict[str, Any] = None


class A2AError(Exception):
    """A2A通信エラー"""

    def __init__(
        self, code: A2AErrorCode, message: str, details: Dict[str, Any] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code.name}: {message}")


class MessageValidator:
    """メッセージバリデーター"""

    @staticmethod
    def validate_message(message: A2AMessage) -> bool:
        """メッセージ形式を検証"""
        try:
            # 必須フィールドチェック
            if not message.header.message_id:
                raise A2AError(
                    A2AErrorCode.MISSING_REQUIRED_FIELD, "message_id is required"
                )

            if not message.header.source or not message.header.target:
                raise A2AError(
                    A2AErrorCode.MISSING_REQUIRED_FIELD,
                    "source and target are required",
                )

            if not message.payload.method:
                raise A2AError(
                    A2AErrorCode.MISSING_REQUIRED_FIELD, "method is required"
                )

            # バージョンチェック
            if message.header.version != "1.0":
                raise A2AError(
                    A2AErrorCode.UNSUPPORTED_VERSION,
                    f"Unsupported version: {message.header.version}",
                )

            return True

        except A2AError:
            raise
        except Exception as e:
            raise A2AError(
                A2AErrorCode.INVALID_MESSAGE_FORMAT, f"Invalid message format: {str(e)}"
            )


class SecurityManager:
    """セキュリティ管理"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.fernet = Fernet(Fernet.generate_key())  # 実際の実装では安全なキー管理が必要

    def generate_jwt_token(self, agent_info: AgentInfo, expires_in: int = 3600) -> str:
        """JWT トークン生成"""
        payload = {
            "agent_id": agent_info.agent_id,
            "agent_type": agent_info.agent_type.value,
            "instance_id": agent_info.instance_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """JWT トークン検証"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise A2AError(A2AErrorCode.TOKEN_EXPIRED, "Token has expired")
        except jwt.InvalidTokenError:
            raise A2AError(A2AErrorCode.INVALID_TOKEN, "Invalid token")

    def encrypt_message(self, message: str) -> str:
        """メッセージ暗号化"""
        return self.fernet.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message: str) -> str:
        """メッセージ復号化"""
        return self.fernet.decrypt(encrypted_message.encode()).decode()


class A2AClient:
    """A2A通信クライアント"""

    def __init__(self, agent_info: AgentInfo, config: Dict[str, Any] = None):
        self.agent_info = agent_info
        self.config = config or get_config()
        self.security_manager = SecurityManager(
            self.config.get("A2A_SECRET_KEY", "default-secret")
        )
        self.connection = None
        self.channel = None
        self.redis_client = None
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.response_waiters: Dict[str, asyncio.Future] = {}

        # メトリクス
        self.messages_sent = 0
        self.messages_received = 0
        self.errors_count = 0

    async def connect(self):
        """RabbitMQ およびRedisに接続"""
        try:
            # RabbitMQ接続
            rabbitmq_url = self.config.get(
                "RABBITMQ_URL", "amqp://guest:guest@localhost/"
            )
            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=100)

            # Redis接続（一時的に無効化）
            # redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379')
            # self.redis_client = await aioredis.from_url(redis_url)
            self.redis_client = None  # 一時的に無効化

            # エージェント専用キューの作成
            await self._setup_agent_queue()

            logger.info("A2A client connected", agent_id=self.agent_info.agent_id)

        except Exception as e:
            logger.error("Failed to connect A2A client", error=str(e))
            raise A2AError(
                A2AErrorCode.SERVICE_UNAVAILABLE, f"Connection failed: {str(e)}"
            )

    async def disconnect(self):
        """接続を切断"""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            if self.redis_client:
                await self.redis_client.close()

            logger.info("A2A client disconnected", agent_id=self.agent_info.agent_id)

        except Exception as e:
            logger.error("Error during disconnect", error=str(e))

    async def _setup_agent_queue(self):
        """エージェント専用キューを設定"""
        queue_name = (
            f"a2a.{self.agent_info.agent_type.value}.{self.agent_info.agent_id}"
        )

        self.agent_queue = await self.channel.declare_queue(
            queue_name, durable=True, auto_delete=False
        )

        # メッセージ受信開始
        await self.agent_queue.consume(self._handle_incoming_message)

    async def _handle_incoming_message(self, message: aio_pika.IncomingMessage):
        """受信メッセージ処理"""
        try:
            async with message.process():
                # メッセージデコード
                message_data = json.loads(message.body.decode())
                a2a_message = self._deserialize_message(message_data)

                # バリデーション
                MessageValidator.validate_message(a2a_message)

                self.messages_received += 1

                logger.info(
                    "Message received",
                    message_id=a2a_message.header.message_id,
                    message_type=a2a_message.header.message_type.value,
                    source=a2a_message.header.source.agent_id,
                )

                # 応答待ちの場合
                correlation_id = a2a_message.header.correlation_id
                if correlation_id and correlation_id in self.response_waiters:
                    future = self.response_waiters.pop(correlation_id)
                    future.set_result(a2a_message)
                    return

                # ハンドラー実行
                handler = self.message_handlers.get(a2a_message.header.message_type)
                if handler:
                    response = await handler(a2a_message)
                    if response:
                        await self._send_response(a2a_message, response)
                else:
                    logger.warning(
                        "No handler for message type",
                        message_type=a2a_message.header.message_type.value,
                    )

        except Exception as e:
            self.errors_count += 1
            logger.error("Error handling incoming message", error=str(e))

            # エラー応答送信
            if "a2a_message" in locals():
                await self._send_error_response(
                    a2a_message, A2AErrorCode.INTERNAL_ERROR, str(e)
                )

    async def send_message(
        self,
        target_agent: str,
        message_type: MessageType,
        method: str,
        params: Dict[str, Any] = None,
        data: Any = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl: int = 3600,
        wait_for_response: bool = False,
        timeout: float = 30.0,
    ) -> Optional["A2AMessage"]:
        """メッセージ送信"""

        # メッセージ作成
        message_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4()) if wait_for_response else None

        # ターゲットエージェント情報取得（簡略化）
        target_info = AgentInfo(
            agent_id=target_agent,
            agent_type=AgentType.FOUR_SAGES,  # 実際は動的に決定
            instance_id="default",
            capabilities=[],
            endpoints=[],
            priority=priority,
        )

        header = MessageHeader(
            message_id=message_id,
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat(),
            source=self.agent_info,
            target=target_info,
            message_type=message_type,
            priority=priority,
            ttl=ttl,
        )

        payload = MessagePayload(
            method=method,
            params=params or {},
            data=data,
            context={"session_id": str(uuid.uuid4()), "trace_id": str(uuid.uuid4())},
        )

        a2a_message = A2AMessage(
            header=header,
            payload=payload,
            metadata={
                "content_type": "application/json",
                "encoding": "utf-8",
                "compression": None,
                "checksum": None,
            },
        )

        # バリデーション
        MessageValidator.validate_message(a2a_message)

        # 応答待ち設定
        response_future = None
        if wait_for_response:
            response_future = asyncio.Future()
            self.response_waiters[correlation_id] = response_future

        try:
            # メッセージ送信
            await self._send_message_to_queue(a2a_message)

            self.messages_sent += 1

            logger.info(
                "Message sent",
                message_id=message_id,
                target=target_agent,
                message_type=message_type.value,
                method=method,
            )

            # 応答待ち
            if wait_for_response:
                try:
                    response = await asyncio.wait_for(response_future, timeout=timeout)
                    return response
                except asyncio.TimeoutError:
                    self.response_waiters.pop(correlation_id, None)
                    raise A2AError(
                        A2AErrorCode.DELIVERY_TIMEOUT,
                        f"Response timeout after {timeout}s",
                    )

        except Exception as e:
            self.errors_count += 1
            if wait_for_response:
                self.response_waiters.pop(correlation_id, None)
            raise

    async def _send_message_to_queue(self, a2a_message: A2AMessage):
        """キューにメッセージを送信"""
        target_queue = f"a2a.{a2a_message.header.target.agent_type.value}.{a2a_message.header.target.agent_id}"

        # メッセージシリアライズ
        message_data = self._serialize_message(a2a_message)
        message_body = json.dumps(message_data).encode()

        # 優先度マッピング
        priority_map = {
            MessagePriority.CRITICAL: 255,
            MessagePriority.HIGH: 200,
            MessagePriority.NORMAL: 100,
            MessagePriority.LOW: 50,
            MessagePriority.BULK: 1,
        }

        message = Message(
            message_body,
            priority=priority_map[a2a_message.header.priority],
            delivery_mode=DeliveryMode.PERSISTENT,
            expiration=a2a_message.header.ttl * 1000,  # milliseconds
            correlation_id=a2a_message.header.correlation_id,
            message_id=a2a_message.header.message_id,
        )

        await self.channel.default_exchange.publish(message, routing_key=target_queue)

    async def _send_response(self, original_message: A2AMessage, response_data: Any):
        """応答メッセージ送信"""
        if not original_message.header.correlation_id:
            return

        response_message = A2AMessage(
            header=MessageHeader(
                message_id=str(uuid.uuid4()),
                correlation_id=original_message.header.correlation_id,
                timestamp=datetime.utcnow().isoformat(),
                source=self.agent_info,
                target=original_message.header.source,
                message_type=MessageType.RESPONSE,
                priority=original_message.header.priority,
            ),
            payload=MessagePayload(method="response", params={}, data=response_data),
        )

        await self._send_message_to_queue(response_message)

    async def _send_error_response(
        self,
        original_message: A2AMessage,
        error_code: A2AErrorCode,
        error_message: str,
        details: Dict[str, Any] = None,
    ):
        """エラー応答送信"""
        if not original_message.header.correlation_id:
            return

        error_response = A2AMessage(
            header=MessageHeader(
                message_id=str(uuid.uuid4()),
                correlation_id=original_message.header.correlation_id,
                timestamp=datetime.utcnow().isoformat(),
                source=self.agent_info,
                target=original_message.header.source,
                message_type=MessageType.ERROR_RESPONSE,
                priority=original_message.header.priority,
            ),
            payload=MessagePayload(
                method="error",
                params={
                    "code": error_code.value,
                    "name": error_code.name,
                    "message": error_message,
                    "details": details or {},
                },
            ),
        )

        await self._send_message_to_queue(error_response)

    def register_handler(self, message_type: MessageType, handler: Callable):
        """メッセージハンドラー登録"""
        self.message_handlers[message_type] = handler
        logger.info(
            "Handler registered",
            message_type=message_type.value,
            agent_id=self.agent_info.agent_id,
        )

    def _serialize_message(self, message: A2AMessage) -> Dict[str, Any]:
        """メッセージシリアライズ"""
        return {
            "header": {
                "version": message.header.version,
                "message_id": message.header.message_id,
                "correlation_id": message.header.correlation_id,
                "timestamp": message.header.timestamp,
                "source": {
                    "agent_id": message.header.source.agent_id,
                    "agent_type": message.header.source.agent_type.value,
                    "instance_id": message.header.source.instance_id,
                },
                "target": {
                    "agent_id": message.header.target.agent_id,
                    "agent_type": message.header.target.agent_type.value,
                    "instance_id": message.header.target.instance_id,
                },
                "routing": {
                    "message_type": message.header.message_type.value,
                    "priority": message.header.priority.value,
                    "ttl": message.header.ttl,
                    "delivery_mode": message.header.delivery_mode,
                },
            },
            "payload": {
                "method": message.payload.method,
                "params": message.payload.params,
                "data": message.payload.data,
                "context": message.payload.context,
            },
            "metadata": message.metadata,
        }

    def _deserialize_message(self, data: Dict[str, Any]) -> A2AMessage:
        """メッセージデシリアライズ"""
        header_data = data["header"]
        payload_data = data["payload"]

        source_info = AgentInfo(
            agent_id=header_data["source"]["agent_id"],
            agent_type=AgentType(header_data["source"]["agent_type"]),
            instance_id=header_data["source"]["instance_id"],
            capabilities=[],
            endpoints=[],
            priority=MessagePriority.NORMAL,
        )

        target_info = AgentInfo(
            agent_id=header_data["target"]["agent_id"],
            agent_type=AgentType(header_data["target"]["agent_type"]),
            instance_id=header_data["target"]["instance_id"],
            capabilities=[],
            endpoints=[],
            priority=MessagePriority.NORMAL,
        )

        header = MessageHeader(
            version=header_data["version"],
            message_id=header_data["message_id"],
            correlation_id=header_data.get("correlation_id"),
            timestamp=header_data["timestamp"],
            source=source_info,
            target=target_info,
            message_type=MessageType(header_data["routing"]["message_type"]),
            priority=MessagePriority(header_data["routing"]["priority"]),
            ttl=header_data["routing"]["ttl"],
            delivery_mode=header_data["routing"]["delivery_mode"],
        )

        payload = MessagePayload(
            method=payload_data["method"],
            params=payload_data["params"],
            data=payload_data.get("data"),
            context=payload_data.get("context"),
        )

        return A2AMessage(header=header, payload=payload, metadata=data.get("metadata"))

    async def get_metrics(self) -> Dict[str, Any]:
        """メトリクス取得"""
        return {
            "agent_id": self.agent_info.agent_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "errors_count": self.errors_count,
            "pending_responses": len(self.response_waiters),
            "uptime": time.time(),  # 簡略化
        }


# Agent registry for discovery
AGENT_REGISTRY = {
    "knowledge_sage": AgentInfo(
        agent_id="knowledge_sage",
        agent_type=AgentType.FOUR_SAGES,
        instance_id="ks-001",
        capabilities=["knowledge_query", "pattern_analysis", "learning_coordination"],
        endpoints=["query", "update", "analyze"],
        priority=MessagePriority.HIGH,
    ),
    "task_sage": AgentInfo(
        agent_id="task_sage",
        agent_type=AgentType.FOUR_SAGES,
        instance_id="ts-001",
        capabilities=["task_management", "resource_allocation", "scheduling"],
        endpoints=["assign", "status", "optimize"],
        priority=MessagePriority.HIGH,
    ),
    "rag_sage": AgentInfo(
        agent_id="rag_sage",
        agent_type=AgentType.FOUR_SAGES,
        instance_id="rs-001",
        capabilities=["document_retrieval", "context_enhancement", "semantic_search"],
        endpoints=["search", "enhance", "index"],
        priority=MessagePriority.HIGH,
    ),
    "incident_sage": AgentInfo(
        agent_id="incident_sage",
        agent_type=AgentType.FOUR_SAGES,
        instance_id="is-001",
        capabilities=["anomaly_detection", "risk_assessment", "recovery_planning"],
        endpoints=["detect", "assess", "recover"],
        priority=MessagePriority.CRITICAL,
    ),
}


async def create_a2a_client(agent_id: str) -> A2AClient:
    """A2Aクライアント作成ヘルパー"""
    if agent_id not in AGENT_REGISTRY:
        raise A2AError(
            A2AErrorCode.AGENT_NOT_FOUND, f"Agent {agent_id} not found in registry"
        )

    agent_info = AGENT_REGISTRY[agent_id]
    client = A2AClient(agent_info)
    await client.connect()
    return client


if __name__ == "__main__":
    # テスト実行
    async def test_a2a():
        try:
            # Knowledge Sageクライアント作成
            knowledge_client = await create_a2a_client("knowledge_sage")

            # Task Sageクライアント作成
            task_client = await create_a2a_client("task_sage")

            # Task Sageにハンドラー登録
            async def handle_knowledge_query(message: A2AMessage):
                print(f"Task Sage received query: {message.payload.params}")
                return {"status": "processed", "result": "sample data"}

            task_client.register_handler(
                MessageType.KNOWLEDGE_QUERY, handle_knowledge_query
            )

            # Knowledge SageからTask Sageに問い合わせ
            response = await knowledge_client.send_message(
                target_agent="task_sage",
                message_type=MessageType.KNOWLEDGE_QUERY,
                method="query_task_history",
                params={"agent_id": "task_sage", "days": 7},
                wait_for_response=True,
                timeout=10.0,
            )

            print(f"Response: {response.payload.data}")

            # メトリクス表示
            print(f"Knowledge metrics: {await knowledge_client.get_metrics()}")
            print(f"Task metrics: {await task_client.get_metrics()}")

            # 切断
            await knowledge_client.disconnect()
            await task_client.disconnect()

        except Exception as e:
            print(f"Test error: {e}")

    # テスト実行
    asyncio.run(test_a2a())

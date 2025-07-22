#!/usr/bin/env python3
"""
Elder Tree A2A (Application-to-Application) Communication Protocol
魂間通信のプロトコル定義と基本実装
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from uuid import uuid4

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """メッセージタイプ"""
    REQUEST = "request"      # リクエスト（応答期待）
    RESPONSE = "response"    # レスポンス
    COMMAND = "command"      # コマンド（応答不要）
    EVENT = "event"          # イベント通知
    QUERY = "query"          # クエリ（データ取得）
    ERROR = "error"          # エラー


class MessagePriority(Enum):
    """メッセージ優先度"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class A2AMessage:
    """A2A通信メッセージ"""
    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender: str = ""
    recipient: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None  # 関連メッセージのID
    reply_to: Optional[str] = None  # 返信先（キュー名など）
    timeout: Optional[float] = 30.0  # タイムアウト（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "timeout": self.timeout
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """辞書から生成"""
        return cls(
            message_id=data.get("message_id", str(uuid4())),
            message_type=MessageType(data.get("message_type", "request")),
            sender=data.get("sender", ""),
            recipient=data.get("recipient", ""),
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", 1)),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            timeout=data.get("timeout", 30.0)
        )
        
    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict())
        
    @classmethod
    def from_json(cls, json_str: str) -> "A2AMessage":
        """JSONから生成"""
        return cls.from_dict(json.loads(json_str))


class A2ACommunicator(ABC):
    """A2A通信の抽象基底クラス"""
    
    def __init__(self, soul_name: str):
        self.soul_name = soul_name
        self._message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        self._pending_responses: Dict[str, asyncio.Future] = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """通信接続を確立"""
        pass
        
    @abstractmethod
    async def disconnect(self):
        """通信接続を切断"""
        pass
        
    @abstractmethod
    async def send_message(self, message: A2AMessage) -> bool:
        """メッセージ送信"""
        pass
        
    @abstractmethod
    async def receive_message(self) -> Optional[A2AMessage]:
        """メッセージ受信"""
        pass
        
    async def request(self, recipient: str, payload: Dict[str, Any], 
                     timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        リクエスト送信（応答待機）
        
        Args:
            recipient: 送信先
            payload: ペイロード
            timeout: タイムアウト（秒）
            
        Returns:
            応答ペイロード
        """
        message = A2AMessage(
            message_type=MessageType.REQUEST,
            sender=self.soul_name,
            recipient=recipient,
            payload=payload,
            timeout=timeout or 30.0
        )
        
        # 応答待機用のFutureを作成
        future = asyncio.Future()
        self._pending_responses[message.message_id] = future
        
        # メッセージ送信
        success = await self.send_message(message)
        
        if not success:
            self._pending_responses.pop(message.message_id, None)
            return None
            
        try:
            # 応答待機
            response = await asyncio.wait_for(future, timeout=message.timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {message.message_id}")
            return None
            
        finally:
            self._pending_responses.pop(message.message_id, None)
            
    async def command(self, recipient: str, payload: Dict[str, Any]) -> bool:
        """
        コマンド送信（応答不要）
        
        Args:
            recipient: 送信先
            payload: ペイロード
            
        Returns:
            送信成功時True
        """
        message = A2AMessage(
            message_type=MessageType.COMMAND,
            sender=self.soul_name,
            recipient=recipient,
            payload=payload
        )
        
        return await self.send_message(message)
        
    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        イベントブロードキャスト
        
        Args:
            event_type: イベントタイプ
            event_data: イベントデータ
            
        Returns:
            送信成功時True
        """
        message = A2AMessage(
            message_type=MessageType.EVENT,
            sender=self.soul_name,
            recipient="*",  # ブロードキャスト
            payload={
                "event_type": event_type,
                "event_data": event_data
            }
        )
        
        return await self.send_message(message)
        
    def register_handler(self, message_type: MessageType, handler: Callable):
        """メッセージハンドラーの登録"""
        self._message_handlers[message_type].append(handler)
        
    async def process_incoming_message(self, message: A2AMessage):
        """受信メッセージの処理"""
        # 応答メッセージの場合
        if message.message_type == MessageType.RESPONSE and message.correlation_id:
            future = self._pending_responses.get(message.correlation_id)
            if future and not future.done():
                future.set_result(message.payload)
                return
                
        # ハンドラー実行
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}", exc_info=True)


class LocalA2ACommunicator(A2ACommunicator):
    """
    ローカルメモリベースのA2A通信実装（開発・テスト用）
    """
    
    # クラス変数：全インスタンスで共有
    _message_queues: Dict[str, asyncio.Queue] = {}
    _connected_souls: Dict[str, "LocalA2ACommunicator"] = {}
    
    def __init__(self, soul_name: str):
        super().__init__(soul_name)
        self._receive_queue = asyncio.Queue()
        self._connected = False
        
    async def connect(self) -> bool:
        """通信接続を確立"""
        if self._connected:
            return True
            
        # キューを登録
        self._message_queues[self.soul_name] = self._receive_queue
        self._connected_souls[self.soul_name] = self
        self._connected = True
        
        logger.info(f"LocalA2ACommunicator connected: {self.soul_name}")
        return True
        
    async def disconnect(self):
        """通信接続を切断"""
        if not self._connected:
            return
            
        # キューを削除
        self._message_queues.pop(self.soul_name, None)
        self._connected_souls.pop(self.soul_name, None)
        self._connected = False
        
        logger.info(f"LocalA2ACommunicator disconnected: {self.soul_name}")
        
    async def send_message(self, message: A2AMessage) -> bool:
        """メッセージ送信"""
        if not self._connected:
            logger.error(f"Not connected: {self.soul_name}")
            return False
            
        # 宛先のキューを取得
        if message.recipient == "*":
            # ブロードキャスト
            for soul_name, queue in self._message_queues.items():
                if soul_name != self.soul_name:
                    await queue.put(message)
        else:
            # ユニキャスト
            target_queue = self._message_queues.get(message.recipient)
            if target_queue:
                await target_queue.put(message)
            else:
                logger.warning(f"Recipient not found: {message.recipient}")
                return False
                
        return True
        
    async def receive_message(self) -> Optional[A2AMessage]:
        """メッセージ受信"""
        if not self._connected:
            return None
            
        try:
            message = await asyncio.wait_for(self._receive_queue.get(), timeout=1.0)
            return message
        except asyncio.TimeoutError:
            return None
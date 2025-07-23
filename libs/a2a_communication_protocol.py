#!/usr/bin/env python3
"""
🌟 A2A Communication Protocol - Agent-to-Agent通信プロトコル
=============================================================

Elder/Servant魂間のAgent-to-Agent通信を実現するプロトコル実装。
真のマルチプロセス分散通信とメッセージルーティングシステム。

Author: Claude Elder
Created: 2025-01-19
"""

import asyncio
import json
import logging
import multiprocessing as mp
import os
import signal
import socket
import sys
import threading
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lightweight_logger import get_logger
from souls.base_soul import ElderType, SoulIdentity, SoulRequest, SoulResponse

logger = get_logger("a2a_protocol")


class MessageType(Enum):
    """メッセージタイプ"""

    REQUEST = "request"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"
    DISCOVERY_RESPONSE = "discovery_response"
    COLLABORATION_INVITE = "collaboration_invite"
    COLLABORATION_ACCEPT = "collaboration_accept"
    COLLABORATION_REJECT = "collaboration_reject"
    COLLABORATION_END = "collaboration_end"
    BROADCAST = "broadcast"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class CommunicationChannel(Enum):
    """通信チャネル"""

    DIRECT = "direct"  # 1対1直接通信
    BROADCAST = "broadcast"  # 1対多ブロードキャスト
    MULTICAST = "multicast"  # グループ通信
    HIERARCHY = "hierarchy"  # 階層通信（上位・下位）
    COLLABORATION = "collaboration"  # 協調作業チャネル


class MessagePriority(Enum):
    """メッセージ優先度"""

    EMERGENCY = 1  # 緊急（即座に処理）
    HIGH = 2  # 高（優先処理）
    NORMAL = 3  # 通常
    LOW = 4  # 低（余裕がある時に処理）
    BACKGROUND = 5  # バックグラウンド


@dataclass
class A2AMessage:
    """A2A通信メッセージ"""

    message_id: str
    message_type: MessageType
    sender_soul_id: str
    sender_process_id: int
    target_soul_id: Optional[str] = None
    target_group: Optional[str] = None
    channel: CommunicationChannel = CommunicationChannel.DIRECT
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    requires_response: bool = False
    correlation_id: Optional[str] = None
    ttl_seconds: int = 300  # Time To Live (5分)
    created_at: datetime = field(default_factory=datetime.now)
    hop_count: int = 0  # メッセージの転送回数
    routing_path: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["channel"] = self.channel.value
        data["priority"] = self.priority.value
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """辞書から復元"""
        data["message_type"] = MessageType(data["message_type"])
        data["channel"] = CommunicationChannel(data["channel"])
        data["priority"] = MessagePriority(data["priority"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def is_expired(self) -> bool:
        """TTL期限切れチェック"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)

    def add_hop(self, soul_id: str):
        """ホップを追加"""
        self.hop_count += 1
        self.routing_path.append(soul_id)


@dataclass
class SoulNode:
    """魂ノード情報"""

    soul_id: str
    identity: SoulIdentity
    process_id: int
    host: str = "localhost"
    port: int = 0
    status: str = "active"
    last_heartbeat: datetime = field(default_factory=datetime.now)
    capabilities: List[str] = field(default_factory=list)
    current_load: float = 0.0  # 0.0-1.0の負荷率
    collaboration_count: int = 0


class MessageRouter:
    """メッセージルーター"""

    def __init__(self):
        self.routing_table: Dict[str, SoulNode] = {}
        self.groups: Dict[str, Set[str]] = {}
        self.message_cache: Dict[str, A2AMessage] = {}
        self.routing_lock = threading.RLock()
        self.logger = get_logger("message_router")

        # デフォルトグループ設定
        self._setup_default_groups()

    def _setup_default_groups(self):
        """デフォルトグループの設定"""
        self.groups.update(
            {
                "elders": set(),
                "sages": set(),
                "servants": set(),
                "knights": set(),
                "all": set(),
            }
        )

    def register_soul(self, node: SoulNode):
        """魂ノードの登録"""
        with self.routing_lock:
            self.routing_table[node.soul_id] = node

            # グループ自動追加
            self.groups["all"].add(node.soul_id)

            if node.identity.elder_type == ElderType.SAGE:
                self.groups["sages"].add(node.soul_id)
            elif node.identity.elder_type == ElderType.SERVANT:
                self.groups["servants"].add(node.soul_id)
            elif node.identity.elder_type == ElderType.KNIGHT:
                self.groups["knights"].add(node.soul_id)
            elif node.identity.elder_type in [
                ElderType.GRAND_ELDER,
                ElderType.CLAUDE_ELDER,
                ElderType.ANCIENT_ELDER,
            ]:
                self.groups["elders"].add(node.soul_id)

        self.logger.info(
            f"🔗 Soul node registered: {node.soul_id} ({node.identity.elder_type.value})"
        )

    def unregister_soul(self, soul_id: str):
        """魂ノードの登録解除"""
        with self.routing_lock:
            if soul_id in self.routing_table:
                del self.routing_table[soul_id]

                # 全グループから削除
                for group_souls in self.groups.values():
                    group_souls.discard(soul_id)

        self.logger.info(f"🔗 Soul node unregistered: {soul_id}")

    def find_route(self, target_soul_id: str) -> Optional[SoulNode]:
        """ターゲット魂への経路探索"""
        with self.routing_lock:
            return self.routing_table.get(target_soul_id)

    def find_group_members(self, group_name: str) -> Set[str]:
        """グループメンバーの取得"""
        with self.routing_lock:
            return self.groups.get(group_name, set()).copy()

    def find_best_soul_for_capability(
        self, capability: str, exclude: Set[str] = None
    ) -> Optional[str]:
        """能力に基づく最適魂の探索"""
        exclude = exclude or set()

        with self.routing_lock:
            candidates = []
            for soul_id, node in self.routing_table.items():
                if soul_id in exclude:
                    continue
                if capability in node.capabilities:
                    candidates.append((soul_id, node.current_load))

            if not candidates:
                return None

            # 負荷が最も低い魂を選択
            return min(candidates, key=lambda x: x[1])[0]

    def update_soul_status(self, soul_id: str, status: str, load: float = None):
        """魂ステータスの更新"""
        with self.routing_lock:
            if soul_id in self.routing_table:
                node = self.routing_table[soul_id]
                node.status = status
                node.last_heartbeat = datetime.now()
                if load is not None:
                    node.current_load = max(0.0, min(1.0, load))

    def cleanup_stale_nodes(self, timeout_seconds: int = 300):
        """古いノードのクリーンアップ"""
        now = datetime.now()
        stale_souls = []

        with self.routing_lock:
            for soul_id, node in self.routing_table.items():
                if (now - node.last_heartbeat).total_seconds() > timeout_seconds:
                    stale_souls.append(soul_id)

        for soul_id in stale_souls:
            self.unregister_soul(soul_id)
            self.logger.warning(f"🧹 Cleaned up stale soul node: {soul_id}")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """ルーティング統計の取得"""
        with self.routing_lock:
            group_stats = {name: len(members) for name, members in self.groups.items()}

            load_stats = []
            for node in self.routing_table.values():
                load_stats.append(node.current_load)

            avg_load = sum(load_stats) / len(load_stats) if load_stats else 0.0

            return {
                "total_souls": len(self.routing_table),
                "groups": group_stats,
                "average_load": avg_load,
                "active_souls": len(
                    [n for n in self.routing_table.values() if n.status == "active"]
                ),
                "cached_messages": len(self.message_cache),
            }


class A2ACommunicationProtocol:
    """A2A通信プロトコル"""

    def __init__(self, soul_identity: SoulIdentity, port: int = 0):
        self.soul_identity = soul_identity
        self.process_id = os.getpid()
        self.router = MessageRouter()
        self.message_queue = mp.Queue()
        self.response_queue = mp.Queue()
        self.running = mp.Value("b", False)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = get_logger(f"a2a_protocol_{soul_identity.soul_id}")

        # TCP通信設定
        self.host = "localhost"
        self.port = port or self._find_free_port()
        self.server_socket: Optional[socket.socket] = None
        self.client_connections: Dict[str, socket.socket] = {}

        # メッセージハンドラー
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.REQUEST: self._handle_request,
            MessageType.RESPONSE: self._handle_response,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.DISCOVERY: self._handle_discovery,
            MessageType.DISCOVERY_RESPONSE: self._handle_discovery_response,
            MessageType.COLLABORATION_INVITE: self._handle_collaboration_invite,
            MessageType.COLLABORATION_ACCEPT: self._handle_collaboration_accept,
            MessageType.COLLABORATION_REJECT: self._handle_collaboration_reject,
            MessageType.COLLABORATION_END: self._handle_collaboration_end,
            MessageType.BROADCAST: self._handle_broadcast,
            MessageType.ERROR: self._handle_error,
            MessageType.SHUTDOWN: self._handle_shutdown,
        }

        # 統計情報
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "connections_established": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

        # 自身をルーターに登録
        self_node = SoulNode(
            soul_id=soul_identity.soul_id,
            identity=soul_identity,
            process_id=self.process_id,
            host=self.host,
            port=self.port,
            capabilities=[cap.value for cap in soul_identity.capabilities],
        )
        self.router.register_soul(self_node)

    def _find_free_port(self) -> int:
        """空いているポートを見つける"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    async def start_protocol(self) -> bool:
        """プロトコル開始"""
        try:
            self.running.value = True

            # TCPサーバー開始
            await self._start_tcp_server()

            # メッセージ処理ループ開始
            asyncio.create_task(self._message_processing_loop())

            # ハートビート送信開始
            asyncio.create_task(self._heartbeat_loop())

            # ネットワーク探索開始
            asyncio.create_task(self._discovery_loop())

            self.logger.info(
                f"🌟 A2A Protocol started for {self.soul_identity.soul_id} on {self.host}:" \
                    "{self.port}"
            )
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start A2A protocol: {e}")
            return False

    async def stop_protocol(self):
        """プロトコル停止"""
        self.running.value = False

        # シャットダウンメッセージをブロードキャスト
        await self.broadcast_message(
            MessageType.SHUTDOWN,
            {"soul_id": self.soul_identity.soul_id, "reason": "normal_shutdown"},
        )

        # 接続をクローズ
        for conn in self.client_connections.values():
            try:
                conn.close()
            except:
                pass

        if self.server_socket:
            self.server_socket.close()

        self.executor.shutdown(wait=True)
        self.router.unregister_soul(self.soul_identity.soul_id)

        self.logger.info(f"🌅 A2A Protocol stopped for {self.soul_identity.soul_id}")

    async def _start_tcp_server(self):
        """TCPサーバー開始"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)

        # ノンブロッキングモードに設定
        self.server_socket.setblocking(False)

        self.logger.info(f"🔗 TCP server listening on {self.host}:{self.port}")

        # 接続受付ループ
        asyncio.create_task(self._accept_connections())

    async def _accept_connections(self):
        """接続受付ループ"""
        while self.running.value:
            try:
                # ノンブロッキング接続受付
                try:
                    conn, addr = self.server_socket.accept()
                    self.stats["connections_established"] += 1
                    asyncio.create_task(self._handle_connection(conn, addr))
                except BlockingIOError:
                    # 接続がない場合は短時間待機
                    await asyncio.sleep(0.1)
                    continue

            except Exception as e:
                if self.running.value:
                    self.logger.error(f"❌ Error accepting connections: {e}")
                await asyncio.sleep(1.0)

    async def _handle_connection(self, conn: socket.socket, addr: Tuple[str, int]):
        """接続ハンドリング"""
        try:
            conn.setblocking(False)
            buffer = b""

            while self.running.value:
                try:
                    # データ受信
                    data = conn.recv(4096)
                    if not data:
                        break

                    buffer += data
                    self.stats["bytes_received"] += len(data)

                    # メッセージ境界の検出（JSON改行区切り）
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if line:
                            await self._process_received_message(line.decode("utf-8"))

                except BlockingIOError:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    self.logger.error(f"❌ Connection handling error: {e}")
                    break

        except Exception as e:
            self.logger.error(f"❌ Connection error from {addr}: {e}")
        finally:
            conn.close()

    async def _process_received_message(self, message_data: str):
        """受信メッセージの処理"""
        try:
            message_dict = json.loads(message_data)
            message = A2AMessage.from_dict(message_dict)

            self.stats["messages_received"] += 1

            # TTL期限切れチェック
            if message.is_expired():
                self.logger.warning(f"⏰ Message expired: {message.message_id}")
                return

            # ハンドラー実行
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                self.logger.warning(
                    f"⚠️ No handler for message type: {message.message_type}"
                )

        except Exception as e:
            self.logger.error(f"❌ Error processing received message: {e}")
            self.stats["errors"] += 1

    async def send_message(self, message: A2AMessage) -> bool:
        """メッセージ送信"""
        try:
            # ルーティング
            if message.channel == CommunicationChannel.DIRECT:
                return await self._send_direct_message(message)
            elif message.channel == CommunicationChannel.BROADCAST:
                return await self._send_broadcast_message(message)
            elif message.channel == CommunicationChannel.MULTICAST:
                return await self._send_multicast_message(message)
            else:
                self.logger.error(f"❌ Unsupported channel: {message.channel}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error sending message: {e}")
            self.stats["errors"] += 1
            return False

    async def _send_direct_message(self, message: A2AMessage) -> bool:
        """直接メッセージ送信"""
        if not message.target_soul_id:
            return False

        target_node = self.router.find_route(message.target_soul_id)
        if not target_node:
            self.logger.warning(f"⚠️ Target soul not found: {message.target_soul_id}")
            return False

        return await self._send_to_node(message, target_node)

    async def _send_broadcast_message(self, message: A2AMessage) -> bool:
        """ブロードキャストメッセージ送信"""
        success_count = 0
        total_count = 0

        for soul_id, node in self.router.routing_table.items():
            if soul_id == self.soul_identity.soul_id:
                continue  # 自分自身には送信しない

            total_count += 1
            if await self._send_to_node(message, node):
                success_count += 1

        self.logger.info(f"📡 Broadcast sent to {success_count}/{total_count} souls")
        return success_count > 0

    async def _send_multicast_message(self, message: A2AMessage) -> bool:
        """マルチキャストメッセージ送信"""
        if not message.target_group:
            return False

        group_members = self.router.find_group_members(message.target_group)
        success_count = 0

        for soul_id in group_members:
            if soul_id == self.soul_identity.soul_id:
                continue

            target_node = self.router.find_route(soul_id)
            if target_node and await self._send_to_node(message, target_node):
                success_count += 1

        self.logger.info(
            f"📡 Multicast sent to {success_count}/{len(group_members)} souls in group " \
                "{message.target_group}"
        )
        return success_count > 0

    async def _send_to_node(self, message: A2AMessage, node: SoulNode) -> bool:
        """特定ノードへの送信"""
        try:
            # 接続を取得または作成
            conn = await self._get_connection(node)
            if not conn:
                return False

            # メッセージをJSONとして送信
            message_data = json.dumps(message.to_dict()) + "\n"
            message_bytes = message_data.encode("utf-8")

            conn.send(message_bytes)
            self.stats["messages_sent"] += 1
            self.stats["bytes_sent"] += len(message_bytes)

            return True

        except Exception as e:
            self.logger.error(f"❌ Error sending to node {node.soul_id}: {e}")
            # 接続エラーの場合は接続を削除
            connection_key = f"{node.host}:{node.port}"
            if connection_key in self.client_connections:
                del self.client_connections[connection_key]
            return False

    async def _get_connection(self, node: SoulNode) -> Optional[socket.socket]:
        """ノードへの接続を取得"""
        connection_key = f"{node.host}:{node.port}"

        if connection_key in self.client_connections:
            return self.client_connections[connection_key]

        try:
            # 新しい接続を作成
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((node.host, node.port))
            conn.setblocking(False)

            self.client_connections[connection_key] = conn
            return conn

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to {connection_key}: {e}")
            return None

    async def _message_processing_loop(self):
        """メッセージ処理ループ"""
        while self.running.value:
            try:
                # メッセージキューからメッセージを取得
                if not self.message_queue.empty():
                    message = self.message_queue.get_nowait()
                    await self.send_message(message)

                await asyncio.sleep(0.01)

            except Exception as e:
                self.logger.error(f"❌ Message processing loop error: {e}")
                await asyncio.sleep(1.0)

    async def _heartbeat_loop(self):
        """ハートビート送信ループ"""
        while self.running.value:
            try:
                # ハートビートメッセージをブロードキャスト
                heartbeat_message = A2AMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.HEARTBEAT,
                    sender_soul_id=self.soul_identity.soul_id,
                    sender_process_id=self.process_id,
                    channel=CommunicationChannel.BROADCAST,
                    payload={
                        "timestamp": datetime.now().isoformat(),
                        "load": self.router.routing_table[
                            self.soul_identity.soul_id
                        ].current_load,
                        "status": "active",
                    },
                )

                await self._send_broadcast_message(heartbeat_message)

                # 古いノードのクリーンアップ
                self.router.cleanup_stale_nodes()

                await asyncio.sleep(30)  # 30秒間隔

            except Exception as e:
                self.logger.error(f"❌ Heartbeat loop error: {e}")
                await asyncio.sleep(30)

    async def _discovery_loop(self):
        """ネットワーク探索ループ"""
        while self.running.value:
            try:
                # 探索メッセージをブロードキャスト
                discovery_message = A2AMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.DISCOVERY,
                    sender_soul_id=self.soul_identity.soul_id,
                    sender_process_id=self.process_id,
                    channel=CommunicationChannel.BROADCAST,
                    payload={
                        "requesting_soul": self.soul_identity.soul_id,
                        "elder_type": self.soul_identity.elder_type.value,
                        "capabilities": [
                            cap.value for cap in self.soul_identity.capabilities
                        ],
                    },
                )

                await self._send_broadcast_message(discovery_message)

                await asyncio.sleep(120)  # 2分間隔

            except Exception as e:
                self.logger.error(f"❌ Discovery loop error: {e}")
                await asyncio.sleep(120)

    # === メッセージハンドラー ===

    async def _handle_request(self, message: A2AMessage):
        """リクエストハンドラー"""
        self.logger.info(
            f"📨 Received request from {message.sender_soul_id}: {message.payload.get(
                'type',
                'unknown'
            )}"
        )

        # リクエストに対するレスポンス（実装は各魂で行う）
        if message.requires_response:
            response = A2AMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.RESPONSE,
                sender_soul_id=self.soul_identity.soul_id,
                sender_process_id=self.process_id,
                target_soul_id=message.sender_soul_id,
                correlation_id=message.message_id,
                payload={"status": "received", "message": "Request acknowledged"},
            )

            await self.send_message(response)

    async def _handle_response(self, message: A2AMessage):
        """レスポンスハンドラー"""
        self.logger.info(f"📬 Received response from {message.sender_soul_id}")
        # レスポンスキューに追加
        self.response_queue.put(message)

    async def _handle_heartbeat(self, message: A2AMessage):
        """ハートビートハンドラー"""
        # 送信者の状態を更新
        payload = message.payload
        self.router.update_soul_status(
            message.sender_soul_id,
            payload.get("status", "unknown"),
            payload.get("load", 0.0),
        )

    async def _handle_discovery(self, message: A2AMessage):
        """探索ハンドラー"""
        # 探索レスポンスを送信
        response = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.DISCOVERY_RESPONSE,
            sender_soul_id=self.soul_identity.soul_id,
            sender_process_id=self.process_id,
            target_soul_id=message.sender_soul_id,
            payload={
                "soul_id": self.soul_identity.soul_id,
                "elder_type": self.soul_identity.elder_type.value,
                "capabilities": [cap.value for cap in self.soul_identity.capabilities],
                "host": self.host,
                "port": self.port,
                "status": "active",
            },
        )

        await self.send_message(response)

    async def _handle_discovery_response(self, message: A2AMessage):
        """探索レスポンスハンドラー"""
        payload = message.payload

        # 新しい魂ノードを登録
        try:
            # SoulIdentityを再構築
            identity = SoulIdentity(
                soul_id=payload["soul_id"],
                soul_name=payload["soul_id"],
                elder_type=ElderType(payload["elder_type"]),
                hierarchy_level=5,
                capabilities=[],  # 簡略化
            )

            node = SoulNode(
                soul_id=payload["soul_id"],
                identity=identity,
                process_id=message.sender_process_id,
                host=payload.get("host", "localhost"),
                port=payload.get("port", 0),
                status=payload.get("status", "active"),
                capabilities=payload.get("capabilities", []),
            )

            self.router.register_soul(node)

        except Exception as e:
            self.logger.error(f"❌ Error processing discovery response: {e}")

    async def _handle_collaboration_invite(self, message: A2AMessage):
        """協調招待ハンドラー"""
        self.logger.info(f"🤝 Collaboration invite from {message.sender_soul_id}")
        # デフォルトでは受諾（実装は各魂で決定）

        response = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.COLLABORATION_ACCEPT,
            sender_soul_id=self.soul_identity.soul_id,
            sender_process_id=self.process_id,
            target_soul_id=message.sender_soul_id,
            payload={"collaboration_id": message.payload.get("collaboration_id")},
        )

        await self.send_message(response)

    async def _handle_collaboration_accept(self, message: A2AMessage):
        """協調受諾ハンドラー"""
        self.logger.info(f"✅ Collaboration accepted by {message.sender_soul_id}")

    async def _handle_collaboration_reject(self, message: A2AMessage):
        """協調拒否ハンドラー"""
        self.logger.info(f"❌ Collaboration rejected by {message.sender_soul_id}")

    async def _handle_collaboration_end(self, message: A2AMessage):
        """協調終了ハンドラー"""
        self.logger.info(f"🏁 Collaboration ended with {message.sender_soul_id}")

    async def _handle_broadcast(self, message: A2AMessage):
        """ブロードキャストハンドラー"""
        self.logger.info(
            f"📡 Broadcast from {message.sender_soul_id}: {message.payload.get('announcement', '')}"
        )

    async def _handle_error(self, message: A2AMessage):
        """エラーハンドラー"""
        self.logger.error(
            f"💥 Error from {message.sender_soul_id}: {message.payload.get(
                'error',
                'Unknown error'
            )}"
        )

    async def _handle_shutdown(self, message: A2AMessage):
        """シャットダウンハンドラー"""
        self.logger.info(f"🌅 Shutdown notice from {message.sender_soul_id}")
        # 送信者をルーティングテーブルから削除
        self.router.unregister_soul(message.sender_soul_id)

    # === 公開API ===

    async def send_request(
        self,
        target_soul_id: str,
        request_type: str,
        payload: Dict[str, Any],
        requires_response: bool = True,
    ) -> Optional[A2AMessage]:
        """リクエスト送信"""
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.REQUEST,
            sender_soul_id=self.soul_identity.soul_id,
            sender_process_id=self.process_id,
            target_soul_id=target_soul_id,
            requires_response=requires_response,
            payload={"type": request_type, **payload},
        )

        if await self.send_message(message):
            if requires_response:
                # レスポンス待機
                timeout = 30.0
                start_time = time.time()

                while time.time() - start_time < timeout:
                    if not self.response_queue.empty():
                        response = self.response_queue.get_nowait()
                        if response.correlation_id == message.message_id:
                            return response
                    await asyncio.sleep(0.1)

                self.logger.warning(
                    f"⏰ Response timeout for message {message.message_id}"
                )
            return message

        return None

    async def broadcast_message(
        self, message_type: MessageType, payload: Dict[str, Any]
    ):
        """ブロードキャストメッセージ送信"""
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_soul_id=self.soul_identity.soul_id,
            sender_process_id=self.process_id,
            channel=CommunicationChannel.BROADCAST,
            payload=payload,
        )

        return await self.send_message(message)

    async def send_to_group(
        self, group_name: str, message_type: MessageType, payload: Dict[str, Any]
    ):
        """グループメッセージ送信"""
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_soul_id=self.soul_identity.soul_id,
            sender_process_id=self.process_id,
            target_group=group_name,
            channel=CommunicationChannel.MULTICAST,
            payload=payload,
        )

        return await self.send_message(message)

    def get_protocol_status(self) -> Dict[str, Any]:
        """プロトコル状態取得"""
        routing_stats = self.router.get_routing_statistics()

        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "soul_id": self.soul_identity.soul_id,
            "process_id": self.process_id,
            "host": self.host,
            "port": self.port,
            "running": self.running.value,
            "uptime_seconds": uptime,
            "statistics": self.stats.copy(),
            "routing": routing_stats,
            "connections": len(self.client_connections),
        }


# === ユーティリティ関数 ===


async def create_a2a_protocol(
    soul_identity: SoulIdentity, port: int = 0
) -> A2ACommunicationProtocol:
    """A2A通信プロトコルの作成"""
    protocol = A2ACommunicationProtocol(soul_identity, port)

    if await protocol.start_protocol():
        return protocol
    else:
        raise RuntimeError(f"Failed to start A2A protocol for {soul_identity.soul_id}")


async def test_a2a_communication():
    """A2A通信のテスト"""
    from souls.base_soul import SoulCapability, create_soul_identity

    # テスト用アイデンティティ
    identity1 = create_soul_identity(
        "Test Soul 1",
        ElderType.CLAUDE_ELDER,
        [SoulCapability.LEADERSHIP, SoulCapability.COMMUNICATION],
    )

    identity2 = create_soul_identity(
        "Test Soul 2", ElderType.SAGE, [SoulCapability.WISDOM, SoulCapability.ANALYSIS]
    )

    # プロトコル作成
    protocol1 = await create_a2a_protocol(identity1, 9001)
    protocol2 = await create_a2a_protocol(identity2, 9002)

    # 少し待機してネットワーク探索を行う
    await asyncio.sleep(2)

    # メッセージ送信テスト
    response = await protocol1.send_request(
        identity2.soul_id, "test_request", {"message": "Hello from Claude Elder!"}
    )

    if response:
        print(f"✅ A2A Communication test successful!")
        print(f"   Response: {response.payload}")
    else:
        print(f"❌ A2A Communication test failed!")

    # プロトコル停止
    await protocol1.stop_protocol()
    await protocol2.stop_protocol()


if __name__ == "__main__":
    print("🌟 A2A Communication Protocol - Agent-to-Agent通信プロトコル")
    print("Test mode:")
    asyncio.run(test_a2a_communication())

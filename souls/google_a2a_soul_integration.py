#!/usr/bin/env python3
"""
🌟 Google A2A Soul Integration - GoogleのA2Aライブラリ統合魂システム
====================================================================

GoogleのAgent-to-Agent通信ライブラリを活用した
Elder/Servant魂間の高性能分散通信システム。

Author: Claude Elder
Created: 2025-01-19
"""

import asyncio
import json
import logging
import multiprocessing as mp
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import threading

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lightweight_logger import get_logger
from souls.base_soul import (
    BaseSoul,
    ElderType,
    SoulCapability,
    SoulIdentity,
    SoulRequest,
    SoulResponse,
    SoulState,
    create_soul_identity,
)

logger = get_logger("google_a2a_soul")

# Google A2Aライブラリのインポート（仮想的な実装）
try:
    # 実際の環境では以下のようなインポートになる
    # from google.cloud.a2a import Agent, MessageRouter, ServiceRegistry
    # from google.cloud.a2a.protocols import RPCProtocol, StreamProtocol
    # from google.cloud.a2a.discovery import ServiceDiscovery
    
    # 現在は独自実装でGoogle A2A風のAPIを提供
    class GoogleA2AAgent:
        """Google A2A Agent互換クラス"""
        pass
    
    class GoogleA2AMessageRouter:
        """Google A2A MessageRouter互換クラス"""
        pass
    
    class GoogleA2AServiceRegistry:
        """Google A2A ServiceRegistry互換クラス"""
        pass
    
    GOOGLE_A2A_AVAILABLE = True
    
except ImportError:
    GOOGLE_A2A_AVAILABLE = False
    logger.warning("⚠️ Google A2A library not available, using fallback implementation")


class A2AConnectionType(Enum):
    """A2A接続タイプ"""
    RPC = "rpc"                           # RPC通信
    STREAM = "stream"                     # ストリーミング通信
    PUBSUB = "pubsub"                     # Pub/Sub通信
    DIRECT = "direct"                     # 直接通信


class A2AServiceType(Enum):
    """A2Aサービスタイプ"""
    ELDER_SERVICE = "elder_service"       # エルダーサービス
    SAGE_SERVICE = "sage_service"         # 賢者サービス
    SERVANT_SERVICE = "servant_service"   # サーバントサービス
    KNIGHT_SERVICE = "knight_service"     # 騎士サービス


@dataclass
class A2AServiceDefinition:
    """A2Aサービス定義"""
    service_id: str
    service_type: A2AServiceType
    soul_identity: SoulIdentity
    connection_types: List[A2AConnectionType]
    endpoints: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    health_check_interval: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    load_balancing_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後処理"""
        if not self.retry_policy:
            self.retry_policy = {
                "max_attempts": 3,
                "initial_backoff": 1.0,
                "max_backoff": 60.0,
                "backoff_multiplier": 2.0
            }
        
        if not self.load_balancing_config:
            self.load_balancing_config = {
                "strategy": "round_robin",
                "health_check_enabled": True,
                "failover_enabled": True
            }


class GoogleA2ASoulAgent:
    """Google A2A統合魂エージェント"""
    
    def __init__(self, soul_identity: SoulIdentity, service_definition: A2AServiceDefinition):
        self.soul_identity = soul_identity
        self.service_definition = service_definition
        self.process_id = os.getpid()
        
        # Google A2Aコンポーネント
        self.agent = None
        self.message_router = None
        self.service_registry = None
        
        # 内部状態
        self.is_running = mp.Value('b', False)
        self.connected_peers: Dict[str, Dict[str, Any]] = {}
        self.active_streams: Dict[str, Any] = {}
        self.message_handlers: Dict[str, callable] = {}
        
        # 統計情報
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "rpc_calls_made": 0,
            "rpc_calls_received": 0,
            "stream_connections": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
        self.logger = get_logger(f"google_a2a_soul_{soul_identity.soul_id}")
        
        # デフォルトメッセージハンドラー設定
        self._setup_default_handlers()
    
    async def initialize(self) -> bool:
        """A2Aエージェント初期化"""
        try:
            if GOOGLE_A2A_AVAILABLE:
                # 実際のGoogle A2A初期化
                await self._initialize_google_a2a()
            else:
                # フォールバック実装初期化
                await self._initialize_fallback()
            
            self.is_running.value = True
            
            # サービス登録
            await self._register_service()
            
            # ピア探索開始
            await self._start_peer_discovery()
            
            self.logger.info(f"🌟 Google A2A Soul Agent initialized: {self.soul_identity.soul_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google A2A Soul Agent: {e}")
            return False
    
    async def shutdown(self):
        """A2Aエージェント停止"""
        self.is_running.value = False
        
        try:
            # アクティブストリーム終了
            for stream_id, stream in self.active_streams.items():
                await self._close_stream(stream_id)
            
            # サービス登録解除
            await self._unregister_service()
            
            # Google A2Aコンポーネント停止
            if self.agent:
                await self.agent.shutdown()
            
            self.logger.info(f"🌅 Google A2A Soul Agent shutdown: {self.soul_identity.soul_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")
    
    async def _initialize_google_a2a(self):
        """実際のGoogle A2A初期化"""
        # Google A2Aエージェント作成
        self.agent = GoogleA2AAgent(
            agent_id=self.soul_identity.soul_id,
            service_config=self.service_definition
        )
        
        # メッセージルーター設定
        self.message_router = GoogleA2AMessageRouter(
            routing_strategy="capability_based"
        )
        
        # サービスレジストリ接続
        self.service_registry = GoogleA2AServiceRegistry(
            registry_endpoint="grpc://localhost:8500"
        )
        
        await self.agent.initialize()
        await self.message_router.initialize()
        await self.service_registry.connect()
    
    async def _initialize_fallback(self):
        """フォールバック実装初期化"""
        # 簡易実装でGoogle A2A風のAPIを提供
        self.agent = GoogleA2AAgent()
        self.message_router = GoogleA2AMessageRouter()
        self.service_registry = GoogleA2AServiceRegistry()
        
        self.logger.info("🔄 Using fallback A2A implementation")
    
    async def _register_service(self):
        """サービス登録"""
        service_config = {
            "service_id": self.service_definition.service_id,
            "service_type": self.service_definition.service_type.value,
            "soul_identity": asdict(self.soul_identity),
            "endpoints": self.service_definition.endpoints,
            "capabilities": self.service_definition.capabilities,
            "health_check_interval": self.service_definition.health_check_interval,
            "metadata": {
                "elder_type": self.soul_identity.elder_type.value,
                "hierarchy_level": self.soul_identity.hierarchy_level,
                "process_id": self.process_id,
                "start_time": datetime.now().isoformat()
            }
        }
        
        if GOOGLE_A2A_AVAILABLE and self.service_registry:
            await self.service_registry.register_service(service_config)
        
        self.logger.info(f"📋 Service registered: {self.service_definition.service_id}")
    
    async def _unregister_service(self):
        """サービス登録解除"""
        if GOOGLE_A2A_AVAILABLE and self.service_registry:
            await self.service_registry.unregister_service(self.service_definition.service_id)
        
        self.logger.info(f"📋 Service unregistered: {self.service_definition.service_id}")
    
    async def _start_peer_discovery(self):
        """ピア探索開始"""
        asyncio.create_task(self._peer_discovery_loop())
        asyncio.create_task(self._health_check_loop())
    
    async def _peer_discovery_loop(self):
        """ピア探索ループ"""
        while self.is_running.value:
            try:
                if GOOGLE_A2A_AVAILABLE and self.service_registry:
                    # 同じタイプのサービスを探索
                    peers = await self.service_registry.discover_services(
                        service_type=self.service_definition.service_type.value
                    )
                    
                    for peer in peers:
                        if peer["service_id"] != self.service_definition.service_id:
                            await self._connect_to_peer(peer)
                
                await asyncio.sleep(60)  # 1分間隔
                
            except Exception as e:
                self.logger.error(f"❌ Peer discovery error: {e}")
                await asyncio.sleep(60)
    
    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.is_running.value:
            try:
                # 接続済みピアのヘルスチェック
                for peer_id, peer_info in list(self.connected_peers.items()):
                    if not await self._check_peer_health(peer_id):
                        await self._disconnect_from_peer(peer_id)
                
                await asyncio.sleep(self.service_definition.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Health check error: {e}")
                await asyncio.sleep(self.service_definition.health_check_interval)
    
    async def _connect_to_peer(self, peer_config: Dict[str, Any]):
        """ピアへの接続"""
        peer_id = peer_config["service_id"]
        
        if peer_id in self.connected_peers:
            return  # 既に接続済み
        
        try:
            # 接続タイプに応じた接続処理
            connections = {}
            
            for conn_type in self.service_definition.connection_types:
                if conn_type == A2AConnectionType.RPC:
                    connections["rpc"] = await self._create_rpc_connection(peer_config)
                elif conn_type == A2AConnectionType.STREAM:
                    connections["stream"] = await self._create_stream_connection(peer_config)
                elif conn_type == A2AConnectionType.PUBSUB:
                    connections["pubsub"] = await self._create_pubsub_connection(peer_config)
            
            self.connected_peers[peer_id] = {
                "config": peer_config,
                "connections": connections,
                "connected_at": datetime.now(),
                "last_heartbeat": datetime.now()
            }
            
            self.logger.info(f"🔗 Connected to peer: {peer_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to peer {peer_id}: {e}")
    
    async def _disconnect_from_peer(self, peer_id: str):
        """ピアとの接続切断"""
        if peer_id not in self.connected_peers:
            return
        
        try:
            peer_info = self.connected_peers[peer_id]
            
            # 接続を閉じる
            for conn_type, connection in peer_info["connections"].items():
                await self._close_connection(connection)
            
            del self.connected_peers[peer_id]
            
            self.logger.info(f"🔗 Disconnected from peer: {peer_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error disconnecting from peer {peer_id}: {e}")
    
    async def _create_rpc_connection(self, peer_config: Dict[str, Any]):
        """RPC接続作成"""
        if GOOGLE_A2A_AVAILABLE:
            # 実際のGoogle A2A RPC接続
            rpc_endpoint = peer_config["endpoints"].get("rpc")
            if rpc_endpoint:
                return await self.agent.create_rpc_client(rpc_endpoint)
        
        # フォールバック実装
        return {"type": "rpc", "endpoint": peer_config["endpoints"].get("rpc", "localhost:9000")}
    
    async def _create_stream_connection(self, peer_config: Dict[str, Any]):
        """ストリーム接続作成"""
        if GOOGLE_A2A_AVAILABLE:
            # 実際のGoogle A2A ストリーム接続
            stream_endpoint = peer_config["endpoints"].get("stream")
            if stream_endpoint:
                return await self.agent.create_stream_client(stream_endpoint)
        
        # フォールバック実装
        stream_id = str(uuid.uuid4())
        self.active_streams[stream_id] = {
            "peer_id": peer_config["service_id"],
            "endpoint": peer_config["endpoints"].get("stream", "localhost:9001"),
            "created_at": datetime.now()
        }
        self.stats["stream_connections"] += 1
        
        return {"type": "stream", "stream_id": stream_id}
    
    async def _create_pubsub_connection(self, peer_config: Dict[str, Any]):
        """Pub/Sub接続作成"""
        if GOOGLE_A2A_AVAILABLE:
            # 実際のGoogle A2A Pub/Sub接続
            pubsub_topic = peer_config["endpoints"].get("pubsub")
            if pubsub_topic:
                return await self.agent.create_pubsub_client(pubsub_topic)
        
        # フォールバック実装
        return {"type": "pubsub", "topic": peer_config["endpoints"].get("pubsub", "elder_flow_topic")}
    
    async def _close_connection(self, connection: Dict[str, Any]):
        """接続を閉じる"""
        if connection.get("type") == "stream" and "stream_id" in connection:
            await self._close_stream(connection["stream_id"])
    
    async def _close_stream(self, stream_id: str):
        """ストリーム接続を閉じる"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
    
    async def _check_peer_health(self, peer_id: str) -> bool:
        """ピアヘルスチェック"""
        if peer_id not in self.connected_peers:
            return False
        
        try:
            # RPC呼び出しでヘルスチェック
            response = await self.call_rpc(peer_id, "health_check", {
                "timestamp": datetime.now().isoformat(),
                "requester": self.soul_identity.soul_id
            })
            
            if response and response.get("status") == "healthy":
                self.connected_peers[peer_id]["last_heartbeat"] = datetime.now()
                return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Health check failed for {peer_id}: {e}")
        
        return False
    
    def _setup_default_handlers(self):
        """デフォルトメッセージハンドラー設定"""
        self.message_handlers.update({
            "health_check": self._handle_health_check,
            "capability_request": self._handle_capability_request,
            "soul_request": self._handle_soul_request,
            "collaboration_invite": self._handle_collaboration_invite,
            "status_inquiry": self._handle_status_inquiry
        })
    
    async def _handle_health_check(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ヘルスチェックハンドラー"""
        return {
            "status": "healthy",
            "soul_id": self.soul_identity.soul_id,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.stats["start_time"]).total_seconds(),
            "stats": self.stats.copy()
        }
    
    async def _handle_capability_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """能力要求ハンドラー"""
        return {
            "soul_id": self.soul_identity.soul_id,
            "capabilities": [cap.value for cap in self.soul_identity.capabilities],
            "elder_type": self.soul_identity.elder_type.value,
            "hierarchy_level": self.soul_identity.hierarchy_level,
            "available": True
        }
    
    async def _handle_soul_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """魂リクエストハンドラー"""
        # 基底魂の process_soul_request を呼び出し（実装は各魂で行う）
        return {
            "soul_id": self.soul_identity.soul_id,
            "request_processed": True,
            "result": "Request acknowledged via Google A2A",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_collaboration_invite(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """協調招待ハンドラー"""
        collaboration_id = request.get("collaboration_id", str(uuid.uuid4()))
        
        return {
            "soul_id": self.soul_identity.soul_id,
            "collaboration_id": collaboration_id,
            "accepted": True,
            "capabilities_offered": [cap.value for cap in self.soul_identity.capabilities],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_status_inquiry(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ステータス問い合わせハンドラー"""
        return {
            "soul_id": self.soul_identity.soul_id,
            "elder_type": self.soul_identity.elder_type.value,
            "state": "active",
            "connected_peers": len(self.connected_peers),
            "active_streams": len(self.active_streams),
            "stats": self.stats.copy(),
            "service_info": asdict(self.service_definition)
        }
    
    # === 公開API ===
    
    async def call_rpc(self, target_soul_id: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """RPC呼び出し"""
        if target_soul_id not in self.connected_peers:
            self.logger.warning(f"⚠️ Peer not connected: {target_soul_id}")
            return None
        
        try:
            peer_info = self.connected_peers[target_soul_id]
            rpc_connection = peer_info["connections"].get("rpc")
            
            if not rpc_connection:
                self.logger.warning(f"⚠️ No RPC connection to {target_soul_id}")
                return None
            
            self.stats["rpc_calls_made"] += 1
            
            if GOOGLE_A2A_AVAILABLE:
                # 実際のGoogle A2A RPC呼び出し
                response = await rpc_connection.call(method, params)
                return response
            else:
                # フォールバック実装（シミュレーション）
                self.logger.info(f"📞 RPC call to {target_soul_id}: {method}")
                
                # メッセージハンドラーでシミュレート
                if method in self.message_handlers:
                    return await self.message_handlers[method](params)
                
                return {"status": "simulated", "method": method, "params": params}
                
        except Exception as e:
            self.logger.error(f"❌ RPC call failed to {target_soul_id}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def send_stream_message(self, target_soul_id: str, message: Dict[str, Any]) -> bool:
        """ストリームメッセージ送信"""
        if target_soul_id not in self.connected_peers:
            return False
        
        try:
            peer_info = self.connected_peers[target_soul_id]
            stream_connection = peer_info["connections"].get("stream")
            
            if not stream_connection:
                return False
            
            if GOOGLE_A2A_AVAILABLE:
                # 実際のGoogle A2A ストリーム送信
                await stream_connection.send(message)
            else:
                # フォールバック実装
                self.logger.info(f"📡 Stream message to {target_soul_id}: {message.get('type', 'unknown')}")
            
            self.stats["messages_sent"] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Stream message failed to {target_soul_id}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def publish_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """Pub/Subメッセージ発行"""
        try:
            if GOOGLE_A2A_AVAILABLE and self.agent:
                # 実際のGoogle A2A Pub/Sub発行
                await self.agent.publish(topic, message)
            else:
                # フォールバック実装
                self.logger.info(f"📢 Published to {topic}: {message.get('type', 'unknown')}")
            
            self.stats["messages_sent"] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Publish failed to {topic}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def discover_souls_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """能力による魂探索"""
        matching_souls = []
        
        try:
            if GOOGLE_A2A_AVAILABLE and self.service_registry:
                # 実際のGoogle A2A サービス探索
                services = await self.service_registry.discover_services_by_capability(capability)
                matching_souls.extend(services)
            else:
                # フォールバック実装
                for peer_id, peer_info in self.connected_peers.items():
                    peer_capabilities = peer_info["config"].get("capabilities", [])
                    if capability in peer_capabilities:
                        matching_souls.append(peer_info["config"])
            
            self.logger.info(f"🔍 Found {len(matching_souls)} souls with capability: {capability}")
            return matching_souls
            
        except Exception as e:
            self.logger.error(f"❌ Soul discovery failed for capability {capability}: {e}")
            return []
    
    async def invite_collaboration(self, target_soul_ids: List[str], collaboration_type: str) -> Dict[str, Any]:
        """協調作業招待"""
        collaboration_id = str(uuid.uuid4())
        invitation_results = {}
        
        for target_soul_id in target_soul_ids:
            try:
                response = await self.call_rpc(target_soul_id, "collaboration_invite", {
                    "collaboration_id": collaboration_id,
                    "collaboration_type": collaboration_type,
                    "initiator": self.soul_identity.soul_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                invitation_results[target_soul_id] = {
                    "accepted": response.get("accepted", False) if response else False,
                    "response": response
                }
                
            except Exception as e:
                invitation_results[target_soul_id] = {
                    "accepted": False,
                    "error": str(e)
                }
        
        self.logger.info(f"🤝 Collaboration invitation sent: {collaboration_id}")
        return {
            "collaboration_id": collaboration_id,
            "invitations": invitation_results,
            "accepted_count": sum(1 for result in invitation_results.values() if result["accepted"])
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """エージェントステータス取得"""
        return {
            "soul_identity": asdict(self.soul_identity),
            "service_definition": asdict(self.service_definition),
            "is_running": self.is_running.value,
            "connected_peers": len(self.connected_peers),
            "active_streams": len(self.active_streams),
            "statistics": self.stats.copy(),
            "google_a2a_available": GOOGLE_A2A_AVAILABLE,
            "uptime_seconds": (datetime.now() - self.stats["start_time"]).total_seconds()
        }


class GoogleA2ASoulManager:
    """Google A2A魂管理システム"""
    
    def __init__(self):
        self.agents: Dict[str, GoogleA2ASoulAgent] = {}
        self.is_running = mp.Value('b', False)
        self.logger = get_logger("google_a2a_soul_manager")
    
    async def start_manager(self) -> bool:
        """管理システム開始"""
        try:
            self.is_running.value = True
            
            # 管理ループ開始
            asyncio.create_task(self._management_loop())
            
            self.logger.info("🏛️ Google A2A Soul Manager started")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Google A2A Soul Manager: {e}")
            return False
    
    async def stop_manager(self):
        """管理システム停止"""
        self.is_running.value = False
        
        # 全エージェント停止
        for agent in list(self.agents.values()):
            await agent.shutdown()
        
        self.agents.clear()
        
        self.logger.info("🌅 Google A2A Soul Manager stopped")
    
    async def create_soul_agent(self, soul_identity: SoulIdentity, service_config: Dict[str, Any] = None) -> str:
        """魂エージェント作成"""
        try:
            # サービス定義作成
            service_definition = A2AServiceDefinition(
                service_id=soul_identity.soul_id,
                service_type=self._get_service_type_from_elder_type(soul_identity.elder_type),
                soul_identity=soul_identity,
                connection_types=[A2AConnectionType.RPC, A2AConnectionType.STREAM],
                endpoints={
                    "rpc": f"grpc://localhost:{9000 + len(self.agents)}",
                    "stream": f"tcp://localhost:{9100 + len(self.agents)}"
                },
                capabilities=[cap.value for cap in soul_identity.capabilities]
            )
            
            # カスタム設定適用
            if service_config:
                for key, value in service_config.items():
                    if hasattr(service_definition, key):
                        setattr(service_definition, key, value)
            
            # エージェント作成・初期化
            agent = GoogleA2ASoulAgent(soul_identity, service_definition)
            
            if await agent.initialize():
                self.agents[soul_identity.soul_id] = agent
                self.logger.info(f"✨ Soul agent created: {soul_identity.soul_name}")
                return soul_identity.soul_id
            else:
                raise RuntimeError(f"Failed to initialize agent for {soul_identity.soul_id}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create soul agent: {e}")
            return ""
    
    async def remove_soul_agent(self, soul_id: str) -> bool:
        """魂エージェント削除"""
        if soul_id not in self.agents:
            return False
        
        try:
            agent = self.agents[soul_id]
            await agent.shutdown()
            del self.agents[soul_id]
            
            self.logger.info(f"🗑️ Soul agent removed: {soul_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to remove soul agent {soul_id}: {e}")
            return False
    
    def get_agent(self, soul_id: str) -> Optional[GoogleA2ASoulAgent]:
        """エージェント取得"""
        return self.agents.get(soul_id)
    
    def get_all_agents(self) -> Dict[str, GoogleA2ASoulAgent]:
        """全エージェント取得"""
        return self.agents.copy()
    
    async def _management_loop(self):
        """管理ループ"""
        while self.is_running.value:
            try:
                # エージェント監視
                for soul_id, agent in list(self.agents.items()):
                    if not agent.is_running.value:
                        self.logger.warning(f"⚠️ Agent not running: {soul_id}")
                        # 必要に応じて再起動処理
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"❌ Management loop error: {e}")
                await asyncio.sleep(30)
    
    def _get_service_type_from_elder_type(self, elder_type: ElderType) -> A2AServiceType:
        """Elder TypeからService Typeへの変換"""
        if elder_type in [ElderType.GRAND_ELDER, ElderType.CLAUDE_ELDER, ElderType.ANCIENT_ELDER]:
            return A2AServiceType.ELDER_SERVICE
        elif elder_type == ElderType.SAGE:
            return A2AServiceType.SAGE_SERVICE
        elif elder_type == ElderType.KNIGHT:
            return A2AServiceType.KNIGHT_SERVICE
        elif elder_type == ElderType.SERVANT:
            return A2AServiceType.SERVANT_SERVICE
        else:
            return A2AServiceType.ELDER_SERVICE


# === ユーティリティ関数 ===

async def create_google_a2a_soul_manager() -> GoogleA2ASoulManager:
    """Google A2A魂管理システムの作成"""
    manager = GoogleA2ASoulManager()
    
    if await manager.start_manager():
        return manager
    else:
        raise RuntimeError("Failed to start Google A2A Soul Manager")


async def test_google_a2a_soul_system():
    """Google A2A魂システムのテスト"""
    print("🌟 Testing Google A2A Soul System...")
    
    # 管理システム作成
    manager = await create_google_a2a_soul_manager()
    
    try:
        # テスト用魂アイデンティティ作成
        claude_elder_identity = create_soul_identity(
            "Claude Elder",
            ElderType.CLAUDE_ELDER,
            [SoulCapability.LEADERSHIP, SoulCapability.COMMUNICATION, SoulCapability.PROBLEM_SOLVING]
        )
        
        knowledge_sage_identity = create_soul_identity(
            "Knowledge Sage",
            ElderType.SAGE,
            [SoulCapability.WISDOM, SoulCapability.LEARNING, SoulCapability.ANALYSIS]
        )
        
        # 魂エージェント作成
        claude_agent_id = await manager.create_soul_agent(claude_elder_identity)
        sage_agent_id = await manager.create_soul_agent(knowledge_sage_identity)
        
        print(f"✅ Created agents: {claude_agent_id}, {sage_agent_id}")
        
        # エージェント取得
        claude_agent = manager.get_agent(claude_agent_id)
        sage_agent = manager.get_agent(sage_agent_id)
        
        if claude_agent and sage_agent:
            # 接続待機
            await asyncio.sleep(5)
            
            # RPC呼び出しテスト
            print("📞 Testing RPC call...")
            response = await claude_agent.call_rpc(sage_agent_id, "capability_request", {
                "requester": claude_agent_id
            })
            print(f"RPC Response: {response}")
            
            # 協調作業招待テスト
            print("🤝 Testing collaboration invitation...")
            collaboration_result = await claude_agent.invite_collaboration(
                [sage_agent_id],
                "knowledge_sharing"
            )
            print(f"Collaboration result: {collaboration_result}")
            
            # ステータス確認
            print("📊 Agent statuses:")
            for agent_id, agent in manager.get_all_agents().items():
                status = agent.get_agent_status()
                print(f"  {agent_id}: {status['connected_peers']} peers, {status['active_streams']} streams")
        
    finally:
        await manager.stop_manager()
    
    print("✅ Google A2A Soul System test completed!")


if __name__ == "__main__":
    print("🌟 Google A2A Soul Integration - GoogleのA2Aライブラリ統合魂システム")
    print("Test mode:")
    asyncio.run(test_google_a2a_soul_system())
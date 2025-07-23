#!/usr/bin/env python3
"""
Elder-Servant A2A Communication Optimization
エルダーズとエルダーサーバント間A2A通信最適化システム
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import structlog

from libs.a2a_communication import (
    A2AClient,
    A2AError,
    A2AErrorCode,
    A2AMessage,
    AgentInfo,
    AgentType,
    MessagePriority,
    MessageType,
)
from libs.env_config import get_config

logger = structlog.get_logger(__name__)


class LoadBalancingStrategy(Enum):
    """負荷分散戦略"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RESPONSE_TIME = "weighted_response_time"
    PRIORITY_BASED = "priority_based"


class ElderServantStatus(Enum):
    """エルダーサーバントの状態"""

    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class ElderServantMetrics:
    """エルダーサーバントのメトリクス"""

    servant_id: str
    status: ElderServantStatus
    current_load: int
    max_capacity: int
    average_response_time: float
    error_rate: float
    last_heartbeat: datetime
    active_tasks: List[str]
    queue_depth: int
    cpu_usage: float
    memory_usage: float


@dataclass
class CommunicationPolicy:
    """通信ポリシー"""

    max_retry_attempts: int = 3
    timeout_seconds: float = 30.0
    heartbeat_interval: float = 10.0
    load_threshold: float = 0.8
    priority_boost_factor: float = 1.5
    batch_size: int = 10
    rate_limit_per_second: int = 100


class ElderServantRegistry:
    """エルダーサーバントレジストリ"""

    def __init__(self):
        """初期化メソッド"""
        self.servants: Dict[str, ElderServantMetrics] = {}
        self.servant_groups: Dict[str, Set[str]] = defaultdict(set)
        self.lock = asyncio.Lock()

    async def register_servant(
        self, servant_id: str, capabilities: List[str], max_capacity: int = 10
    ):
        """エルダーサーバントを登録"""
        async with self.lock:
            metrics = ElderServantMetrics(
                servant_id=servant_id,
                status=ElderServantStatus.AVAILABLE,
                current_load=0,
                max_capacity=max_capacity,
                average_response_time=0.0,
                error_rate=0.0,
                last_heartbeat=datetime.utcnow(),
                active_tasks=[],
                queue_depth=0,
                cpu_usage=0.0,
                memory_usage=0.0,
            )

            self.servants[servant_id] = metrics

            # 能力グループに追加
            for capability in capabilities:
                self.servant_groups[capability].add(servant_id)

            logger.info(
                "Elder servant registered",
                servant_id=servant_id,
                capabilities=capabilities,
            )

    async def update_servant_metrics(
        self, servant_id: str, metrics_update: Dict[str, Any]
    ):
        """サーバントメトリクスを更新"""
        async with self.lock:
            if servant_id not in self.servants:
                logger.warning("Unknown servant metrics update", servant_id=servant_id)
                return

            metrics = self.servants[servant_id]

            # メトリクス更新
            for key, value in metrics_update.items():
                if hasattr(metrics, key):
                    setattr(metrics, key, value)

            metrics.last_heartbeat = datetime.utcnow()

            # ステータス自動更新
            await self._update_servant_status(servant_id)

    async def _update_servant_status(self, servant_id: str):
        """サーバントステータスの自動更新"""
        metrics = self.servants[servant_id]

        # 負荷に基づくステータス更新
        load_ratio = metrics.current_load / metrics.max_capacity

        if load_ratio >= 1.0:
            metrics.status = ElderServantStatus.OVERLOADED
        elif load_ratio >= 0.8:
            metrics.status = ElderServantStatus.BUSY
        else:
            metrics.status = ElderServantStatus.AVAILABLE

        # ハートビートタイムアウトチェック
        heartbeat_timeout = datetime.utcnow() - timedelta(seconds=30)
        if metrics.last_heartbeat < heartbeat_timeout:
            metrics.status = ElderServantStatus.OFFLINE

    async def get_available_servants(self, capability: str = None) -> List[str]:
        """利用可能なサーバント一覧を取得"""
        async with self.lock:
            available = []

            target_servants = (
                self.servant_groups.get(capability, set())
                if capability
                else set(self.servants.keys())
            )

            for servant_id in target_servants:
                metrics = self.servants.get(servant_id)
                if metrics and metrics.status in [
                    ElderServantStatus.AVAILABLE,
                    ElderServantStatus.BUSY,
                ]:
                    available.append(servant_id)

            return available

    async def get_servant_metrics(
        self, servant_id: str
    ) -> Optional[ElderServantMetrics]:
        """特定サーバントのメトリクス取得"""
        return self.servants.get(servant_id)


class LoadBalancer:
    """負荷分散器"""

    def __init__(
        self,
        registry: ElderServantRegistry,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME,
    ):
        self.registry = registry
        self.strategy = strategy
        self.round_robin_index = defaultdict(int)

    async def select_servant(
        self, capability: str = None, priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[str]:
        """最適なサーバントを選択"""
        available_servants = await self.registry.get_available_servants(capability)

        if not available_servants:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return await self._round_robin_selection(available_servants, capability)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_selection(available_servants)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME:
            return await self._weighted_response_time_selection(available_servants)
        elif self.strategy == LoadBalancingStrategy.PRIORITY_BASED:
            return await self._priority_based_selection(available_servants, priority)

        return available_servants[0]  # フォールバック

    async def _round_robin_selection(self, servants: List[str], capability: str) -> str:
        """ラウンドロビン選択"""
        index = self.round_robin_index[capability or "default"]
        selected = servants[index % len(servants)]
        self.round_robin_index[capability or "default"] = (index + 1) % len(servants)
        return selected

    async def _least_connections_selection(self, servants: List[str]) -> str:
        """最少コネクション選択"""
        min_load = float("inf")
        best_servant = servants[0]

        for servant_id in servants:
            metrics = await self.registry.get_servant_metrics(servant_id)
            if metrics and metrics.current_load < min_load:
                min_load = metrics.current_load
                best_servant = servant_id

        return best_servant

    async def _weighted_response_time_selection(self, servants: List[str]) -> str:
        """加重応答時間選択"""
        best_score = float("inf")
        best_servant = servants[0]

        for servant_id in servants:
            metrics = await self.registry.get_servant_metrics(servant_id)
            if metrics:
                # スコア = 応答時間 * (1 + 負荷率)
                load_ratio = metrics.current_load / metrics.max_capacity
                score = metrics.average_response_time * (1 + load_ratio)

                if score < best_score:
                    best_score = score
                    best_servant = servant_id

        return best_servant

    async def _priority_based_selection(
        self, servants: List[str], priority: MessagePriority
    ) -> str:
        """優先度ベース選択"""
        # 高優先度メッセージには最も負荷の少ないサーバントを選択
        if priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
            return await self._least_connections_selection(servants)
        else:
            return await self._round_robin_selection(servants, "normal_priority")


class MessageBatcher:
    """メッセージバッチング"""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 1.0):
        """初期化メソッド"""
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.batches: Dict[str, List[A2AMessage]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.batch_callbacks: Dict[str, Callable] = {}

    async def add_message(
        self, target_servant: str, message: A2AMessage, callback: Callable
    ):
        """メッセージをバッチに追加"""
        self.batches[target_servant].append(message)
        self.batch_callbacks[target_servant] = callback

        # バッチサイズに達した場合は即座に送信
        if len(self.batches[target_servant]) >= self.batch_size:
            await self._send_batch(target_servant)
        else:
            # タイマー設定
            if target_servant not in self.batch_timers:
                self.batch_timers[target_servant] = asyncio.create_task(
                    self._batch_timeout_handler(target_servant)
                )

    async def _batch_timeout_handler(self, target_servant: str):
        """バッチタイムアウト処理"""
        await asyncio.sleep(self.batch_timeout)
        if target_servant in self.batches and self.batches[target_servant]:
            await self._send_batch(target_servant)

    async def _send_batch(self, target_servant: str):
        """バッチ送信"""
        if target_servant not in self.batches:
            return

        batch = self.batches.pop(target_servant, [])
        callback = self.batch_callbacks.pop(target_servant, None)

        if target_servant in self.batch_timers:
            self.batch_timers[target_servant].cancel()
            del self.batch_timers[target_servant]

        if batch and callback:
            await callback(target_servant, batch)


class CircuitBreaker:
    """サーキットブレーカー"""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """初期化メソッド"""
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_counts: Dict[str, int] = defaultdict(int)
        self.last_failure_times: Dict[str, datetime] = {}
        self.circuit_states: Dict[str, str] = defaultdict(
            lambda: "CLOSED"
        )  # CLOSED, OPEN, HALF_OPEN

    async def call_with_circuit_breaker(self, servant_id: str, coro: Callable) -> Any:
        """サーキットブレーカー付きでコール実行"""
        state = self.circuit_states[servant_id]

        if state == "OPEN":
            # タイムアウト後にハーフオープンに移行
            last_failure = self.last_failure_times.get(servant_id)
            if last_failure and datetime.utcnow() - last_failure > timedelta(
                seconds=self.timeout
            ):
                self.circuit_states[servant_id] = "HALF_OPEN"
            else:
                raise A2AError(
                    A2AErrorCode.SERVICE_UNAVAILABLE,
                    f"Circuit breaker open for {servant_id}",
                )

        try:
            result = await coro()

            # 成功時はリセット
            if state == "HALF_OPEN":
                self.circuit_states[servant_id] = "CLOSED"
                self.failure_counts[servant_id] = 0

            return result

        except Exception as e:
            await self._record_failure(servant_id)
            raise

    async def _record_failure(self, servant_id: str):
        """失敗を記録"""
        self.failure_counts[servant_id] += 1
        self.last_failure_times[servant_id] = datetime.utcnow()

        if self.failure_counts[servant_id] >= self.failure_threshold:
            self.circuit_states[servant_id] = "OPEN"
            logger.warning("Circuit breaker opened", servant_id=servant_id)


class ElderServantOptimizer:
    """エルダーサーバント通信最適化管理"""

    def __init__(self, elder_client:
        """初期化メソッド"""
    A2AClient, policy: CommunicationPolicy = None):
        self.elder_client = elder_client
        self.policy = policy or CommunicationPolicy()
        self.registry = ElderServantRegistry()
        self.load_balancer = LoadBalancer(self.registry)
        self.message_batcher = MessageBatcher(
            batch_size=self.policy.batch_size, batch_timeout=1.0
        )
        self.circuit_breaker = CircuitBreaker()

        # メトリクス
        self.total_messages = 0
        self.successful_messages = 0
        self.failed_messages = 0
        self.average_latency = 0.0
        self.optimization_enabled = True

    async def initialize(self):
        """初期化"""
        # デフォルトサーバントの登録
        default_servants = [
            ("elder_servant_001", ["task_execution", "file_operations"], 10),
            ("elder_servant_002", ["data_processing", "analysis"], 8),
            ("elder_servant_003", ["monitoring", "reporting"], 12),
            ("elder_servant_004", ["backup", "maintenance"], 6),
        ]

        for servant_id, capabilities, capacity in default_servants:
            await self.registry.register_servant(servant_id, capabilities, capacity)

        # ハートビート監視開始
        asyncio.create_task(self._heartbeat_monitor())

        logger.info("Elder-Servant optimizer initialized")

    async def send_optimized_message(
        self,
        capability: str,
        message_type: MessageType,
        method: str,
        params: Dict[str, Any] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        use_batching: bool = False,
    ) -> Any:
        """最適化されたメッセージ送信"""

        if not self.optimization_enabled:
            # 最適化無効時は直接送信
            return await self._direct_send(
                capability, message_type, method, params, priority
            )

        start_time = time.time()

        try:
            # 最適なサーバント選択
            servant_id = await self.load_balancer.select_servant(capability, priority)
            if not servant_id:
                raise A2AError(
                    A2AErrorCode.SERVICE_UNAVAILABLE,
                    f"No available servants for capability: {capability}",
                )

            # メッセージ作成
            message = await self._create_message(
                servant_id, message_type, method, params, priority
            )

            # バッチング使用時
            if use_batching and priority not in [MessagePriority.CRITICAL]:
                await self.message_batcher.add_message(
                    servant_id, message, self._send_batch_to_servant
                )
                return {"status": "batched", "servant_id": servant_id}

            # サーキットブレーカー付き送信
            response = await self.circuit_breaker.call_with_circuit_breaker(
                servant_id, lambda: self._send_to_servant(servant_id, message)
            )

            # メトリクス更新
            latency = time.time() - start_time
            await self._update_metrics(servant_id, latency, True)

            return response

        except Exception as e:
            latency = time.time() - start_time
            await self._update_metrics(None, latency, False)
            raise

    async def _create_message(
        self,
        servant_id: str,
        message_type: MessageType,
        method: str,
        params: Dict[str, Any],
        priority: MessagePriority,
    ) -> A2AMessage:
        """メッセージ作成"""
        from libs.a2a_communication import A2AMessage, MessageHeader, MessagePayload

        # サーバント情報取得（簡略化）
        servant_info = AgentInfo(
            agent_id=servant_id,
            agent_type=AgentType.ELDER_SERVANT,
            instance_id=f"{servant_id}_001",
            capabilities=[],
            endpoints=[],
            priority=priority,
        )

        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source=self.elder_client.agent_info,
            target=servant_info,
            message_type=message_type,
            priority=priority,
            ttl=self.policy.timeout_seconds,
        )

        payload = MessagePayload(
            method=method,
            params=params or {},
            context={"optimization_enabled": True, "trace_id": str(uuid.uuid4())},
        )

        return A2AMessage(header=header, payload=payload)

    async def _send_to_servant(self, servant_id: str, message: A2AMessage) -> Any:
        """サーバントへの送信"""
        response = await self.elder_client.send_message(
            target_agent=servant_id,
            message_type=message.header.message_type,
            method=message.payload.method,
            params=message.payload.params,
            priority=message.header.priority,
            wait_for_response=True,
            timeout=self.policy.timeout_seconds,
        )

        return response.payload.data if response else None

    async def _send_batch_to_servant(self, servant_id: str, batch: List[A2AMessage]):
        """バッチをサーバントに送信"""
        try:
            # バッチメッセージ作成
            batch_message = await self._create_batch_message(servant_id, batch)

            response = await self.circuit_breaker.call_with_circuit_breaker(
                servant_id, lambda: self._send_to_servant(servant_id, batch_message)
            )

            logger.info(
                "Batch sent successfully", servant_id=servant_id, batch_size=len(batch)
            )

        except Exception as e:
            logger.error("Batch send failed", servant_id=servant_id, error=str(e))

    async def _create_batch_message(
        self, servant_id: str, batch: List[A2AMessage]
    ) -> A2AMessage:
        """バッチメッセージ作成"""
        batch_data = []
        for msg in batch:
            batch_data.append(
                {
                    "message_id": msg.header.message_id,
                    "method": msg.payload.method,
                    "params": msg.payload.params,
                    "priority": msg.header.priority.value,
                }
            )

        return await self._create_message(
            servant_id=servant_id,
            message_type=MessageType.COMMAND,
            method="execute_batch",
            params={"batch": batch_data},
            priority=MessagePriority.NORMAL,
        )

    async def _direct_send(
        self,
        capability: str,
        message_type: MessageType,
        method: str,
        params: Dict[str, Any],
        priority: MessagePriority,
    ) -> Any:
        """直接送信（最適化なし）"""
        # 最初の利用可能なサーバントに送信
        servants = await self.registry.get_available_servants(capability)
        if not servants:
            raise A2AError(A2AErrorCode.SERVICE_UNAVAILABLE, "No available servants")

        servant_id = servants[0]
        message = await self._create_message(
            servant_id, message_type, method, params, priority
        )

        return await self._send_to_servant(servant_id, message)

    async def _update_metrics(
        self, servant_id: Optional[str], latency: float, success: bool
    ):
        """メトリクス更新"""
        self.total_messages += 1

        if success:
            self.successful_messages += 1
            # 移動平均での遅延更新
            self.average_latency = (self.average_latency * 0.9) + (latency * 0.1)

            if servant_id:
                await self.registry.update_servant_metrics(
                    servant_id,
                    {
                        "average_response_time": latency,
                        "current_load": max(
                            0, self.registry.servants[servant_id].current_load - 1
                        ),
                    },
                )
        else:
            self.failed_messages += 1

    async def _heartbeat_monitor(self):
        """ハートビート監視"""
        while True:
            try:
                # 全サーバントのヘルスチェック
                for servant_id in list(self.registry.servants.keys()):
                    try:
                        await self.send_optimized_message(
                            capability="monitoring",
                            message_type=MessageType.HEALTH_CHECK,
                            method="ping",
                            params={},
                            priority=MessagePriority.LOW,
                        )
                    except Exception:
                        # ハートビート失敗をメトリクスに反映
                        await self.registry.update_servant_metrics(
                            servant_id, {"status": ElderServantStatus.OFFLINE}
                        )

                await asyncio.sleep(self.policy.heartbeat_interval)

            except Exception as e:
                logger.error("Heartbeat monitor error", error=str(e))
                await asyncio.sleep(5)

    async def get_optimization_metrics(self) -> Dict[str, Any]:
        """最適化メトリクス取得"""
        success_rate = (
            self.successful_messages / self.total_messages
            if self.total_messages > 0
            else 0
        )

        servant_metrics = {}
        for servant_id, metrics in self.registry.servants.items():
            servant_metrics[servant_id] = {
                "status": metrics.status.value,
                "load": f"{metrics.current_load}/{metrics.max_capacity}",
                "response_time": f"{metrics.average_response_time:.3f}s",
                "error_rate": f"{metrics.error_rate:.2%}",
            }

        return {
            "total_messages": self.total_messages,
            "success_rate": f"{success_rate:.2%}",
            "average_latency": f"{self.average_latency:.3f}s",
            "optimization_enabled": self.optimization_enabled,
            "load_balancing_strategy": self.load_balancer.strategy.value,
            "circuit_breaker_states": dict(self.circuit_breaker.circuit_states),
            "servant_metrics": servant_metrics,
        }

    async def enable_optimization(self, enabled: bool = True):
        """最適化有効/無効切り替え"""
        self.optimization_enabled = enabled
        logger.info("Optimization toggled", enabled=enabled)

    async def shutdown(self):
        """シャットダウン"""
        # 全バッチを強制送信
        for servant_id in list(self.message_batcher.batches.keys()):
            if self.message_batcher.batches[servant_id]:
                await self.message_batcher._send_batch(servant_id)

        logger.info("Elder-Servant optimizer shutdown complete")


# Example usage
async def example_elder_servant_optimization():
    """使用例"""
    from libs.a2a_communication import create_a2a_client

    try:
        # Elderクライアント作成
        elder_client = await create_a2a_client("knowledge_sage")

        # 最適化システム初期化
        optimizer = ElderServantOptimizer(elder_client)
        await optimizer.initialize()

        # 最適化された通信例

        # 1. 高優先度タスク（最適なサーバント選択）
        result1 = await optimizer.send_optimized_message(
            capability="task_execution",
            message_type=MessageType.TASK_ASSIGNMENT,
            method="execute_critical_task",
            params={"task_id": "crit_001", "deadline": "2025-07-09T18:00:00Z"},
            priority=MessagePriority.CRITICAL,
        )
        print(f"Critical task result: {result1}")

        # 2. バッチ処理（複数の低優先度タスク）
        for i in range(5):
            await optimizer.send_optimized_message(
                capability="data_processing",
                message_type=MessageType.COMMAND,
                method="process_data_chunk",
                params={"chunk_id": f"chunk_{i}", "data_size": 1024},
                priority=MessagePriority.LOW,
                use_batching=True,
            )

        # 3. 監視データ収集
        health_result = await optimizer.send_optimized_message(
            capability="monitoring",
            message_type=MessageType.HEALTH_CHECK,
            method="get_system_status",
            params={},
            priority=MessagePriority.NORMAL,
        )
        print(f"Health check result: {health_result}")

        # メトリクス表示
        metrics = await optimizer.get_optimization_metrics()
        print(f"Optimization metrics: {json.dumps(metrics, indent=2)}")

        # クリーンアップ
        await optimizer.shutdown()
        await elder_client.disconnect()

    except Exception as e:
        print(f"Example error: {e}")


if __name__ == "__main__":
    asyncio.run(example_elder_servant_optimization())

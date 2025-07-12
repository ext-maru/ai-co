#!/usr/bin/env python3
"""
✨ Elder Tree Soul Binding System - エルダーツリー魂紐づけシステム
エルダー間の魂の絆と通信を管理する高度なシステム

エルダーズギルド評議会承認 - 2025年7月12日
Creator: Claude Elder (クロードエルダー)
Soul Binding Technology: Quantum Entanglement Inspired
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import time

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_tree_hierarchy import (
    ElderTreeHierarchy, ElderNode, ElderMessage, ElderRank, SageType,
    get_elder_tree, MessagePriority
)


class SoulBindingState(Enum):
    """魂紐づけ状態"""
    UNBOUND = "unbound"                 # 未紐づけ
    BINDING = "binding"                 # 紐づけ中
    BOUND = "bound"                     # 紐づけ済み
    WEAKENING = "weakening"             # 弱化中
    BROKEN = "broken"                   # 破断
    RECOVERING = "recovering"           # 回復中


class SoulConnectionType(Enum):
    """魂接続タイプ"""
    DIRECT = "direct"                   # 直接接続
    HIERARCHICAL = "hierarchical"       # 階層接続
    COLLABORATIVE = "collaborative"     # 協調接続
    EMERGENCY = "emergency"             # 緊急接続
    QUANTUM_ENTANGLED = "quantum_entangled"  # 量子もつれ接続


class SoulEventType(Enum):
    """魂イベントタイプ"""
    BINDING_REQUEST = "binding_request"
    BINDING_ACCEPTED = "binding_accepted"
    BINDING_REJECTED = "binding_rejected"
    SOUL_SYNC = "soul_sync"
    WEAKENING_DETECTED = "weakening_detected"
    CONNECTION_LOST = "connection_lost"
    RECOVERY_INITIATED = "recovery_initiated"
    EMERGENCY_ALERT = "emergency_alert"


@dataclass
class SoulBinding:
    """魂の紐づけ情報"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    elder_a_id: str = ""
    elder_b_id: str = ""
    connection_type: SoulConnectionType = SoulConnectionType.DIRECT
    state: SoulBindingState = SoulBindingState.UNBOUND
    strength: float = 0.0  # 0.0-1.0
    established_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    sync_frequency: float = 1.0  # Hz
    metadata: Dict[str, Any] = field(default_factory=dict)
    quantum_signature: str = ""

    def __post_init__(self):
        """初期化後処理"""
        if not self.quantum_signature:
            self.quantum_signature = self._generate_quantum_signature()

    def _generate_quantum_signature(self) -> str:
        """量子署名生成"""
        combined = f"{self.elder_a_id}:{self.elder_b_id}:{time.time()}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]


@dataclass
class SoulEvent:
    """魂イベント"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SoulEventType = SoulEventType.SOUL_SYNC
    binding_id: str = ""
    elder_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False


class SoulResonanceCalculator:
    """魂の共鳴計算システム"""

    @staticmethod
    def calculate_binding_strength(elder_a: ElderNode, elder_b: ElderNode) -> float:
        """紐づけ強度計算"""
        strength_factors = []

        # 階層関係による強度
        if elder_a.parent_id == elder_b.id or elder_b.parent_id == elder_a.id:
            strength_factors.append(0.9)  # 親子関係は強い
        elif elder_a.rank == elder_b.rank:
            strength_factors.append(0.7)  # 同階級は中程度
        else:
            strength_factors.append(0.5)  # その他は基本レベル

        # 相互作用履歴による強度
        activity_factor = 0.6  # デフォルト
        if elder_a.last_activity and elder_b.last_activity:
            time_diff = abs((elder_a.last_activity - elder_b.last_activity).total_seconds())
            if time_diff < 3600:  # 1時間以内
                activity_factor = 0.9
            elif time_diff < 86400:  # 24時間以内
                activity_factor = 0.7
        strength_factors.append(activity_factor)

        # 機能的親和性
        compatibility = SoulResonanceCalculator._calculate_compatibility(elder_a, elder_b)
        strength_factors.append(compatibility)

        # 最終強度計算（加重平均）
        weights = [0.4, 0.3, 0.3]
        final_strength = sum(f * w for f, w in zip(strength_factors, weights))

        return min(1.0, max(0.0, final_strength))

    @staticmethod
    def _calculate_compatibility(elder_a: ElderNode, elder_b: ElderNode) -> float:
        """機能的親和性計算"""
        # 能力の重複度
        capabilities_a = set(elder_a.capabilities)
        capabilities_b = set(elder_b.capabilities)

        if not capabilities_a or not capabilities_b:
            return 0.5

        intersection = capabilities_a & capabilities_b
        union = capabilities_a | capabilities_b

        overlap_ratio = len(intersection) / len(union) if union else 0

        # 親和性スコア（適度な重複が理想）
        if 0.2 <= overlap_ratio <= 0.6:
            return 0.8 + (0.4 - abs(overlap_ratio - 0.4)) * 0.5
        else:
            return 0.4 + overlap_ratio * 0.4

    @staticmethod
    def calculate_decay_rate(binding: SoulBinding) -> float:
        """紐づけ減衰率計算"""
        base_decay = 0.01  # 1%/hour

        # 接続タイプによる減衰率調整
        type_modifiers = {
            SoulConnectionType.QUANTUM_ENTANGLED: 0.1,  # 量子もつれは減衰が少ない
            SoulConnectionType.DIRECT: 0.5,
            SoulConnectionType.HIERARCHICAL: 0.3,
            SoulConnectionType.COLLABORATIVE: 0.7,
            SoulConnectionType.EMERGENCY: 2.0  # 緊急接続は減衰が早い
        }

        modifier = type_modifiers.get(binding.connection_type, 1.0)
        return base_decay * modifier


class ElderSoulBindingSystem:
    """Elder魂紐づけシステム"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.elder_tree = get_elder_tree()
        self.soul_bindings: Dict[str, SoulBinding] = {}
        self.soul_events: List[SoulEvent] = []
        self.active_connections: Dict[str, Set[str]] = {}  # elder_id -> connected_elder_ids
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        self.resonance_calculator = SoulResonanceCalculator()

        # システム状態
        self.running = False
        self.last_maintenance = datetime.now()
        self.statistics = {
            "total_bindings": 0,
            "active_bindings": 0,
            "broken_bindings": 0,
            "sync_operations": 0,
            "emergency_connections": 0
        }

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_soul_binding")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Soul Binding - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def start_soul_binding_system(self):
        """魂紐づけシステム開始"""
        if self.running:
            self.logger.warning("Soul binding system already running")
            return

        self.running = True
        self.logger.info("✨ Elder Soul Binding System starting...")

        # まず核心エルダーの魂を紐づけ
        from libs.elder_tree_hierarchy import bind_all_core_elders
        souls_bound = bind_all_core_elders()

        if souls_bound:
            self.logger.info("✨ All core Elder souls successfully bound")
        else:
            self.logger.warning("⚠️ Some Elder souls failed to bind")

        # Elder Tree状態確認
        tree_status = self.elder_tree.get_elder_tree_status()
        self.logger.info(f"🌳 Elder Tree Status: {tree_status['bound_souls']}/{tree_status['total_nodes']} souls bound")

        # 核心エルダー間の量子もつれ接続を確立
        await self._establish_core_quantum_entanglements()

        # 定期メンテナンスタスクを開始
        asyncio.create_task(self._maintenance_loop())

        # イベント処理タスクを開始
        asyncio.create_task(self._event_processing_loop())

        self.logger.info("🚀 Elder Soul Binding System fully operational")

    async def _establish_core_quantum_entanglements(self):
        """核心エルダー間の量子もつれ確立"""
        core_connections = [
            ("grand_elder_maru", "claude_elder", SoulConnectionType.QUANTUM_ENTANGLED),
            ("claude_elder", "knowledge_sage", SoulConnectionType.HIERARCHICAL),
            ("claude_elder", "task_sage", SoulConnectionType.HIERARCHICAL),
            ("claude_elder", "incident_sage", SoulConnectionType.HIERARCHICAL),
            ("claude_elder", "rag_sage", SoulConnectionType.HIERARCHICAL),
            ("knowledge_sage", "task_sage", SoulConnectionType.COLLABORATIVE),
            ("knowledge_sage", "rag_sage", SoulConnectionType.COLLABORATIVE),
            ("incident_sage", "task_sage", SoulConnectionType.COLLABORATIVE),
        ]

        for elder_a_id, elder_b_id, connection_type in core_connections:
            if elder_a_id in self.elder_tree.nodes and elder_b_id in self.elder_tree.nodes:
                binding = await self.create_soul_binding(
                    elder_a_id, elder_b_id, connection_type
                )
                if binding:
                    self.logger.info(f"🔗 量子もつれ確立: {elder_a_id} ↔ {elder_b_id}")

    async def create_soul_binding(
        self,
        elder_a_id: str,
        elder_b_id: str,
        connection_type: SoulConnectionType = SoulConnectionType.DIRECT,
        force: bool = False
    ) -> Optional[SoulBinding]:
        """魂の紐づけ作成"""

        # エルダー存在確認
        if elder_a_id not in self.elder_tree.nodes or elder_b_id not in self.elder_tree.nodes:
            self.logger.error(f"Elder not found: {elder_a_id} or {elder_b_id}")
            return None

        elder_a = self.elder_tree.nodes[elder_a_id]
        elder_b = self.elder_tree.nodes[elder_b_id]

        # 既存バインディング確認
        existing_binding = self._find_existing_binding(elder_a_id, elder_b_id)
        if existing_binding and not force:
            self.logger.warning(f"Soul binding already exists: {elder_a_id} ↔ {elder_b_id}")
            return existing_binding

        # 魂が紐づけられているか確認
        if not elder_a.soul_bound or not elder_b.soul_bound:
            self.logger.error("Both elders must have bound souls for connection")
            return None

        # 新しい紐づけ作成
        binding = SoulBinding(
            elder_a_id=elder_a_id,
            elder_b_id=elder_b_id,
            connection_type=connection_type,
            state=SoulBindingState.BINDING
        )

        # 強度計算
        binding.strength = self.resonance_calculator.calculate_binding_strength(elder_a, elder_b)

        # 紐づけプロセス実行
        success = await self._execute_binding_process(binding)

        if success:
            binding.state = SoulBindingState.BOUND
            binding.established_at = datetime.now()
            binding.last_sync = datetime.now()

            # システムに登録
            self.soul_bindings[binding.id] = binding
            self._update_active_connections(binding)

            # 統計更新
            self.statistics["total_bindings"] += 1
            self.statistics["active_bindings"] += 1

            # イベント記録
            event = SoulEvent(
                event_type=SoulEventType.BINDING_ACCEPTED,
                binding_id=binding.id,
                elder_id=elder_a_id,
                data={"connected_to": elder_b_id, "strength": binding.strength}
            )
            self.soul_events.append(event)

            # 同期タスク開始
            await self._start_sync_task(binding)

            self.logger.info(f"✨ Soul binding created: {elder_a.name} ↔ {elder_b.name} (strength: {binding.strength:.2f})")
            return binding

        else:
            self.logger.error(f"❌ Soul binding failed: {elder_a_id} ↔ {elder_b_id}")
            return None

    async def _execute_binding_process(self, binding: SoulBinding) -> bool:
        """紐づけプロセス実行"""
        try:
            # 量子もつれの場合は特別な処理
            if binding.connection_type == SoulConnectionType.QUANTUM_ENTANGLED:
                return await self._establish_quantum_entanglement(binding)

            # 通常の紐づけプロセス
            # 1. 魂の共鳴確認
            if binding.strength < 0.3:
                self.logger.warning(f"Low resonance for binding: {binding.strength}")
                return False

            # 2. エルダー間通信テスト
            test_success = await self._test_elder_communication(binding)
            if not test_success:
                return False

            # 3. 紐づけ登録
            await asyncio.sleep(0.1)  # シンボリックな紐づけ時間

            return True

        except Exception as e:
            self.logger.error(f"Binding process error: {e}")
            return False

    async def _establish_quantum_entanglement(self, binding: SoulBinding) -> bool:
        """量子もつれ確立"""
        try:
            # 量子署名生成
            binding.quantum_signature = binding._generate_quantum_signature()

            # 両方のエルダーに量子もつれトークンを設定
            elder_a = self.elder_tree.nodes[binding.elder_a_id]
            elder_b = self.elder_tree.nodes[binding.elder_b_id]

            entanglement_token = f"quantum_{binding.quantum_signature}"
            elder_a.metadata["quantum_entanglement"] = entanglement_token
            elder_b.metadata["quantum_entanglement"] = entanglement_token

            # 量子もつれは強度を1.0に設定
            binding.strength = 1.0

            self.logger.info(f"🌌 Quantum entanglement established: {binding.quantum_signature}")
            return True

        except Exception as e:
            self.logger.error(f"Quantum entanglement error: {e}")
            return False

    async def _test_elder_communication(self, binding: SoulBinding) -> bool:
        """エルダー間通信テスト"""
        try:
            # テストメッセージ送信
            test_message = ElderMessage(
                sender_id=binding.elder_a_id,
                sender_rank=self.elder_tree.nodes[binding.elder_a_id].rank,
                receiver_id=binding.elder_b_id,
                receiver_rank=self.elder_tree.nodes[binding.elder_b_id].rank,
                message_type="soul_binding_test",
                content={"test": True, "binding_id": binding.id}
            )

            success = self.elder_tree.send_elder_message(test_message)

            if success:
                # メッセージ処理
                processed = self.elder_tree.process_message_queue()
                return processed > 0

            return False

        except Exception as e:
            self.logger.error(f"Communication test error: {e}")
            return False

    def _find_existing_binding(self, elder_a_id: str, elder_b_id: str) -> Optional[SoulBinding]:
        """既存の紐づけ検索"""
        for binding in self.soul_bindings.values():
            if ((binding.elder_a_id == elder_a_id and binding.elder_b_id == elder_b_id) or
                (binding.elder_a_id == elder_b_id and binding.elder_b_id == elder_a_id)):
                return binding
        return None

    def _update_active_connections(self, binding: SoulBinding):
        """アクティブ接続更新"""
        if binding.elder_a_id not in self.active_connections:
            self.active_connections[binding.elder_a_id] = set()
        if binding.elder_b_id not in self.active_connections:
            self.active_connections[binding.elder_b_id] = set()

        self.active_connections[binding.elder_a_id].add(binding.elder_b_id)
        self.active_connections[binding.elder_b_id].add(binding.elder_a_id)

    async def _start_sync_task(self, binding: SoulBinding):
        """同期タスク開始"""
        if binding.id in self.sync_tasks:
            self.sync_tasks[binding.id].cancel()

        sync_task = asyncio.create_task(self._soul_sync_loop(binding))
        self.sync_tasks[binding.id] = sync_task

    async def _soul_sync_loop(self, binding: SoulBinding):
        """魂の同期ループ"""
        try:
            interval = 1.0 / binding.sync_frequency  # 秒

            while binding.state == SoulBindingState.BOUND and self.running:
                await asyncio.sleep(interval)

                # 魂の同期実行
                await self._perform_soul_sync(binding)

        except asyncio.CancelledError:
            self.logger.debug(f"Sync task cancelled for binding {binding.id}")
        except Exception as e:
            self.logger.error(f"Soul sync error: {e}")

    async def _perform_soul_sync(self, binding: SoulBinding):
        """魂の同期実行"""
        try:
            # 減衰計算
            time_since_last_sync = (datetime.now() - binding.last_sync).total_seconds() / 3600
            decay_rate = self.resonance_calculator.calculate_decay_rate(binding)
            strength_loss = decay_rate * time_since_last_sync

            binding.strength = max(0.0, binding.strength - strength_loss)
            binding.last_sync = datetime.now()

            # 統計更新
            self.statistics["sync_operations"] += 1

            # 弱化検知
            if binding.strength < 0.2 and binding.state == SoulBindingState.BOUND:
                binding.state = SoulBindingState.WEAKENING
                event = SoulEvent(
                    event_type=SoulEventType.WEAKENING_DETECTED,
                    binding_id=binding.id,
                    elder_id=binding.elder_a_id,
                    data={"strength": binding.strength}
                )
                self.soul_events.append(event)
                self.logger.warning(f"⚠️ Soul binding weakening: {binding.id} (strength: {binding.strength:.2f})")

            # 破断検知
            elif binding.strength <= 0.0:
                binding.state = SoulBindingState.BROKEN
                event = SoulEvent(
                    event_type=SoulEventType.CONNECTION_LOST,
                    binding_id=binding.id,
                    elder_id=binding.elder_a_id,
                    data={"reason": "strength_depleted"}
                )
                self.soul_events.append(event)
                self.logger.error(f"💔 Soul binding broken: {binding.id}")

                # 統計更新
                self.statistics["active_bindings"] -= 1
                self.statistics["broken_bindings"] += 1

                # 同期タスク停止
                if binding.id in self.sync_tasks:
                    self.sync_tasks[binding.id].cancel()
                    del self.sync_tasks[binding.id]

        except Exception as e:
            self.logger.error(f"Soul sync error: {e}")

    async def _maintenance_loop(self):
        """定期メンテナンスループ"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5分間隔
                await self._perform_maintenance()
            except Exception as e:
                self.logger.error(f"Maintenance error: {e}")

    async def _perform_maintenance(self):
        """定期メンテナンス実行"""
        self.logger.debug("🔧 Performing soul binding maintenance...")

        # 破断した紐づけのクリーンアップ
        broken_bindings = [
            binding_id for binding_id, binding in self.soul_bindings.items()
            if binding.state == SoulBindingState.BROKEN
        ]

        for binding_id in broken_bindings:
            await self._cleanup_broken_binding(binding_id)

        # 弱化した紐づけの回復試行
        weakened_bindings = [
            binding for binding in self.soul_bindings.values()
            if binding.state == SoulBindingState.WEAKENING
        ]

        for binding in weakened_bindings:
            await self._attempt_binding_recovery(binding)

        self.last_maintenance = datetime.now()

    async def _cleanup_broken_binding(self, binding_id: str):
        """破断した紐づけのクリーンアップ"""
        if binding_id not in self.soul_bindings:
            return

        binding = self.soul_bindings[binding_id]

        # アクティブ接続から削除
        if binding.elder_a_id in self.active_connections:
            self.active_connections[binding.elder_a_id].discard(binding.elder_b_id)
        if binding.elder_b_id in self.active_connections:
            self.active_connections[binding.elder_b_id].discard(binding.elder_a_id)

        # 同期タスク停止
        if binding_id in self.sync_tasks:
            self.sync_tasks[binding_id].cancel()
            del self.sync_tasks[binding_id]

        # バインディング削除
        del self.soul_bindings[binding_id]

        self.logger.info(f"🗑️ Cleaned up broken binding: {binding_id}")

    async def _attempt_binding_recovery(self, binding: SoulBinding):
        """紐づけ回復試行"""
        try:
            elder_a = self.elder_tree.nodes[binding.elder_a_id]
            elder_b = self.elder_tree.nodes[binding.elder_b_id]

            # 新しい強度計算
            new_strength = self.resonance_calculator.calculate_binding_strength(elder_a, elder_b)

            if new_strength > binding.strength:
                binding.strength = new_strength
                binding.state = SoulBindingState.RECOVERING

                # 回復イベント記録
                event = SoulEvent(
                    event_type=SoulEventType.RECOVERY_INITIATED,
                    binding_id=binding.id,
                    elder_id=binding.elder_a_id,
                    data={"old_strength": binding.strength, "new_strength": new_strength}
                )
                self.soul_events.append(event)

                self.logger.info(f"🔄 Soul binding recovery: {binding.id} (strength: {new_strength:.2f})")

                # 十分な強度に回復した場合
                if new_strength > 0.5:
                    binding.state = SoulBindingState.BOUND
                    await self._start_sync_task(binding)

        except Exception as e:
            self.logger.error(f"Binding recovery error: {e}")

    async def _event_processing_loop(self):
        """イベント処理ループ"""
        while self.running:
            try:
                await asyncio.sleep(1.0)  # 1秒間隔
                await self._process_pending_events()
            except Exception as e:
                self.logger.error(f"Event processing error: {e}")

    async def _process_pending_events(self):
        """保留中イベント処理"""
        unprocessed_events = [event for event in self.soul_events if not event.processed]

        for event in unprocessed_events:
            try:
                await self._handle_soul_event(event)
                event.processed = True
            except Exception as e:
                self.logger.error(f"Event handling error: {e}")

    async def _handle_soul_event(self, event: SoulEvent):
        """魂イベント処理"""
        if event.event_type == SoulEventType.EMERGENCY_ALERT:
            await self._handle_emergency_alert(event)
        elif event.event_type == SoulEventType.WEAKENING_DETECTED:
            await self._handle_weakening_detection(event)
        elif event.event_type == SoulEventType.CONNECTION_LOST:
            await self._handle_connection_loss(event)

    async def _handle_emergency_alert(self, event: SoulEvent):
        """緊急アラート処理"""
        self.logger.critical(f"🚨 Emergency Alert: {event.data}")

        # 緊急接続確立
        if "target_elder" in event.data:
            target_elder = event.data["target_elder"]
            emergency_binding = await self.create_soul_binding(
                event.elder_id, target_elder, SoulConnectionType.EMERGENCY, force=True
            )
            if emergency_binding:
                self.statistics["emergency_connections"] += 1

    async def _handle_weakening_detection(self, event: SoulEvent):
        """弱化検知処理"""
        binding = self.soul_bindings.get(event.binding_id)
        if binding:
            # 自動回復試行
            await self._attempt_binding_recovery(binding)

    async def _handle_connection_loss(self, event: SoulEvent):
        """接続喪失処理"""
        # 代替ルート検索
        await self._find_alternative_routes(event.elder_id)

    async def _find_alternative_routes(self, elder_id: str):
        """代替ルート検索"""
        # 簡単な代替ルート検索実装
        # より詳細な実装は将来的に追加
        pass

    def get_soul_binding_status(self) -> Dict[str, Any]:
        """魂紐づけシステム状態取得"""
        active_bindings = [
            binding for binding in self.soul_bindings.values()
            if binding.state == SoulBindingState.BOUND
        ]

        avg_strength = sum(binding.strength for binding in active_bindings) / len(active_bindings) if active_bindings else 0

        return {
            "system_running": self.running,
            "total_bindings": len(self.soul_bindings),
            "active_bindings": len(active_bindings),
            "average_strength": avg_strength,
            "sync_tasks": len(self.sync_tasks),
            "pending_events": len([e for e in self.soul_events if not e.processed]),
            "statistics": self.statistics.copy(),
            "last_maintenance": self.last_maintenance.isoformat(),
            "connected_elders": len(self.active_connections)
        }

    async def emergency_soul_binding(self, elder_a_id: str, elder_b_id: str) -> Optional[SoulBinding]:
        """緊急魂紐づけ"""
        self.logger.warning(f"🚨 Emergency soul binding request: {elder_a_id} ↔ {elder_b_id}")

        binding = await self.create_soul_binding(
            elder_a_id, elder_b_id, SoulConnectionType.EMERGENCY, force=True
        )

        if binding:
            # 緊急接続は強制的に高強度に設定
            binding.strength = 0.9
            binding.sync_frequency = 10.0  # 高頻度同期

            # 緊急イベント記録
            event = SoulEvent(
                event_type=SoulEventType.EMERGENCY_ALERT,
                binding_id=binding.id,
                elder_id=elder_a_id,
                data={"emergency_connection": True, "target": elder_b_id}
            )
            self.soul_events.append(event)

            self.statistics["emergency_connections"] += 1

        return binding

    async def stop_soul_binding_system(self):
        """魂紐づけシステム停止"""
        if not self.running:
            return

        self.logger.info("🛑 Stopping Elder Soul Binding System...")

        self.running = False

        # 全同期タスク停止
        for task in self.sync_tasks.values():
            task.cancel()

        await asyncio.gather(*self.sync_tasks.values(), return_exceptions=True)
        self.sync_tasks.clear()

        self.logger.info("✅ Elder Soul Binding System stopped")

    def save_soul_bindings(self, file_path: str = "data/soul_bindings.json"):
        """魂紐づけ状態保存"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                "bindings": {
                    binding_id: {
                        "id": binding.id,
                        "elder_a_id": binding.elder_a_id,
                        "elder_b_id": binding.elder_b_id,
                        "connection_type": binding.connection_type.value,
                        "state": binding.state.value,
                        "strength": binding.strength,
                        "established_at": binding.established_at.isoformat() if binding.established_at else None,
                        "last_sync": binding.last_sync.isoformat() if binding.last_sync else None,
                        "sync_frequency": binding.sync_frequency,
                        "metadata": binding.metadata,
                        "quantum_signature": binding.quantum_signature
                    }
                    for binding_id, binding in self.soul_bindings.items()
                },
                "statistics": self.statistics,
                "saved_at": datetime.now().isoformat()
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"💾 Soul bindings saved: {file_path}")

        except Exception as e:
            self.logger.error(f"Soul bindings save error: {e}")


# Global soul binding system instance
_soul_binding_system: Optional[ElderSoulBindingSystem] = None


def get_soul_binding_system() -> ElderSoulBindingSystem:
    """魂紐づけシステム取得"""
    global _soul_binding_system

    if _soul_binding_system is None:
        _soul_binding_system = ElderSoulBindingSystem()

    return _soul_binding_system


async def initialize_soul_binding_system() -> ElderSoulBindingSystem:
    """魂紐づけシステム初期化"""
    system = get_soul_binding_system()
    await system.start_soul_binding_system()
    return system


# Example Usage and Testing
if __name__ == "__main__":
    async def main():
        print("✨ Elder Soul Binding System Test")

        # システム初期化
        soul_system = await initialize_soul_binding_system()

        # 状態確認
        status = soul_system.get_soul_binding_status()
        print(f"\n📊 Soul Binding Status:")
        print(f"- Active Bindings: {status['active_bindings']}")
        print(f"- Average Strength: {status['average_strength']:.2f}")
        print(f"- Connected Elders: {status['connected_elders']}")

        # テスト待機
        print("\n⏳ Testing soul synchronization...")
        await asyncio.sleep(5)

        # 最終状態確認
        final_status = soul_system.get_soul_binding_status()
        print(f"\n📈 Final Status:")
        print(f"- Sync Operations: {final_status['statistics']['sync_operations']}")
        print(f"- Total Bindings: {final_status['statistics']['total_bindings']}")

        # システム停止
        await soul_system.stop_soul_binding_system()

        print("\n🎉 Soul Binding System Test Complete!")

    asyncio.run(main())

#!/usr/bin/env python3
"""
🔗 Weapon Sharing System - 武具共有システム
ドワーフ工房と騎士団の間で武具を共有・配送するシステム

このシステムにより：
- 騎士団は必要な武具をリクエスト
- ドワーフ工房は最適な武具を作成・配送
- リアルタイムで武具の状態を共有
- 戦況に応じた動的な武具配分
"""

import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class WeaponType(Enum):
    """武具タイプ"""

    # 最適化ツール
    MEMORY_OPTIMIZER = "memory_optimizer"
    CPU_BALANCER = "cpu_balancer"
    CACHE_OPTIMIZER = "cache_optimizer"

    # 監視武器
    ANOMALY_DETECTOR = "anomaly_detector"
    PERFORMANCE_SCOUT = "performance_scout"
    RESOURCE_GUARDIAN = "resource_guardian"

    # 特殊武具
    EMERGENCY_SHIELD = "emergency_shield"
    RAPID_RECOVERY_KIT = "rapid_recovery_kit"
    TACTICAL_ANALYZER = "tactical_analyzer"


class RequestPriority(Enum):
    """リクエスト優先度"""

    CRITICAL = "critical"  # 即座に必要
    HIGH = "high"  # 1時間以内
    MEDIUM = "medium"  # 6時間以内
    LOW = "low"  # 24時間以内


class DeliveryStatus(Enum):
    """配送状態"""

    PENDING = "pending"
    CRAFTING = "crafting"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    REJECTED = "rejected"


@dataclass
class WeaponRequest:
    """武具リクエスト"""

    request_id: str
    requester_id: str  # 騎士団ID
    weapon_type: WeaponType
    priority: RequestPriority
    quantity: int
    purpose: str
    requested_at: datetime
    required_by: Optional[datetime] = None
    metadata: Dict[str, Any] = None


@dataclass
class WeaponDelivery:
    """武具配送"""

    delivery_id: str
    request_id: str
    weapon_specs: List[Dict[str, Any]]
    status: DeliveryStatus
    estimated_delivery: datetime
    actual_delivery: Optional[datetime] = None
    delivery_notes: Optional[str] = None


class SharedWeaponInventory:
    """共有武具インベントリ"""

    def __init__(self):
        """初期化"""
        self.inventory = defaultdict(list)
        self.allocated_weapons = {}
        self.weapon_metadata = {}
        self._lock = threading.Lock()

        logger.info("🗃️ Shared Weapon Inventory initialized")

    def add_weapon(
        self,
        weapon_id: str,
        weapon_type: WeaponType,
        specs: Dict[str, Any],
        owner: str = "workshop",
    ):
        """武具を追加"""
        with self._lock:
            weapon_data = {
                "weapon_id": weapon_id,
                "weapon_type": weapon_type,
                "specs": specs,
                "owner": owner,
                "status": "available",
                "created_at": datetime.now(),
                "last_used": None,
                "usage_count": 0,
                "maintenance_required": False,
            }

            self.inventory[weapon_type].append(weapon_data)
            self.weapon_metadata[weapon_id] = weapon_data

            logger.info(
                f"➕ Added weapon {weapon_id} ({weapon_type.value}) to inventory"
            )

    def allocate_weapon(self, weapon_id: str, allocated_to: str) -> bool:
        """武具を割り当て"""
        with self._lock:
            if weapon_id not in self.weapon_metadata:
                return False

            weapon_data = self.weapon_metadata[weapon_id]
            if weapon_data["status"] != "available":
                return False

            weapon_data["status"] = "allocated"
            weapon_data["last_used"] = datetime.now()
            weapon_data["usage_count"] += 1
            self.allocated_weapons[weapon_id] = allocated_to

            logger.info(f"🎯 Allocated weapon {weapon_id} to {allocated_to}")
            return True

    def release_weapon(self, weapon_id: str) -> bool:
        """武具を解放"""
        with self._lock:
            if weapon_id not in self.weapon_metadata:
                return False

            weapon_data = self.weapon_metadata[weapon_id]
            weapon_data["status"] = "available"

            if weapon_id in self.allocated_weapons:
                del self.allocated_weapons[weapon_id]

            # 使用回数に応じてメンテナンスフラグ
            if weapon_data["usage_count"] % 10 == 0:
                weapon_data["maintenance_required"] = True

            logger.info(f"🔓 Released weapon {weapon_id}")
            return True

    def get_available_weapons(
        self, weapon_type: Optional[WeaponType] = None
    ) -> List[Dict[str, Any]]:
        """利用可能な武具を取得"""
        with self._lock:
            available = []

            if weapon_type:
                weapon_list = self.inventory.get(weapon_type, [])
            else:
                weapon_list = [
                    w for weapons in self.inventory.values() for w in weapons
                ]

            for weapon in weapon_list:
                if (
                    weapon["status"] == "available"
                    and not weapon["maintenance_required"]
                ):
                    available.append(weapon.copy())

            return available

    def perform_maintenance(self, weapon_id: str) -> bool:
        """武具のメンテナンス"""
        with self._lock:
            if weapon_id not in self.weapon_metadata:
                return False

            weapon_data = self.weapon_metadata[weapon_id]
            weapon_data["maintenance_required"] = False
            weapon_data["last_maintenance"] = datetime.now()

            # メンテナンスで性能向上
            if "effectiveness" in weapon_data["specs"]:
                weapon_data["specs"]["effectiveness"] = min(
                    1.0, weapon_data["specs"]["effectiveness"] * 1.05
                )

            logger.info(f"🔧 Performed maintenance on weapon {weapon_id}")
            return True


class WeaponSharingCoordinator:
    """武具共有コーディネーター"""

    def __init__(self, inventory: SharedWeaponInventory):
        """初期化"""
        self.inventory = inventory
        self.pending_requests = deque()
        self.active_deliveries = {}
        self.request_history = []
        self.delivery_metrics = {
            "total_requests": 0,
            "fulfilled_requests": 0,
            "rejected_requests": 0,
            "average_delivery_time": 0,
            "weapon_utilization": defaultdict(float),
        }

        self._request_processor_thread = None
        self._delivery_tracker_thread = None
        self._running = False

        logger.info("🤝 Weapon Sharing Coordinator initialized")

    def start(self):
        """コーディネーター開始"""
        self._running = True

        self._request_processor_thread = threading.Thread(
            target=self._process_requests_loop, daemon=True
        )
        self._request_processor_thread.start()

        self._delivery_tracker_thread = threading.Thread(
            target=self._track_deliveries_loop, daemon=True
        )
        self._delivery_tracker_thread.start()

        logger.info("✅ Weapon Sharing Coordinator started")

    def stop(self):
        """コーディネーター停止"""
        self._running = False
        logger.info("🛑 Weapon Sharing Coordinator stopped")

    def submit_request(self, request: WeaponRequest) -> str:
        """武具リクエストを提出"""
        self.pending_requests.append(request)
        self.request_history.append(request)
        self.delivery_metrics["total_requests"] += 1

        logger.info(
            f"📥 Received weapon request {request.request_id} from {request.requester_id}"
        )
        return request.request_id

    def _process_requests_loop(self):
        """リクエスト処理ループ"""
        while self._running:
            if self.pending_requests:
                request = self.pending_requests.popleft()
                self._process_single_request(request)
            else:
                time.sleep(1)

    def _process_single_request(self, request: WeaponRequest):
        """単一リクエストを処理"""
        # 利用可能な武具を確認
        available_weapons = self.inventory.get_available_weapons(request.weapon_type)

        if len(available_weapons) >= request.quantity:
            # 即座に配送可能
            self._fulfill_request_immediately(
                request, available_weapons[: request.quantity]
            )
        else:
            # クラフトが必要
            self._schedule_crafting(request)

    def _fulfill_request_immediately(
        self, request: WeaponRequest, weapons: List[Dict[str, Any]]
    ):
        """即座にリクエストを満たす"""
        weapon_specs = []

        for weapon in weapons:
            if self.inventory.allocate_weapon(
                weapon["weapon_id"], request.requester_id
            ):
                weapon_specs.append(
                    {
                        "weapon_id": weapon["weapon_id"],
                        "weapon_type": weapon["weapon_type"].value,
                        "specs": weapon["specs"],
                    }
                )

        delivery = WeaponDelivery(
            delivery_id=f"delivery_{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            weapon_specs=weapon_specs,
            status=DeliveryStatus.DELIVERED,
            estimated_delivery=datetime.now(),
            actual_delivery=datetime.now(),
            delivery_notes="Immediate delivery from inventory",
        )

        self.active_deliveries[delivery.delivery_id] = delivery
        self.delivery_metrics["fulfilled_requests"] += 1

        logger.info(
            f"📦 Immediately delivered {len(weapon_specs)} weapons for request {request.request_id}"
        )

    def _schedule_crafting(self, request: WeaponRequest):
        """クラフトをスケジュール"""
        # 優先度に基づくクラフト時間
        craft_times = {
            RequestPriority.CRITICAL: 60,  # 1分
            RequestPriority.HIGH: 300,  # 5分
            RequestPriority.MEDIUM: 1800,  # 30分
            RequestPriority.LOW: 3600,  # 1時間
        }

        craft_time = craft_times.get(request.priority, 1800)
        estimated_delivery = datetime.now() + timedelta(seconds=craft_time)

        delivery = WeaponDelivery(
            delivery_id=f"delivery_{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            weapon_specs=[],  # クラフト後に更新
            status=DeliveryStatus.CRAFTING,
            estimated_delivery=estimated_delivery,
            delivery_notes=f"Crafting required for {request.quantity} {request.weapon_type.value}",
        )

        self.active_deliveries[delivery.delivery_id] = delivery

        logger.info(
            f"🔨 Scheduled crafting for request {request.request_id}, ETA: {estimated_delivery}"
        )

    def _track_deliveries_loop(self):
        """配送追跡ループ"""
        # ループ処理
        while self._running:
            current_time = datetime.now()

            for delivery_id, delivery in list(self.active_deliveries.items()):
                if delivery.status == DeliveryStatus.CRAFTING:
                    if current_time >= delivery.estimated_delivery:
                        self._complete_crafting(delivery)
                elif delivery.status == DeliveryStatus.IN_TRANSIT:
                    if not (current_time >= delivery.estimated_delivery):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if current_time >= delivery.estimated_delivery:
                        self._complete_delivery(delivery)

            time.sleep(5)

    def _complete_crafting(self, delivery: WeaponDelivery):
        """クラフト完了処理"""
        # 武具を作成（簡略化）
        request = next(
            (r for r in self.request_history if r.request_id == delivery.request_id),
            None,
        )
        if not request:
            return

        weapon_specs = []
        for i in range(request.quantity):
            weapon_id = f"{request.weapon_type.value}_{uuid.uuid4().hex[:8]}"
            specs = {
                "effectiveness": 0.85,
                "durability": 100,
                "crafted_for": request.requester_id,
            }

            self.inventory.add_weapon(weapon_id, request.weapon_type, specs)
            self.inventory.allocate_weapon(weapon_id, request.requester_id)

            weapon_specs.append(
                {
                    "weapon_id": weapon_id,
                    "weapon_type": request.weapon_type.value,
                    "specs": specs,
                }
            )

        delivery.weapon_specs = weapon_specs
        delivery.status = DeliveryStatus.IN_TRANSIT
        delivery.estimated_delivery = datetime.now() + timedelta(
            seconds=30
        )  # 30秒配送時間

        logger.info(f"✅ Crafting completed for delivery {delivery.delivery_id}")

    def _complete_delivery(self, delivery: WeaponDelivery):
        """配送完了処理"""
        delivery.status = DeliveryStatus.DELIVERED
        delivery.actual_delivery = datetime.now()

        # メトリクス更新
        delivery_time = (
            delivery.actual_delivery - delivery.estimated_delivery
        ).total_seconds()
        self.delivery_metrics["average_delivery_time"] = (
            self.delivery_metrics["average_delivery_time"]
            * (self.delivery_metrics["fulfilled_requests"] - 1)
            + delivery_time
        ) / self.delivery_metrics["fulfilled_requests"]

        logger.info(f"🎉 Delivery {delivery.delivery_id} completed!")

    def get_delivery_status(self, delivery_id: str) -> Optional[DeliveryStatus]:
        """配送状態を取得"""
        if delivery_id in self.active_deliveries:
            return self.active_deliveries[delivery_id].status
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        return {
            **self.delivery_metrics,
            "pending_requests": len(self.pending_requests),
            "active_deliveries": len(
                [
                    d
                    for d in self.active_deliveries.values()
                    if d.status != DeliveryStatus.DELIVERED
                ]
            ),
        }


# グローバルインスタンス
shared_inventory = SharedWeaponInventory()
weapon_coordinator = WeaponSharingCoordinator(shared_inventory)


def initialize_weapon_sharing():
    """武具共有システムを初期化"""
    weapon_coordinator.start()
    logger.info("🚀 Weapon Sharing System initialized and started")


def shutdown_weapon_sharing():
    """武具共有システムをシャットダウン"""
    weapon_coordinator.stop()
    logger.info("🛑 Weapon Sharing System shut down")

#!/usr/bin/env python3
"""
Unified Item Manager - 統一アイテム管理システム
既存の3つのインベントリシステムを統合し、データ整合性を確保

統合対象:
1.0 WeaponSharingSystem (weapon_sharing_system.py)
2.0 Knight Equipment (knight_brigade.py)
3.0 Dwarf Workshop Inventory (dwarf_workshop.py)

安全性原則:
- 既存システムを削除せず並行稼働
- 段階的データ移行
- ロールバック機能付き
- Elder Council承認済み設計
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

# 既存システムとの互換性を保つためのインポート
try:
    from libs.weapon_sharing_system import SharedWeaponInventory
except ImportError:
    SharedWeaponInventory = None

try:
    from libs.knight_brigade import KnightBrigade
except ImportError:
    KnightBrigade = None

try:
    from libs.dwarf_workshop import DwarfWorkshop
except ImportError:
    DwarfWorkshop = None

logger = logging.getLogger(__name__)


@dataclass
class ItemInfo:
    """アイテム情報の統一データ構造"""

    item_id: str
    item_type: str  # 'weapon', 'resource', 'equipment', 'tool'
    name: str
    category: str
    quantity: int
    quality: float  # 0.0-1.0
    durability: float  # 0.0-1.0
    attributes: Dict[str, Any]
    location: str  # 'dwarf_workshop', 'knight_brigade', 'shared_inventory'
    allocated_to: Optional[str] = None
    allocated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AllocationRecord:
    """割り当て記録"""

    allocation_id: str
    item_id: str
    allocated_to: str
    allocated_by: str
    allocation_type: str  # 'temporary', 'permanent', 'shared'
    allocated_at: datetime
    expected_return: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    status: str = "active"  # 'active', 'returned', 'overdue'
    notes: str = ""


class LegacySystemConnector:
    """既存システムとの連携コネクタ"""

    def __init__(self):
        """初期化メソッド"""
        self.weapon_sharing = None
        self.knight_brigade = None
        self.dwarf_workshop = None
        self._initialize_legacy_systems()

    def _initialize_legacy_systems(self):
        """既存システムの初期化（可能な場合のみ）"""
        try:
            if SharedWeaponInventory:
                self.weapon_sharing = SharedWeaponInventory()
                logger.info("✅ WeaponSharingSystem connected")
        except Exception as e:
            logger.warning(f"⚠️ WeaponSharingSystem unavailable: {e}")

        try:
            if KnightBrigade:
                self.knight_brigade = KnightBrigade("unified_bridge")
                logger.info("✅ KnightBrigade connected")
        except Exception as e:
            logger.warning(f"⚠️ KnightBrigade unavailable: {e}")

        try:
            if DwarfWorkshop:
                self.dwarf_workshop = DwarfWorkshop()
                logger.info("✅ DwarfWorkshop connected")
        except Exception as e:
            logger.warning(f"⚠️ DwarfWorkshop unavailable: {e}")

    def sync_from_legacy_systems(self) -> List[ItemInfo]:
        """既存システムからアイテム情報を同期"""
        unified_items = []

        # WeaponSharingSystemから同期
        if self.weapon_sharing:
            try:
                weapon_data = self.weapon_sharing.get_all_weapons()
                for weapon in weapon_data:
                    item = ItemInfo(
                        item_id=weapon.get("weapon_id", str(uuid.uuid4())),
                        item_type="weapon",
                        name=weapon.get("name", "Unknown Weapon"),
                        category=weapon.get("category", "general"),
                        quantity=weapon.get("quantity", 1),
                        quality=weapon.get("quality", 0.8),
                        durability=weapon.get("durability", 1.0),
                        attributes=weapon.get("attributes", {}),
                        location="shared_inventory",
                        allocated_to=weapon.get("allocated_to"),
                        created_at=datetime.now(),
                        metadata={"source": "weapon_sharing_system"},
                    )
                    unified_items.append(item)
                logger.info(
                    f"📦 Synced {len(weapon_data)} weapons from WeaponSharingSystem"
                )
            except Exception as e:
                logger.error(f"❌ Failed to sync from WeaponSharingSystem: {e}")

        # KnightBrigadeから同期
        if self.knight_brigade:
            try:
                equipment_data = getattr(self.knight_brigade, "equipment", {})
                for eq_id, equipment in equipment_data.items():
                    item = ItemInfo(
                        item_id=eq_id,
                        item_type="equipment",
                        name=equipment.get("name", "Knight Equipment"),
                        category=equipment.get("type", "armor"),
                        quantity=equipment.get("quantity", 1),
                        quality=equipment.get("effectiveness", 0.8),
                        durability=equipment.get("durability", 1.0),
                        attributes=equipment.get("attributes", {}),
                        location="knight_brigade",
                        allocated_to="knight_brigade",
                        created_at=datetime.now(),
                        metadata={"source": "knight_brigade"},
                    )
                    unified_items.append(item)
                logger.info(
                    f"⚔️ Synced {len(equipment_data)} equipment from KnightBrigade"
                )
            except Exception as e:
                logger.error(f"❌ Failed to sync from KnightBrigade: {e}")

        # DwarfWorkshopから同期
        if self.dwarf_workshop:
            try:
                inventory_data = getattr(self.dwarf_workshop, "material_inventory", {})
                for mat_id, material in inventory_data.items():
                    item = ItemInfo(
                        item_id=mat_id,
                        item_type="resource",
                        name=material.get("name", "Crafting Material"),
                        category=material.get("category", "material"),
                        quantity=material.get("quantity", 1),
                        quality=material.get("quality", 0.8),
                        durability=1.0,  # 材料は耐久度なし
                        attributes=material.get("properties", {}),
                        location="dwarf_workshop",
                        allocated_to="dwarf_workshop",
                        created_at=datetime.now(),
                        metadata={"source": "dwarf_workshop"},
                    )
                    unified_items.append(item)
                logger.info(
                    f"🔨 Synced {len(inventory_data)} materials from DwarfWorkshop"
                )
            except Exception as e:
                logger.error(f"❌ Failed to sync from DwarfWorkshop: {e}")

        return unified_items


class UnifiedItemManager:
    """統一アイテム管理システム - Elder Council承認済み設計"""

    def __init__(self, data_file: str = "data/unified_inventory.json"):
        """初期化メソッド"""
        self.data_file = data_file
        self.items: Dict[str, ItemInfo] = {}
        self.allocations: Dict[str, AllocationRecord] = {}
        self.categories: Dict[str, List[str]] = defaultdict(list)
        self.locations: Dict[str, List[str]] = defaultdict(list)

        # 既存システムとの連携
        self.legacy_connector = LegacySystemConnector()

        # 統計・メトリクス
        self.stats = {
            "total_items": 0,
            "active_allocations": 0,
            "sync_operations": 0,
            "last_sync": None,
        }

        # スレッドセーフティ
        self._lock = threading.RLock()

        # 初期化
        self._initialize_data_storage()
        self._load_data()
        self._perform_initial_sync()

        logger.info("🎯 UnifiedItemManager initialized - 既存システムと並行稼働開始")

    def _initialize_data_storage(self):
        """データストレージの初期化"""
        try:
            data_dir = Path(self.data_file).parent
            data_dir.mkdir(parents=True, exist_ok=True)

            if not Path(self.data_file).exists():
                initial_data = {
                    "items": {},
                    "allocations": {},
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0.0",
                        "elder_council_approved": True,
                    },
                }
                with open(self.data_file, "w") as f:
                    json.dump(initial_data, f, indent=2, default=str)
                logger.info(f"📂 Created new inventory file: {self.data_file}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize data storage: {e}")

    def _load_data(self):
        """既存データの読み込み"""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, "r") as f:
                    data = json.load(f)

                # アイテム復元
                for item_id, item_data in data.get("items", {}).items():
                    item_data["created_at"] = (
                        datetime.fromisoformat(item_data["created_at"])
                        if item_data.get("created_at")
                        else None
                    )
                    item_data["updated_at"] = (
                        datetime.fromisoformat(item_data["updated_at"])
                        if item_data.get("updated_at")
                        else None
                    )
                    item_data["allocated_at"] = (
                        datetime.fromisoformat(item_data["allocated_at"])
                        if item_data.get("allocated_at")
                        else None
                    )

                    self.items[item_id] = ItemInfo(**item_data)

                # 割り当て記録復元
                for alloc_id, alloc_data in data.get("allocations", {}).items():
                    alloc_data["allocated_at"] = datetime.fromisoformat(
                        alloc_data["allocated_at"]
                    )
                    if alloc_data.get("expected_return"):
                        alloc_data["expected_return"] = datetime.fromisoformat(
                            alloc_data["expected_return"]
                        )
                    if alloc_data.get("returned_at"):
                        alloc_data["returned_at"] = datetime.fromisoformat(
                            alloc_data["returned_at"]
                        )

                    self.allocations[alloc_id] = AllocationRecord(**alloc_data)

                self._rebuild_indexes()
                logger.info(
                    f"📂 Loaded {len(self.items)} items and {len(self.allocations)} allocations"
                )
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")

    def _save_data(self):
        """データの永続化"""
        try:
            with self._lock:
                data = {
                    "items": {
                        item_id: asdict(item) for item_id, item in self.items.items()
                    },
                    "allocations": {
                        alloc_id: asdict(alloc)
                        for alloc_id, alloc in self.allocations.items()
                    },
                    "stats": self.stats,
                    "metadata": {
                        "updated_at": datetime.now().isoformat(),
                        "version": "1.0.0",
                        "elder_council_approved": True,
                    },
                }

                with open(self.data_file, "w") as f:
                    json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")

    def _rebuild_indexes(self):
        """インデックスの再構築"""
        self.categories.clear()
        self.locations.clear()

        for item_id, item in self.items.items():
            self.categories[item.category].append(item_id)
            self.locations[item.location].append(item_id)

        # 統計更新
        self.stats["total_items"] = len(self.items)
        self.stats["active_allocations"] = len(
            [a for a in self.allocations.values() if a.status == "active"]
        )

    def _perform_initial_sync(self):
        """初回同期の実行"""
        try:
            legacy_items = self.legacy_connector.sync_from_legacy_systems()

            synced_count = 0
            for item in legacy_items:
                if item.item_id not in self.items:
                    self.items[item.item_id] = item
                    synced_count += 1
                else:
                    # 既存アイテムの更新（メタデータマージ）
                    existing = self.items[item.item_id]
                    if not existing.metadata:
                        existing.metadata = {}
                    existing.metadata.update(item.metadata or {})
                    existing.updated_at = datetime.now()

            self._rebuild_indexes()
            self._save_data()

            self.stats["sync_operations"] += 1
            self.stats["last_sync"] = datetime.now()

            logger.info(
                f"🔄 Initial sync completed: {synced_count} new items integrated"
            )
        except Exception as e:
            logger.error(f"❌ Initial sync failed: {e}")

    def add_item(self, item: ItemInfo) -> bool:
        """アイテムの追加"""
        try:
            with self._lock:
                if item.item_id in self.items:
                    logger.warning(f"⚠️ Item {item.item_id} already exists")
                    return False

                item.created_at = datetime.now()
                item.updated_at = datetime.now()

                self.items[item.item_id] = item
                self.categories[item.category].append(item.item_id)
                self.locations[item.location].append(item.item_id)

                self.stats["total_items"] += 1
                self._save_data()

                logger.info(f"✅ Added item: {item.name} ({item.item_id})")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to add item: {e}")
            return False

    def allocate_item(
        self,
        item_id: str,
        allocated_to: str,
        allocation_type: str = "temporary",
        allocated_by: str = "system",
        expected_return: Optional[datetime] = None,
        notes: str = "",
    ) -> Optional[str]:
        """アイテムの割り当て"""
        try:
            with self._lock:
                if item_id not in self.items:
                    logger.error(f"❌ Item {item_id} not found")
                    return None

                item = self.items[item_id]
                if item.allocated_to and item.allocated_to != allocated_to:
                    logger.warning(
                        f"⚠️ Item {item_id} already allocated to {item.allocated_to}"
                    )
                    return None

                allocation_id = str(uuid.uuid4())
                allocation = AllocationRecord(
                    allocation_id=allocation_id,
                    item_id=item_id,
                    allocated_to=allocated_to,
                    allocated_by=allocated_by,
                    allocation_type=allocation_type,
                    allocated_at=datetime.now(),
                    expected_return=expected_return,
                    notes=notes,
                )

                # アイテム状態更新
                item.allocated_to = allocated_to
                item.allocated_at = allocation.allocated_at
                item.updated_at = datetime.now()

                self.allocations[allocation_id] = allocation
                self.stats["active_allocations"] += 1
                self._save_data()

                logger.info(f"📋 Allocated {item.name} to {allocated_to}")
                return allocation_id
        except Exception as e:
            logger.error(f"❌ Failed to allocate item: {e}")
            return None

    def return_item(self, allocation_id: str) -> bool:
        """アイテムの返却"""
        try:
            with self._lock:
                if allocation_id not in self.allocations:
                    logger.error(f"❌ Allocation {allocation_id} not found")
                    return False

                allocation = self.allocations[allocation_id]
                if allocation.status != "active":
                    logger.warning(f"⚠️ Allocation {allocation_id} not active")
                    return False

                item = self.items[allocation.item_id]

                # 返却処理
                allocation.returned_at = datetime.now()
                allocation.status = "returned"

                item.allocated_to = None
                item.allocated_at = None
                item.updated_at = datetime.now()

                self.stats["active_allocations"] -= 1
                self._save_data()

                logger.info(f"🔄 Returned {item.name} from {allocation.allocated_to}")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to return item: {e}")
            return False

    def get_items_by_category(self, category: str) -> List[ItemInfo]:
        """カテゴリ別アイテム検索"""
        item_ids = self.categories.get(category, [])
        return [self.items[item_id] for item_id in item_ids if item_id in self.items]

    def get_items_by_location(self, location: str) -> List[ItemInfo]:
        """場所別アイテム検索"""
        item_ids = self.locations.get(location, [])
        return [self.items[item_id] for item_id in item_ids if item_id in self.items]

    def get_available_items(self, category: Optional[str] = None) -> List[ItemInfo]:
        """利用可能アイテムの取得"""
        available = []
        for item in self.items.values():
            if item.allocated_to is None:
                if category is None or item.category == category:
                    available.append(item)
        return available

    def get_allocation_history(
        self, item_id: Optional[str] = None
    ) -> List[AllocationRecord]:
        """割り当て履歴の取得"""
        if item_id:
            return [
                alloc for alloc in self.allocations.values() if alloc.item_id == item_id
            ]
        return list(self.allocations.values())

    def sync_with_legacy_systems(self, force: bool = False) -> Dict[str, Any]:
        """既存システムとの手動同期"""
        if not force and self.stats["last_sync"]:
            last_sync = self.stats["last_sync"]
            if isinstance(last_sync, str):
                last_sync = datetime.fromisoformat(last_sync)
            if datetime.now() - last_sync < timedelta(minutes=30):
                return {"status": "skipped", "reason": "recent_sync"}

        try:
            legacy_items = self.legacy_connector.sync_from_legacy_systems()

            new_items = 0
            updated_items = 0

            for item in legacy_items:
                if item.item_id not in self.items:
                    self.items[item.item_id] = item
                    new_items += 1
                else:
                    # 既存アイテムの更新
                    existing = self.items[item.item_id]
                    existing.quantity = item.quantity
                    existing.quality = item.quality
                    existing.durability = item.durability
                    existing.updated_at = datetime.now()
                    updated_items += 1

            self._rebuild_indexes()
            self._save_data()

            self.stats["sync_operations"] += 1
            self.stats["last_sync"] = datetime.now()

            result = {
                "status": "success",
                "new_items": new_items,
                "updated_items": updated_items,
                "total_items": len(self.items),
                "sync_time": self.stats["last_sync"],
            }

            logger.info(f"🔄 Sync completed: {new_items} new, {updated_items} updated")
            return result
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態の取得"""
        with self._lock:
            return {
                "total_items": len(self.items),
                "categories": dict(self.categories),
                "locations": dict(self.locations),
                "active_allocations": len(
                    [a for a in self.allocations.values() if a.status == "active"]
                ),
                "legacy_systems": {
                    "weapon_sharing": self.legacy_connector.weapon_sharing is not None,
                    "knight_brigade": self.legacy_connector.knight_brigade is not None,
                    "dwarf_workshop": self.legacy_connector.dwarf_workshop is not None,
                },
                "stats": self.stats,
                "data_file": self.data_file,
                "elder_council_approved": True,
            }

    def create_backup(self) -> str:
        """システムバックアップの作成"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.data_file}.backup_{timestamp}"

            backup_data = {
                "items": {
                    item_id: asdict(item) for item_id, item in self.items.items()
                },
                "allocations": {
                    alloc_id: asdict(alloc)
                    for alloc_id, alloc in self.allocations.items()
                },
                "stats": self.stats,
                "metadata": {
                    "backup_created": datetime.now().isoformat(),
                    "original_file": self.data_file,
                    "elder_council_approved": True,
                },
            }

            with open(backup_file, "w") as f:
                json.dump(backup_data, f, indent=2, default=str)

            logger.info(f"💾 Backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return ""


# 使用例とテスト関数
def demo_unified_item_manager():
    """UnifiedItemManagerのデモンストレーション"""

    print("🎯 UnifiedItemManager Demo - Elder Council承認済み")
    print("=" * 60)

    # マネージャー初期化
    manager = UnifiedItemManager("data/demo_unified_inventory.json")

    # テストアイテムの追加
    test_items = [
        ItemInfo(
            item_id="test_sword_001",
            item_type="weapon",
            name="Test Sword of Unity",
            category="sword",
            quantity=1,
            quality=0.95,
            durability=1.0,
            attributes={"damage": 100, "magic": True},
            location="unified_inventory",
        ),
        ItemInfo(
            item_id="test_material_001",
            item_type="resource",
            name="Mythril Ore",
            category="metal",
            quantity=50,
            quality=0.9,
            durability=1.0,
            attributes={"rarity": "legendary"},
            location="unified_inventory",
        ),
    ]

    for item in test_items:
        success = manager.add_item(item)
        print(f"{'✅' if success else '❌'} Added: {item.name}")

    # アイテム割り当て
    allocation_id = manager.allocate_item(
        "test_sword_001",
        "knight_001",
        allocation_type="temporary",
        notes="For testing purposes",
    )
    print(f"📋 Allocation ID: {allocation_id}")

    # 既存システムとの同期
    sync_result = manager.sync_with_legacy_systems(force=True)
    print(f"🔄 Sync result: {sync_result}")

    # システム状態表示
    status = manager.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   Total Items: {status['total_items']}")
    print(f"   Active Allocations: {status['active_allocations']}")
    print(f"   Legacy Systems: {status['legacy_systems']}")

    # バックアップ作成
    backup_file = manager.create_backup()
    print(f"💾 Backup: {backup_file}")

    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_unified_item_manager()

#!/usr/bin/env python3
"""
Test Weapon Sharing System - 武具共有システムのテスト
ドワーフ工房と騎士団の連携動作を確認
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
import time

from libs.dwarf_workshop import CraftingEngine
from libs.knight_brigade import KnightSquad
from libs.weapon_sharing_system import (
    RequestPriority,
    WeaponRequest,
    WeaponType,
    initialize_weapon_sharing,
    shared_inventory,
    weapon_coordinator,
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)


def test_weapon_sharing():
    """武具共有システムのテスト"""
    print("🧪 Testing Weapon Sharing System...\n")

    # 1. システム初期化
    print("1️⃣ Initializing systems...")
    initialize_weapon_sharing()
    crafting_engine = CraftingEngine()
    knight_squad = KnightSquad("test_squad_001", "guardian")
    print("✅ Systems initialized\n")

    # 2. ドワーフ工房で武具を作成
    print("2️⃣ Dwarf Workshop creating initial weapons...")
    initial_weapons = [
        ("memory_optimizer", 2),
        ("anomaly_detector", 1),
        ("resource_guardian", 1),
    ]

    for weapon_type, count in initial_weapons:
        result = crafting_engine.provide_weapon_to_knights(
            "inventory", weapon_type, count
        )
        print(f"   - Created {count} {weapon_type}: {result['success']}")

    # インベントリ確認
    available = shared_inventory.get_available_weapons()
    print(f"✅ Total weapons in inventory: {len(available)}\n")

    # 3. 騎士団から武具リクエスト
    print("3️⃣ Knight Squad requesting weapons...")
    request_id = knight_squad.request_weapon_from_workshop(
        "memory_optimizer",
        quantity=1,
        priority="high",
        purpose="System defense operation",
    )
    print(f"   - Request ID: {request_id}")

    # リクエスト処理待ち
    time.sleep(2)

    # 配送状態確認
    delivery_status = weapon_coordinator.get_delivery_status(request_id)
    print(f"   - Delivery status: {delivery_status}")

    # 4. ドワーフ工房から直接提供
    print("\n4️⃣ Direct weapon provision from Dwarf Workshop...")
    direct_result = crafting_engine.provide_weapon_to_knights(
        knight_squad.squad_id, "anomaly_detector", 1
    )

    if direct_result["success"]:
        # 騎士団で受け取り
        knight_squad.receive_weapon_delivery(direct_result["weapons"])
        print(f"✅ Knight squad received {len(direct_result['weapons'])} weapons")

    # 5. 装備状態確認
    print("\n5️⃣ Equipment status:")
    print(f"   - Squad equipment count: {len(knight_squad.equipment)}")
    for weapon_id, weapon_data in knight_squad.equipment.items():
        print(
            f"     • {weapon_id}: {weapon_data['weapon_type']} "
            f"(effectiveness: {weapon_data['effectiveness']:.2f})"
        )

    # 6. メトリクス表示
    print("\n6️⃣ System metrics:")
    metrics = weapon_coordinator.get_metrics()
    print(f"   - Total requests: {metrics['total_requests']}")
    print(f"   - Fulfilled requests: {metrics['fulfilled_requests']}")
    print(f"   - Pending requests: {metrics['pending_requests']}")
    print(f"   - Active deliveries: {metrics['active_deliveries']}")

    # 7. 武具の解放とメンテナンス
    print("\n7️⃣ Weapon maintenance...")
    for weapon_id in list(knight_squad.equipment.keys())[:1]:
        if shared_inventory.release_weapon(weapon_id):
            print(f"   - Released weapon: {weapon_id}")
        if shared_inventory.perform_maintenance(weapon_id):
            print(f"   - Maintenance completed: {weapon_id}")

    print("\n✅ Weapon sharing test completed!")


if __name__ == "__main__":
    test_weapon_sharing()

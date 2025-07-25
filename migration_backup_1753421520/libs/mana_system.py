#!/usr/bin/env python3
"""
マナシステム - 5大契約精霊のエネルギー管理
エルダー評議会の契約精霊たちの活動エネルギーを管理
"""

import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManaSystem:
    """5大契約精霊のマナ（エネルギー）管理システム"""

    def __init__(self):
        """初期化メソッド"""
        # マナの初期値と最大値
        self.max_mana = 100
        self.mana_regen_rate = 0.5  # 毎秒の回復量

        # 5大契約精霊のマナ状態
        self.spirit_mana = {
            "will": {  # 意思の大精霊
                "current": 100,
                "max": 100,
                "regen_rate": 0.8,  # 戦略的決断力の回復が早い
                "drain_rate": 0.2,  # 消費も激しい
                "last_update": time.time(),
                "status": "active",
                "color": "#FFD700",  # ゴールド
            },
            "wisdom": {  # 叡智の大精霊
                "current": 100,
                "max": 100,
                "regen_rate": 0.3,  # ゆっくり回復
                "drain_rate": 0.1,  # 消費も少ない
                "last_update": time.time(),
                "status": "active",
                "color": "#4169E1",  # ロイヤルブルー
            },
            "peace": {  # 平和の大精霊
                "current": 100,
                "max": 100,
                "regen_rate": 0.4,
                "drain_rate": 0.15,
                "last_update": time.time(),
                "status": "active",
                "color": "#32CD32",  # ライムグリーン
            },
            "creation": {  # 創造の大精霊
                "current": 100,
                "max": 100,
                "regen_rate": 0.6,  # 創造力は変動が激しい
                "drain_rate": 0.25,
                "last_update": time.time(),
                "status": "active",
                "color": "#FF6347",  # トマトレッド
            },
            "harmony": {  # 調和の大精霊
                "current": 100,
                "max": 100,
                "regen_rate": 0.5,
                "drain_rate": 0.1,
                "last_update": time.time(),
                "status": "active",
                "color": "#87CEEB",  # スカイブルー
            },
        }

        # マナ消費イベント履歴
        self.mana_history = []

        # 精霊活動によるマナ変動
        self.activity_drain = {
            "decision_making": 5,  # 意思決定
            "knowledge_search": 3,  # 知識検索
            "security_check": 4,  # セキュリティチェック
            "innovation": 6,  # 革新的提案
            "balancing": 2,  # バランス調整
        }

        logger.info("マナシステムを初期化しました")

    def update_mana(self) -> None:
        """全精霊のマナを更新（回復・消費計算）"""
        current_time = time.time()

        for spirit_name, spirit_data in self.spirit_mana.items():
            time_diff = current_time - spirit_data["last_update"]

            # 自然回復
            regen_amount = spirit_data["regen_rate"] * time_diff

            # ランダムな活動による消費（シミュレーション）
            if random.random() < 0.1:  # 10%の確率で活動
                drain_amount = (
                    spirit_data["drain_rate"] * time_diff * random.uniform(5, 15)
                )
                spirit_data["current"] -= drain_amount

                # 履歴記録
                self.mana_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "spirit": spirit_name,
                        "type": "drain",
                        "amount": drain_amount,
                        "reason": "spirit_activity",
                    }
                )

            # マナ回復
            spirit_data["current"] = min(
                spirit_data["current"] + regen_amount, spirit_data["max"]
            )

            # マナが0以下になったら休眠状態
            if spirit_data["current"] <= 0:
                spirit_data["current"] = 0
                spirit_data["status"] = "dormant"
            elif spirit_data["current"] < 30:
                spirit_data["status"] = "exhausted"
            elif spirit_data["current"] < 60:
                spirit_data["status"] = "tired"
            else:
                spirit_data["status"] = "active"

            spirit_data["last_update"] = current_time

    def get_all_mana_status(self) -> Dict[str, Any]:
        """全精霊のマナ状態を取得"""
        self.update_mana()

        status = {
            "timestamp": datetime.now().isoformat(),
            "spirits": {},
            "overall_health": 0,
            "alerts": [],
        }

        total_mana = 0
        total_max = 0

        for spirit_name, spirit_data in self.spirit_mana.items():
            mana_percentage = (spirit_data["current"] / spirit_data["max"]) * 100

            status["spirits"][spirit_name] = {
                "name": self._get_spirit_japanese_name(spirit_name),
                "current": round(spirit_data["current"], 2),
                "max": spirit_data["max"],
                "percentage": round(mana_percentage, 1),
                "status": spirit_data["status"],
                "color": spirit_data["color"],
                "regen_rate": spirit_data["regen_rate"],
                "drain_rate": spirit_data["drain_rate"],
            }

            total_mana += spirit_data["current"]
            total_max += spirit_data["max"]

            # アラート判定
            if spirit_data["status"] == "dormant":
                status["alerts"].append(
                    {
                        "level": "critical",
                        "spirit": spirit_name,
                        "message": f"{self._get_spirit_japanese_name(spirit_name)}が休眠状態です！",
                    }
                )
            elif spirit_data["status"] == "exhausted":
                status["alerts"].append(
                    {
                        "level": "warning",
                        "spirit": spirit_name,
                        "message": f"{self._get_spirit_japanese_name(spirit_name)}が疲弊状態です",
                    }
                )

        # 全体の健全性
        status["overall_health"] = round((total_mana / total_max) * 100, 1)

        # 警告レベル判定
        if status["overall_health"] < 30:
            status["system_alert"] = "critical"
        elif status["overall_health"] < 60:
            status["system_alert"] = "warning"
        else:
            status["system_alert"] = "normal"

        return status

    def consume_mana(self, spirit: str, amount: float, reason: str) -> Dict[str, Any]:
        """特定の精霊のマナを消費"""
        if spirit not in self.spirit_mana:
            return {"success": False, "error": f"Unknown spirit: {spirit}"}

        self.update_mana()

        spirit_data = self.spirit_mana[spirit]
        if spirit_data["current"] < amount:
            return {
                "success": False,
                "error": f"Insufficient mana: {spirit_data['current']} < {amount}",
            }

        # マナ消費
        spirit_data["current"] -= amount

        # 履歴記録
        self.mana_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "spirit": spirit,
                "type": "consume",
                "amount": amount,
                "reason": reason,
            }
        )

        return {
            "success": True,
            "spirit": spirit,
            "consumed": amount,
            "remaining": round(spirit_data["current"], 2),
            "reason": reason,
        }

    def restore_mana(self, spirit: str, amount: float) -> Dict[str, Any]:
        """特定の精霊のマナを回復"""
        if spirit not in self.spirit_mana:
            return {"success": False, "error": f"Unknown spirit: {spirit}"}

        spirit_data = self.spirit_mana[spirit]
        before = spirit_data["current"]
        spirit_data["current"] = min(
            spirit_data["current"] + amount, spirit_data["max"]
        )
        restored = spirit_data["current"] - before

        # 履歴記録
        self.mana_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "spirit": spirit,
                "type": "restore",
                "amount": restored,
                "reason": "manual_restore",
            }
        )

        return {
            "success": True,
            "spirit": spirit,
            "restored": round(restored, 2),
            "current": round(spirit_data["current"], 2),
            "max": spirit_data["max"],
        }

    def get_mana_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """マナ変動履歴を取得"""
        return self.mana_history[-limit:]

    def _get_spirit_japanese_name(self, spirit: str) -> str:
        """精霊の日本語名を取得"""
        names = {
            "will": "意思の大精霊",
            "wisdom": "叡智の大精霊",
            "peace": "平和の大精霊",
            "creation": "創造の大精霊",
            "harmony": "調和の大精霊",
        }
        return names.get(spirit, spirit)

    def simulate_council_meeting(self, duration: int = 300) -> Dict[str, Any]:
        """評議会開催をシミュレート（マナ消費）"""
        self.update_mana()

        meeting_result = {
            "start_time": datetime.now().isoformat(),
            "duration": duration,
            "mana_consumed": {},
            "decisions_made": 0,
        }

        # 各精霊の活動によるマナ消費
        activities = [
            ("will", 15, "strategic_decision"),
            ("wisdom", 10, "knowledge_consultation"),
            ("peace", 8, "safety_assessment"),
            ("creation", 12, "innovation_proposal"),
            ("harmony", 5, "balance_adjustment"),
        ]

        for spirit, consumption, reason in activities:
            result = self.consume_mana(spirit, consumption, f"council_meeting_{reason}")
            if result["success"]:
                meeting_result["mana_consumed"][spirit] = consumption
                meeting_result["decisions_made"] += 1

        meeting_result["end_time"] = datetime.now().isoformat()
        return meeting_result

    def emergency_mana_boost(self) -> Dict[str, Any]:
        """緊急時の全精霊マナブースト"""
        boost_result = {"timestamp": datetime.now().isoformat(), "spirits_boosted": {}}

        for spirit in self.spirit_mana.keys():
            result = self.restore_mana(spirit, 50)
            boost_result["spirits_boosted"][spirit] = result["restored"]

        return boost_result


# グローバルインスタンス
mana_system = ManaSystem()

if __name__ == "__main__":
    # テスト実行
    print("🔮 マナシステムテスト")
    print("=" * 50)

    # 初期状態
    status = mana_system.get_all_mana_status()
    print(f"初期マナ状態:")
    for spirit, data in status["spirits"].items():
        print(
            f"  {data['name']}: {data['current']}/{data['max']} ({data['percentage']}%)"
        )

    # 評議会シミュレーション
    print("\n📋 評議会開催シミュレーション...")
    meeting = mana_system.simulate_council_meeting()
    print(f"決定事項数: {meeting['decisions_made']}")
    print(f"消費マナ: {meeting['mana_consumed']}")

    # 消費後の状態
    status = mana_system.get_all_mana_status()
    print(f"\n評議会後のマナ状態:")
    for spirit, data in status["spirits"].items():
        print(
            f"  {data['name']}: {data['current']}/{data['max']} ({data['percentage']}%)"
        )

    print(f"\nシステム全体健全性: {status['overall_health']}%")
    print(f"アラート数: {len(status['alerts'])}")

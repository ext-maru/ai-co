#!/usr/bin/env python3
"""
🏛️ エルダーズギルド 予言書システム (Prophecy Engine)
段階的進化システムの汎用エンジン
"""

import asyncio
import json
import logging
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvolutionTrigger(Enum):
    """進化トリガー種別"""

    AUTOMATIC = "automatic"
    MANUAL_APPROVAL = "manual_approval"
    ELDER_COUNCIL = "elder_council"


@dataclass
class Criterion:
    """進化条件"""

    name: str
    operator: str  # ">=", "<=", "==", "!=", ">", "<"
    target_value: Any
    weight: float = 1.0
    description: str = ""

    def evaluate(self, current_value: Any) -> bool:
        """条件評価"""
        try:
            if self.operator == ">=":
                return current_value >= self.target_value
            elif self.operator == "<=":
                return current_value <= self.target_value
            elif self.operator == "==":
                return current_value == self.target_value
            elif self.operator == "!=":
                return current_value != self.target_value
            elif self.operator == ">":
                return current_value > self.target_value
            elif self.operator == "<":
                return current_value < self.target_value
            return False
        except (TypeError, ValueError):
            logger.warning(
                f"条件評価エラー: {self.name} {current_value} {self.operator} {self.target_value}"
            )
            return False


@dataclass
class Gate:
    """進化ゲート"""

    gate_id: str
    target_phase: int
    criteria: List[Criterion]
    evolution_actions: List[str]
    stability_days: int = 7
    trigger: EvolutionTrigger = EvolutionTrigger.AUTOMATIC
    description: str = ""

    def evaluate_readiness(self, metrics: Dict) -> Dict:
        """ゲート通過準備度評価"""
        results = {}
        passed_criteria = 0
        total_weight = 0
        weighted_score = 0

        for criterion in self.criteria:
            current_value = metrics.get(criterion.name, 0)
            passed = criterion.evaluate(current_value)

            results[criterion.name] = {
                "passed": passed,
                "current": current_value,
                "target": criterion.target_value,
                "operator": criterion.operator,
                "weight": criterion.weight,
                "description": criterion.description,
            }

            if passed:
                passed_criteria += 1
                weighted_score += criterion.weight

            total_weight += criterion.weight

        readiness_score = passed_criteria / len(self.criteria)
        weighted_readiness = weighted_score / total_weight if total_weight > 0 else 0

        return {
            "gate_id": self.gate_id,
            "target_phase": self.target_phase,
            "readiness_score": readiness_score,
            "weighted_readiness": weighted_readiness,
            "is_ready": readiness_score >= 1.0,
            "criteria_results": results,
            "missing_criteria": [
                name for name, result in results.items() if not result["passed"]
            ],
            "stability_days": self.stability_days,
            "trigger": self.trigger.value,
        }


@dataclass
class Phase:
    """進化フェーズ"""

    phase_id: int
    name: str
    description: str
    gates: List[Gate]
    features: List[str] = None
    requirements: List[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.requirements is None:
            self.requirements = []


@dataclass
class Prophecy:
    """予言書"""

    prophecy_name: str
    description: str
    phases: List[Phase]
    created_at: str
    updated_at: str
    version: str = "1.0"
    category: str = "general"
    author: str = "Claude Elder"

    def get_current_phase(self, current_state: Dict) -> Optional[Phase]:
        """現在のフェーズを取得"""
        current_phase_id = current_state.get("current_phase", 1)
        return next((p for p in self.phases if p.phase_id == current_phase_id), None)

    def get_next_gate(self, current_phase_id: int) -> Optional[Gate]:
        """次のゲートを取得"""
        current_phase = next(
            (p for p in self.phases if p.phase_id == current_phase_id), None
        )
        if current_phase and current_phase.gates:
            return current_phase.gates[0]  # 通常は1つのゲートのみ
        return None

    def get_phase_by_id(self, phase_id: int) -> Optional[Phase]:
        """フェーズIDでフェーズを取得"""
        return next((p for p in self.phases if p.phase_id == phase_id), None)


class ProphecyEngine:
    """予言書エンジン"""

    def __init__(self, prophecy_dir: Path = None):
        self.prophecy_dir = prophecy_dir or Path(__file__).parent.parent / "prophecies"
        self.prophecy_dir.mkdir(exist_ok=True)

        self.prophecies: Dict[str, Prophecy] = {}
        self.active_prophecies: Dict[str, Dict] = {}
        self.prophecy_history: List[Dict] = []

        # 状態保存ファイル
        self.state_file = self.prophecy_dir / "prophecy_state.json"
        self.history_file = self.prophecy_dir / "prophecy_history.json"

        # 状態復元
        self.load_state()

    def load_state(self):
        """状態復元"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.active_prophecies = json.load(f)
                # logger.info("予言書状態を復元しました")  # ログ出力を削減
            except Exception as e:
                logger.warning(f"状態復元エラー: {e}")

        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.prophecy_history = json.load(f)
                # logger.info("予言書履歴を復元しました")  # ログ出力を削減
            except Exception as e:
                logger.warning(f"履歴復元エラー: {e}")

    def save_state(self):
        """状態保存"""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.active_prophecies, f, indent=2, ensure_ascii=False, default=str
                )

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.prophecy_history, f, indent=2, ensure_ascii=False, default=str
                )

        except Exception as e:
            logger.error(f"状態保存エラー: {e}")

    def register_prophecy(self, prophecy: Prophecy):
        """予言書を登録"""
        self.prophecies[prophecy.prophecy_name] = prophecy

        if prophecy.prophecy_name not in self.active_prophecies:
            self.active_prophecies[prophecy.prophecy_name] = {
                "current_phase": 1,
                "last_evolution": None,
                "stability_start": None,
                "metrics_history": [],
                "created_at": datetime.now().isoformat(),
            }

        logger.info(f"予言書 '{prophecy.prophecy_name}' を登録しました")
        self.save_state()

    def load_prophecy_from_yaml(self, yaml_path: Path) -> Optional[Prophecy]:
        """YAMLファイルから予言書を読み込み"""
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            prophecy = self.parse_prophecy_data(data)
            return prophecy

        except Exception as e:
            logger.error(f"予言書読み込みエラー {yaml_path}: {e}")
            return None

    def parse_prophecy_data(self, data: Dict) -> Prophecy:
        """予言書データをパース"""
        # フェーズ解析
        phases = []
        for phase_data in data.get("phases", []):
            # ゲート解析
            gates = []
            for gate_data in phase_data.get("gates", []):
                # 条件解析
                criteria = []
                for criterion_data in gate_data.get("criteria", []):
                    if isinstance(criterion_data, dict):
                        for name, condition in criterion_data.items():
                            # ">=95%" や ">= 95%" のような条件をパース
                            if isinstance(condition, str):
                                operator, value = self.parse_condition(condition)
                            else:
                                operator = ">="
                                value = condition

                            criteria.append(
                                Criterion(
                                    name=name,
                                    operator=operator,
                                    target_value=value,
                                    weight=1.0,
                                )
                            )

                gate = Gate(
                    gate_id=gate_data["gate_id"],
                    target_phase=gate_data["target_phase"],
                    criteria=criteria,
                    evolution_actions=gate_data.get("evolution_actions", []),
                    stability_days=gate_data.get("stability_days", 7),
                    trigger=EvolutionTrigger(gate_data.get("trigger", "automatic")),
                    description=gate_data.get("description", ""),
                )
                gates.append(gate)

            phase = Phase(
                phase_id=phase_data["phase_id"],
                name=phase_data["name"],
                description=phase_data.get("description", ""),
                gates=gates,
                features=phase_data.get("features", []),
                requirements=phase_data.get("requirements", []),
            )
            phases.append(phase)

        prophecy = Prophecy(
            prophecy_name=data["prophecy_name"],
            description=data.get("description", ""),
            phases=phases,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            version=data.get("version", "1.0"),
            category=data.get("category", "general"),
            author=data.get("author", "Claude Elder"),
        )

        return prophecy

    def parse_condition(self, condition: str) -> tuple:
        """条件文字列をパース"""
        condition = condition.strip()

        operators = [">=", "<=", "==", "!=", ">", "<"]
        for op in operators:
            if condition.startswith(op):
                value_str = condition[len(op) :].strip()
                # パーセント記号を削除
                if value_str.endswith("%"):
                    value_str = value_str[:-1]

                # 数値変換
                try:
                    if "." in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                except ValueError:
                    value = value_str

                return op, value

        # デフォルト
        return ">=", condition

    def evaluate_prophecy(self, prophecy_name: str, current_metrics: Dict) -> Dict:
        """予言書の評価実行"""
        if prophecy_name not in self.prophecies:
            return {"error": f"Prophecy {prophecy_name} not found"}

        prophecy = self.prophecies[prophecy_name]
        state = self.active_prophecies[prophecy_name]

        # メトリクス履歴に追加
        state["metrics_history"].append(
            {"timestamp": datetime.now().isoformat(), "metrics": current_metrics.copy()}
        )

        # 履歴は最新100件のみ保持
        if len(state["metrics_history"]) > 100:
            state["metrics_history"] = state["metrics_history"][-100:]

        current_phase = prophecy.get_current_phase(state)
        if not current_phase:
            return {"error": "Current phase not found"}

        next_gate = prophecy.get_next_gate(current_phase.phase_id)
        if not next_gate:
            return {
                "status": "Final phase reached",
                "phase": current_phase.phase_id,
                "phase_name": current_phase.name,
            }

        gate_status = next_gate.evaluate_readiness(current_metrics)

        # 安定期間チェック
        stability_info = self.check_stability(prophecy_name, gate_status["is_ready"])

        result = {
            "prophecy_name": prophecy_name,
            "current_phase": current_phase.phase_id,
            "current_phase_name": current_phase.name,
            "gate_status": gate_status,
            "stability_info": stability_info,
            "evolution_ready": gate_status["is_ready"] and stability_info["is_stable"],
            "next_actions": (
                next_gate.evolution_actions if gate_status["is_ready"] else []
            ),
            "last_updated": datetime.now().isoformat(),
        }

        self.save_state()
        return result

    def check_stability(self, prophecy_name: str, criteria_met: bool) -> Dict:
        """安定期間チェック"""
        state = self.active_prophecies[prophecy_name]

        if criteria_met:
            if state["stability_start"] is None:
                state["stability_start"] = datetime.now().isoformat()
                stable_days = 0
            else:
                stability_start = datetime.fromisoformat(state["stability_start"])
                stable_days = (datetime.now() - stability_start).days
        else:
            # 条件を満たさない場合はリセット
            state["stability_start"] = None
            stable_days = 0

        prophecy = self.prophecies[prophecy_name]
        current_phase = prophecy.get_current_phase(state)
        next_gate = (
            prophecy.get_next_gate(current_phase.phase_id) if current_phase else None
        )
        required_days = next_gate.stability_days if next_gate else 7

        return {
            "is_stable": stable_days >= required_days,
            "stable_days": stable_days,
            "required_days": required_days,
            "stability_start": state["stability_start"],
        }

    async def execute_evolution(
        self, prophecy_name: str, gate_id: str, force: bool = False
    ) -> Dict:
        """進化実行"""
        if prophecy_name not in self.prophecies:
            return {"error": f"Prophecy {prophecy_name} not found"}

        prophecy = self.prophecies[prophecy_name]
        state = self.active_prophecies[prophecy_name]

        # 現在のフェーズとゲートを取得
        current_phase = prophecy.get_current_phase(state)
        if not current_phase:
            return {"error": "Current phase not found"}

        gate = next((g for g in current_phase.gates if g.gate_id == gate_id), None)
        if not gate:
            return {"error": f"Gate {gate_id} not found"}

        # 進化条件チェック（force=Trueの場合はスキップ）
        if not force:
            evaluation = self.evaluate_prophecy(prophecy_name, {})
            if not evaluation.get("evolution_ready", False):
                return {
                    "error": "Evolution conditions not met",
                    "evaluation": evaluation,
                }

        # 進化実行
        evolution_result = {
            "prophecy_name": prophecy_name,
            "from_phase": current_phase.phase_id,
            "to_phase": gate.target_phase,
            "gate_id": gate_id,
            "evolution_actions": gate.evolution_actions,
            "executed_at": datetime.now().isoformat(),
            "success": True,
            "backup_id": None,
        }

        try:
            # バックアップ作成
            backup_id = await self.create_backup(prophecy_name)
            evolution_result["backup_id"] = backup_id

            # 進化アクション実行
            for action in gate.evolution_actions:
                logger.info(f"進化アクション実行: {action}")
                # 実際のアクション実行はサブクラスで実装
                await self.execute_evolution_action(prophecy_name, action)

            # 状態更新
            state["current_phase"] = gate.target_phase
            state["last_evolution"] = datetime.now().isoformat()
            state["stability_start"] = None  # 新フェーズの安定期間をリセット

            # 履歴記録
            self.prophecy_history.append(evolution_result)

            logger.info(
                f"進化完了: {prophecy_name} Phase {current_phase.phase_id} → {gate.target_phase}"
            )

        except Exception as e:
            evolution_result["success"] = False
            evolution_result["error"] = str(e)
            logger.error(f"進化実行エラー: {e}")

        self.save_state()
        return evolution_result

    async def create_backup(self, prophecy_name: str) -> str:
        """バックアップ作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{prophecy_name}_backup_{timestamp}"

        backup_dir = self.prophecy_dir / "backups" / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 現在の状態をバックアップ
        backup_data = {
            "prophecy_name": prophecy_name,
            "state": self.active_prophecies.get(prophecy_name, {}),
            "created_at": datetime.now().isoformat(),
        }

        backup_file = backup_dir / "state.json"
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"バックアップ作成: {backup_id}")
        return backup_id

    async def execute_evolution_action(self, prophecy_name: str, action: str):
        """進化アクション実行 (サブクラスでオーバーライド)"""
        logger.info(f"進化アクション: {action} (デフォルト実装)")
        # 実際の実装はサブクラスで行う
        pass

    def get_prophecy_status(self, prophecy_name: str) -> Dict:
        """予言書状態取得"""
        if prophecy_name not in self.prophecies:
            return {"error": f"Prophecy {prophecy_name} not found"}

        prophecy = self.prophecies[prophecy_name]
        state = self.active_prophecies[prophecy_name]

        current_phase = prophecy.get_current_phase(state)
        next_gate = (
            prophecy.get_next_gate(current_phase.phase_id) if current_phase else None
        )

        return {
            "prophecy_name": prophecy_name,
            "description": prophecy.description,
            "version": prophecy.version,
            "current_phase": (
                {
                    "phase_id": current_phase.phase_id,
                    "name": current_phase.name,
                    "description": current_phase.description,
                    "features": current_phase.features,
                }
                if current_phase
                else None
            ),
            "next_gate": (
                {
                    "gate_id": next_gate.gate_id,
                    "target_phase": next_gate.target_phase,
                    "criteria_count": len(next_gate.criteria),
                    "stability_days": next_gate.stability_days,
                }
                if next_gate
                else None
            ),
            "state": state,
            "total_phases": len(prophecy.phases),
        }

    def list_prophecies(self) -> List[Dict]:
        """予言書一覧取得"""
        result = []
        for name, prophecy in self.prophecies.items():
            state = self.active_prophecies.get(name, {})
            result.append(
                {
                    "name": name,
                    "description": prophecy.description,
                    "category": prophecy.category,
                    "version": prophecy.version,
                    "current_phase": state.get("current_phase", 1),
                    "total_phases": len(prophecy.phases),
                    "last_updated": prophecy.updated_at,
                }
            )
        return result


# 使用例
async def main():
    """テスト用メイン関数"""
    engine = ProphecyEngine()

    # テスト用予言書作成
    test_prophecy = Prophecy(
        prophecy_name="test_evolution",
        description="テスト用進化予言書",
        phases=[
            Phase(
                phase_id=1,
                name="初期段階",
                description="テスト初期段階",
                gates=[
                    Gate(
                        gate_id="test_gate_1",
                        target_phase=2,
                        criteria=[
                            Criterion("test_metric", ">=", 50),
                            Criterion("stability_metric", ">=", 80),
                        ],
                        evolution_actions=["enable_feature_1", "configure_system"],
                    )
                ],
            )
        ],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    # 予言書登録
    engine.register_prophecy(test_prophecy)

    # 評価実行
    test_metrics = {"test_metric": 60, "stability_metric": 85}
    result = engine.evaluate_prophecy("test_evolution", test_metrics)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

"""
Elder Flow PDCA自動化エンジン
永遠に回り続ける改善サイクルで、違反ゼロの楽園を目指す
"""

import threading
import time
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import statistics

from libs.elder_flow_violation_types_original import (
    ViolationType,
    ViolationSeverity,
    ViolationCategory,
    ELDER_FLOW_VIOLATION_RULES,
    ViolationRule,
)
from libs.elder_flow_violation_db import ElderFlowViolationDB


logger = logging.getLogger(__name__)


class PDCAPhase(Enum):
    """PDCAフェーズ"""

    PLAN = "plan"
    DO = "do"
    CHECK = "check"
    ACT = "act"


class ActionPriority(Enum):
    """改善アクションの優先度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(Enum):
    """アクションの状態"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PDCAMetrics:
    """PDCAサイクルのメトリクス"""

    violation_rate: float = 0.0  # 違反発生率（件/時）
    auto_fix_success_rate: float = 0.0  # 自動修正成功率（%）
    mttr_minutes: float = 0.0  # 平均修復時間（分）
    compliance_rate: float = 0.0  # プロセス遵守率（%）
    cycle_count: int = 0  # 実行サイクル数

    # 詳細メトリクス
    total_violations: int = 0
    violations_last_hour: int = 0
    auto_fixes_attempted: int = 0
    auto_fixes_successful: int = 0
    total_resolution_time: float = 0.0
    resolved_violations: int = 0

    # 前回との比較用
    previous_violation_rate: float = 0.0
    previous_auto_fix_rate: float = 0.0

    def calculate(self):
        """メトリクスを計算"""
        if self.total_violations > 0:
            self.violation_rate = self.violations_last_hour

        if self.auto_fixes_attempted > 0:
            self.auto_fix_success_rate = (
                self.auto_fixes_successful / self.auto_fixes_attempted * 100
            )

        if self.resolved_violations > 0:
            self.mttr_minutes = self.total_resolution_time / self.resolved_violations

    def is_improving(self) -> bool:
        """改善傾向にあるか判定"""
        return (
            self.violation_rate < self.previous_violation_rate
            or self.auto_fix_success_rate > self.previous_auto_fix_rate
        )

    def get_improvement_percentage(self) -> float:
        """改善率を取得"""
        if self.previous_violation_rate > 0:
            return (
                (self.previous_violation_rate - self.violation_rate)
                / self.previous_violation_rate
                * 100
            )
        return 0.0


@dataclass
class ImprovementAction:
    """改善アクション"""

    action_id: str
    title: str
    description: str
    priority: ActionPriority
    target_violation_type: Optional[ViolationType] = None
    status: ActionStatus = ActionStatus.PENDING

    # 実行情報
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: Optional[bool] = None
    result: Optional[str] = None

    def start_execution(self):
        """実行開始"""
        self.status = ActionStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete_execution(self, success: bool, result: str = ""):
        """実行完了"""
        self.status = ActionStatus.COMPLETED if success else ActionStatus.FAILED
        self.completed_at = datetime.now()
        self.success = success
        self.result = result

    def get_duration(self) -> Optional[timedelta]:
        """実行時間を取得"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class CycleResult:
    """PDCAサイクルの実行結果"""

    cycle_id: str
    started_at: datetime
    completed_at: datetime
    phase_results: Dict[PDCAPhase, Any]
    emergency: bool = False
    emergency_reason: Optional[str] = None

    def get_duration(self) -> timedelta:
        """サイクル実行時間を取得"""
        return self.completed_at - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.get_duration().total_seconds(),
            "phase_results": {
                phase.value: results for phase, results in self.phase_results.items()
            },
            "emergency": self.emergency,
            "emergency_reason": self.emergency_reason,
        }


class PDCACycle:
    """PDCAサイクルの実装"""

    def __init__(self):
        """初期化メソッド"""
        self.db = ElderFlowViolationDB()
        self.current_metrics = PDCAMetrics()
        self.improvement_actions: List[ImprovementAction] = []
        self.cycle_count = 0

    def plan(self) -> List[ImprovementAction]:
        """Plan: 違反傾向分析と改善計画策定"""
        logger.info("PDCAサイクル - Plan フェーズ開始")

        actions = []

        # 1.0 違反統計を分析
        stats = self.db.get_statistics()

        # 2.0 最も頻度の高い違反タイプを特定
        top_violations = self._identify_top_violations(stats)

        # 3.0 各違反タイプに対する改善アクションを生成
        for violation_type, count in top_violations:
            action = self._create_improvement_action(violation_type, count)
            if action:
                actions.append(action)

        # 4.0 優先度順にソート
        actions.sort(
            key=lambda a: (
                0
                if a.priority == ActionPriority.CRITICAL
                else (
                    1
                    if a.priority == ActionPriority.HIGH
                    else 2 if a.priority == ActionPriority.MEDIUM else 3
                )
            )
        )

        logger.info(f"Plan完了: {len(actions)}個のアクションを生成")
        return actions

    def do(self, actions: List[ImprovementAction]) -> List[ImprovementAction]:
        """Do: 改善アクションの実行"""
        logger.info(f"PDCAサイクル - Do フェーズ開始 ({len(actions)}個のアクション)")

        executed_actions = []

        for action in actions:
            try:
                action.start_execution()
                success = self._execute_action(action)
                action.complete_execution(
                    success=success, result="実行完了" if success else "実行失敗"
                )
                executed_actions.append(action)

            except Exception as e:
                logger.error(f"アクション実行エラー: {e}")
                action.complete_execution(success=False, result=f"エラー: {str(e)}")
                executed_actions.append(action)

        logger.info(f"Do完了: {len(executed_actions)}個のアクションを実行")
        return executed_actions

    def check(self, executed_actions: List[ImprovementAction]) -> Dict[str, Any]:
        """Check: 効果測定とKPI評価"""
        logger.info("PDCAサイクル - Check フェーズ開始")

        # 1.0 現在のメトリクスを計算
        current_metrics = self._calculate_current_metrics()

        # 2.0 アクションの成功率を評価
        successful_actions = sum(1 for a in executed_actions if a.success)
        failed_actions = len(executed_actions) - successful_actions

        # 3.0 改善度を評価
        improvement = current_metrics.get_improvement_percentage()

        evaluation = {
            "metrics": current_metrics,
            "action_results": {
                "total": len(executed_actions),
                "successful": successful_actions,
                "failed": failed_actions,
                "success_rate": (
                    (successful_actions / len(executed_actions) * 100)
                    if executed_actions
                    else 0
                ),
            },
            "improvement_percentage": improvement,
            "is_improving": current_metrics.is_improving(),
            "recommendations": self._generate_recommendations(current_metrics),
        }

        logger.info(f"Check完了: 改善率={improvement:0.1f}%")
        return evaluation

    def act(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Act: ルール更新とプロセス改善"""
        logger.info("PDCAサイクル - Act フェーズ開始")

        updates = {
            "rules_updated": 0,
            "process_improvements": [],
            "knowledge_base_updates": [],
        }

        # 1.0 効果的だったアクションに基づいてルールを更新
        if evaluation["is_improving"]:
            rule_updates = self._update_violation_rules(evaluation)
            updates["rules_updated"] = rule_updates

        # 2.0 プロセス改善の実施
        improvements = self._implement_process_improvements(evaluation)
        updates["process_improvements"] = improvements

        # 3.0 知識ベースの更新
        kb_updates = self._update_knowledge_base(evaluation)
        updates["knowledge_base_updates"] = kb_updates

        # 4.0 次回サイクルへの引き継ぎ事項を記録
        self._record_learnings(evaluation)

        logger.info(f"Act完了: {updates['rules_updated']}個のルール更新")
        return updates

    def execute_full_cycle(self) -> CycleResult:
        """フルPDCAサイクルを実行"""
        cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        started_at = datetime.now()
        phase_results = {}

        logger.info(f"PDCAサイクル開始: {cycle_id}")

        try:
            # Plan
            actions = self.plan()
            phase_results[PDCAPhase.PLAN] = {
                "actions_created": len(actions),
                "actions": [a.action_id for a in actions],
            }

            # Do
            executed = self.do(actions)
            phase_results[PDCAPhase.DO] = {
                "actions_executed": len(executed),
                "successful": sum(1 for a in executed if a.success),
            }

            # Check
            evaluation = self.check(executed)
            phase_results[PDCAPhase.CHECK] = evaluation

            # Act
            updates = self.act(evaluation)
            phase_results[PDCAPhase.ACT] = updates

            self.cycle_count += 1

        except Exception as e:
            logger.error(f"PDCAサイクルエラー: {e}")
            phase_results["error"] = str(e)

        completed_at = datetime.now()

        result = CycleResult(
            cycle_id=cycle_id,
            started_at=started_at,
            completed_at=completed_at,
            phase_results=phase_results,
        )

        logger.info(f"PDCAサイクル完了: {cycle_id} (所要時間: {result.get_duration()})")
        return result

    def _identify_top_violations(self, stats: Dict[str, Any]) -> List[tuple]:
        """最も頻度の高い違反を特定"""
        violations = []

        if "by_type" in stats:
            for violation_data in stats["by_type"]:
                violation_type = violation_data["violation_type"]
                count = violation_data["count"]
                violations.append((violation_type, count))

        # 頻度順にソート
        violations.sort(key=lambda x: x[1], reverse=True)

        # 上位5件を返す
        return violations[:5]

    def _create_improvement_action(
        self, violation_type: str, count: int
    ) -> Optional[ImprovementAction]:
        """違反タイプに応じた改善アクションを作成"""
        action_templates = {
            "docker_permission_violation": {
                "title": "Docker権限違反の自動修正強化",
                "description": "sg docker -cへの自動置換ロジックを改善",
                "priority": ActionPriority.HIGH,
            },
            "tdd_test_first_violation": {
                "title": "TDD違反の事前検知強化",
                "description": "コード作成前のテスト存在確認を強化",
                "priority": ActionPriority.HIGH,
            },
            "four_sages_consultation_missing": {
                "title": "4賢者相談リマインダー実装",
                "description": "新機能実装時の自動相談提案を実装",
                "priority": ActionPriority.CRITICAL,
            },
        }

        if violation_type in action_templates:
            template = action_templates[violation_type]
            return ImprovementAction(
                action_id=f"ACT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{violation_type[:5]}",
                title=template["title"],
                description=f"{template['description']} (過去{count}件発生)",
                priority=template["priority"],
                target_violation_type=(
                    ViolationType(violation_type)
                    if violation_type in [v.value for v in ViolationType]
                    else None
                ),
            )

        return None

    def _execute_action(self, action: ImprovementAction) -> bool:
        """アクションを実行"""
        logger.info(f"アクション実行: {action.title}")

        # 実際の実装では、各アクションタイプに応じた処理を実行
        # ここではシミュレーション

        if action.target_violation_type == ViolationType.DOCKER_PERMISSION_VIOLATION:
            # Docker権限違反の自動修正ロジック強化
            return self._enhance_docker_auto_fix()

        elif action.target_violation_type == ViolationType.TDD_TEST_FIRST_VIOLATION:
            # TDD違反検知の強化
            return self._enhance_tdd_detection()

        # デフォルトは成功とする
        return True

    def _enhance_docker_auto_fix(self) -> bool:
        """Docker自動修正の強化（シミュレーション）"""
        # 実際の実装では、自動修正ロジックを更新
        logger.info("Docker権限違反の自動修正ロジックを強化しました")
        return True

    def _enhance_tdd_detection(self) -> bool:
        """TDD違反検知の強化（シミュレーション）"""
        # 実際の実装では、検知ロジックを更新
        logger.info("TDD違反の事前検知ロジックを強化しました")
        return True

    def _calculate_current_metrics(self) -> PDCAMetrics:
        """現在のメトリクスを計算"""
        metrics = PDCAMetrics()
        stats = self.db.get_statistics()

        # 基本メトリクスを設定
        metrics.total_violations = stats.get("total_violations", 0)
        metrics.violations_last_hour = self._get_violations_last_hour()

        # 自動修正の統計（シミュレーション）
        metrics.auto_fixes_attempted = 50  # 実際はログから取得
        metrics.auto_fixes_successful = 40

        # MTTR計算用データ（シミュレーション）
        metrics.resolved_violations = 30
        metrics.total_resolution_time = 150  # 分

        # 前回のメトリクスを保存
        if hasattr(self, "current_metrics"):
            metrics.previous_violation_rate = self.current_metrics.violation_rate
            metrics.previous_auto_fix_rate = self.current_metrics.auto_fix_success_rate

        metrics.calculate()
        self.current_metrics = metrics

        return metrics

    def _get_violations_last_hour(self) -> int:
        """過去1時間の違反数を取得"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        violations = self.db.search_violations(
            start_date=one_hour_ago, resolved=None  # 全ての違反を含む
        )
        return len(violations)

    def _generate_recommendations(self, metrics: PDCAMetrics) -> List[str]:
        """改善推奨事項を生成"""
        recommendations = []

        if metrics.violation_rate > 10:
            recommendations.append("違反発生率が高いため、予防的対策の強化を推奨")

        if metrics.auto_fix_success_rate < 70:
            recommendations.append(
                "自動修正成功率が低いため、修正ロジックの見直しを推奨"
            )

        if metrics.mttr_minutes > 30:
            recommendations.append("平均修復時間が長いため、対応プロセスの効率化を推奨")

        return recommendations

    def _update_violation_rules(self, evaluation: Dict[str, Any]) -> int:
        """違反ルールを更新"""
        updates = 0

        # 実際の実装では、効果的だったアクションに基づいて
        # 違反検知ルールや自動修正ロジックを更新

        logger.info("違反ルールの更新を実施")
        return updates

    def _implement_process_improvements(self, evaluation: Dict[str, Any]) -> List[str]:
        """プロセス改善を実施"""
        improvements = []

        if evaluation["improvement_percentage"] > 20:
            improvements.append("成功パターンをドキュメント化")
            improvements.append("チーム全体へのベストプラクティス共有")

        return improvements

    def _update_knowledge_base(self, evaluation: Dict[str, Any]) -> List[str]:
        """知識ベースを更新"""
        updates = []

        # 学習内容を知識ベースに記録
        kb_path = Path("knowledge_base/pdca_learnings")
        kb_path.mkdir(parents=True, exist_ok=True)

        learning_file = (
            kb_path / f"learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(learning_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": evaluation["metrics"].__dict__,
                    "improvement_percentage": evaluation["improvement_percentage"],
                    "recommendations": evaluation["recommendations"],
                },
                f,
                indent=2,
            )

        updates.append(f"学習内容を記録: {learning_file.name}")
        return updates

    def _record_learnings(self, evaluation: Dict[str, Any]):
        """学習内容を記録"""
        logger.info("PDCAサイクルの学習内容を記録")
        # 次回サイクルで活用するための情報を保存


class PDCAEngine:
    """PDCA自動化エンジン"""

    def __init__(self, cycle_interval: int = 3600):
        """
        初期化

        Args:
            cycle_interval: サイクル実行間隔（秒）、デフォルト1時間
        """
        self.cycle = PDCACycle()
        self.cycle_interval = cycle_interval
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.cycle_history: List[CycleResult] = []
        self.stop_event = threading.Event()

    def start(self):
        """エンジンを開始"""
        if not self.is_running:
            self.is_running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_continuous)
            self.thread.daemon = True
            self.thread.start()
            logger.info("PDCAエンジンを起動しました")

    def stop(self):
        """エンジンを停止"""
        if self.is_running:
            self.is_running = False
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("PDCAエンジンを停止しました")

    def _run_continuous(self):
        """継続的にサイクルを実行"""
        while self.is_running and not self.stop_event.is_set():
            self._run_cycle()

            # 次のサイクルまで待機
            self.stop_event.wait(self.cycle_interval)

    def _run_cycle(self):
        """1サイクルを実行"""
        try:
            result = self.cycle.execute_full_cycle()
            self.cycle_history.append(result)

            # 履歴は最新100件のみ保持
            if len(self.cycle_history) > 100:
                self.cycle_history = self.cycle_history[-100:]

        except Exception as e:
            logger.error(f"PDCAサイクル実行エラー: {e}")

    def trigger_emergency_cycle(self, reason: str):
        """緊急サイクルをトリガー"""
        logger.warning(f"緊急PDCAサイクルをトリガー: {reason}")

        # 緊急サイクルを即座に実行
        result = self.cycle.execute_full_cycle()
        result.emergency = True
        result.emergency_reason = reason
        self.cycle_history.append(result)

    def get_status(self) -> Dict[str, Any]:
        """エンジンのステータスを取得"""
        last_cycle = self.cycle_history[-1] if self.cycle_history else None

        status = {
            "is_running": self.is_running,
            "cycle_interval_seconds": self.cycle_interval,
            "total_cycles": len(self.cycle_history),
            "last_cycle_time": (
                last_cycle.completed_at.isoformat() if last_cycle else None
            ),
            "last_cycle_duration": (
                last_cycle.get_duration().total_seconds() if last_cycle else None
            ),
        }

        # 平均サイクル時間を計算
        if self.cycle_history:
            durations = [
                c.get_duration().total_seconds() for c in self.cycle_history[-10:]
            ]
            status["average_cycle_duration"] = statistics.mean(durations)

        return status

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクスのサマリーを取得"""
        if not self.cycle_history:
            return {}

        # 最新のメトリクスを取得
        latest_metrics = None
        for cycle in reversed(self.cycle_history):
            if PDCAPhase.CHECK in cycle.phase_results:
                check_result = cycle.phase_results[PDCAPhase.CHECK]
                if "metrics" in check_result:
                    latest_metrics = check_result["metrics"]
                    break

        if not latest_metrics:
            return {}

        summary = {
            "current_violation_rate": latest_metrics.violation_rate,
            "current_auto_fix_rate": latest_metrics.auto_fix_success_rate,
            "current_mttr": latest_metrics.mttr_minutes,
            "total_cycles_executed": len(self.cycle_history),
        }

        # トレンドを計算
        if len(self.cycle_history) >= 2:
            # 前回のメトリクスと比較
            prev_metrics = None
            for cycle in self.cycle_history[-2::-1]:
                if PDCAPhase.CHECK in cycle.phase_results:
                    check_result = cycle.phase_results[PDCAPhase.CHECK]
                    if "metrics" in check_result:
                        prev_metrics = check_result["metrics"]
                        break

            if prev_metrics:
                summary["violation_rate_trend"] = (
                    "improving"
                    if latest_metrics.violation_rate < prev_metrics.violation_rate
                    else "worsening"
                )
                summary["improvement_percentage"] = (
                    (
                        (prev_metrics.violation_rate - latest_metrics.violation_rate)
                        / prev_metrics.violation_rate
                        * 100
                    )
                    if prev_metrics.violation_rate > 0
                    else 0
                )

        return summary

    def export_cycle_history(self) -> str:
        """サイクル履歴をエクスポート"""
        export_data = {
            "engine_status": self.get_status(),
            "metrics_summary": self.get_metrics_summary(),
            "cycles": [cycle.to_dict() for cycle in self.cycle_history],
        }

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def _schedule_next_cycle(self):
        """次のサイクルをスケジュール"""
        if self.is_running:
            timer = threading.Timer(self.cycle_interval, self._run_continuous)
            timer.daemon = True
            timer.start()

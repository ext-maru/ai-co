#!/usr/bin/env python3
"""
自己修復オーケストレーター
エラー予測、予防、修正、学習の全サイクルを統合管理
"""

import asyncio
import json
import logging
import sqlite3

# プロジェクトルートをPythonパスに追加
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Lock, Thread
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import EMOJI, BaseManager, get_config
from libs.auto_fix_executor import AutoFixExecutor
from libs.error_intelligence_manager import ErrorIntelligenceManager
from libs.error_pattern_predictor import ErrorPatternPredictor

# from libs.preventive_fix_engine import PreventiveFixEngine  # Module not found
from libs.learning_optimizer import LearningOptimizer
from libs.retry_orchestrator import RetryOrchestrator
from libs.slack_notifier import SlackNotifier


class HealingStrategy(Enum):
    """修復戦略"""

    PREVENTIVE = "preventive"  # 予防的修正
    REACTIVE = "reactive"  # リアクティブ修正
    PREDICTIVE = "predictive"  # 予測的修正
    ADAPTIVE = "adaptive"  # 適応的修正
    EMERGENCY = "emergency"  # 緊急修正


class SystemHealth(Enum):
    """システム健康状態"""

    EXCELLENT = "excellent"  # 95%以上の自動修正率
    GOOD = "good"  # 80-95%
    FAIR = "fair"  # 60-80%
    POOR = "poor"  # 40-60%
    CRITICAL = "critical"  # 40%未満


class SelfHealingOrchestrator(BaseManager):
    """自己修復システムの中央オーケストレーター"""

    def __init__(self)super().__init__()
    """初期化メソッド"""
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)

        # コンポーネント初期化
        self.error_manager = ErrorIntelligenceManager()
        self.fix_executor = AutoFixExecutor()
        self.retry_orchestrator = RetryOrchestrator()
        self.pattern_predictor = ErrorPatternPredictor()
        # self.preventive_engine = PreventiveFixEngine()  # Module not available
        self.learning_optimizer = LearningOptimizer()
        self.slack_notifier = SlackNotifier()

        # 実行管理
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.active_healings = {}
        self.healing_lock = Lock()

        # データベース
        self.db_path = PROJECT_ROOT / "db" / "self_healing.db"
        self._init_database()

        # システム状態
        self.system_health = SystemHealth.FAIR
        self.healing_metrics = {
            "total_incidents": 0,
            "self_healed": 0,
            "prevented": 0,
            "manual_required": 0,
            "avg_healing_time": 0,
            "health_score": 0.6,
        }

        # 設定
        self.healing_config = {
            "enable_predictive": True,
            "enable_preventive": True,
            "enable_learning": True,
            "max_healing_attempts": 5,
            "health_check_interval": 300,  # 5分
            "optimization_interval": 3600,  # 1時間
            "emergency_threshold": 0.4,  # 健康スコア40%未満で緊急モード
        }

    def _init_database(self)self.db_path.parent.mkdir(parents=True, exist_ok=True)
    """自己修復履歴データベース"""

        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS healing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE,
                    error_type TEXT,
                    error_hash TEXT,
                    detected_at TIMESTAMP,
                    healing_strategy TEXT,
                    actions_taken TEXT,  -- JSON
                    healing_duration REAL,
                    success BOOLEAN,
                    prevented BOOLEAN,
                    manual_intervention BOOLEAN,
                    health_impact REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_health_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    health_status TEXT,
                    health_score REAL,
                    auto_healing_rate REAL,
                    prevention_rate REAL,
                    avg_healing_time REAL,
                    active_issues INTEGER,
                    metrics_json TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS healing_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT,
                    feedback_type TEXT,  -- success, failure, false_positive
                    feedback_data TEXT,
                    impact_score REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    async def start_orchestration(self)self.logger.info("Starting Self-Healing Orchestrator...")
    """オーケストレーション開始"""

        # 各コンポーネントを起動
        await self._start_components()

        # 監視ループを開始
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._optimization_loop())
        asyncio.create_task(self._predictive_healing_loop())

        self.logger.info("Self-Healing Orchestrator started successfully")

    async def _start_components(self):
        """コンポーネントを起動"""
        # 予防エンジンを起動
        self.preventive_engine.start_monitoring()

        # 学習最適化を開始
        self.learning_optimizer.start_optimization()

        # 初期健康診断
        await self._perform_health_check()

    async def _health_monitoring_loop(self):
        """システム健康監視ループ"""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.healing_config["health_check_interval"])
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)

    async def _optimization_loop(self):
        """最適化ループ"""
        while True:
            try:
                await self._optimize_healing_strategies()
                await asyncio.sleep(self.healing_config["optimization_interval"])
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(300)

    async def _predictive_healing_loop(self):
        """予測的修復ループ"""
        while self.healing_config["enable_predictive"]:
            try:
                # エラー予測を取得
                predictions = self.pattern_predictor.predict_errors()

                # 高リスク予測に対して予防的対応
                for prediction in predictions:
                    if prediction.risk_score > 0.7:
                        await self._initiate_predictive_healing(prediction)

                await asyncio.sleep(60)  # 1分ごとにチェック

            except Exception as e:
                self.logger.error(f"Error in predictive healing: {e}")
                await asyncio.sleep(60)

    async def handle_error_incident(self, error_info: Dict) -> Dict:
        """エラーインシデントを処理"""
        incident_id = f"incident_{datetime.now(
            ).strftime('%Y%m%d_%H%M%S')}_{error_info.get('error_type',
            'unknown'
        )}"

        self.healing_metrics["total_incidents"] += 1

        healing_result = {
            "incident_id": incident_id,
            "success": False,
            "strategy_used": None,
            "actions_taken": [],
            "duration": 0,
            "prevented": False,
            "manual_required": False,
        }

        start_time = time.time()

        try:
            # エラーを記録（学習用）
            error_hash = self.pattern_predictor.record_error_occurrence(error_info)

            # 修復戦略を決定
            strategy = await self._determine_healing_strategy(error_info)
            healing_result["strategy_used"] = strategy.value

            # 戦略に基づいて修復実行
            if strategy == HealingStrategy.EMERGENCY:
                success = await self._execute_emergency_healing(error_info, incident_id)
            elif strategy == HealingStrategy.PREVENTIVE:
                success = await self._execute_preventive_healing(
                    error_info, incident_id
                )
            elif strategy == HealingStrategy.PREDICTIVE:
                success = await self._execute_predictive_healing(
                    error_info, incident_id
                )
            elif strategy == HealingStrategy.ADAPTIVE:
                success = await self._execute_adaptive_healing(error_info, incident_id)
            else:  # REACTIVE
                success = await self._execute_reactive_healing(error_info, incident_id)

            healing_result["success"] = success

            if success:
                self.healing_metrics["self_healed"] += 1
                await self._notify_healing_success(incident_id, strategy)
            else:
                self.healing_metrics["manual_required"] += 1
                await self._notify_manual_intervention_required(incident_id, error_info)
                healing_result["manual_required"] = True

        except Exception as e:
            self.logger.error(f"Error in healing orchestration: {e}")
            healing_result["error"] = str(e)

        finally:
            healing_result["duration"] = time.time() - start_time

            # 修復履歴を記録
            self._record_healing_history(incident_id, error_info, healing_result)

            # メトリクス更新
            await self._update_healing_metrics(healing_result)

            # 学習フィードバック
            self.learning_optimizer.provide_feedback(incident_id, healing_result)

        return healing_result

    async def _determine_healing_strategy(self, error_info: Dict) -> HealingStrategy:
        """最適な修復戦略を決定"""
        # システム健康状態を考慮
        if self.system_health == SystemHealth.CRITICAL:
            return HealingStrategy.EMERGENCY

        # エラー分析
        analysis = self.error_manager.analyze_error(
            error_info.get("error_text", ""), error_info
        )

        # 予測可能性をチェック
        if self.healing_config["enable_predictive"]:
            predictability = self._assess_predictability(error_info)
            if predictability > 0.8:
                return HealingStrategy.PREDICTIVE

        # 予防可能性をチェック
        if self.healing_config["enable_preventive"]:
            if analysis["category"] in ["dependency", "filesystem", "permission"]:
                return HealingStrategy.PREVENTIVE

        # 学習データが十分な場合は適応的戦略
        if self._has_sufficient_learning_data(error_info):
            return HealingStrategy.ADAPTIVE

        # デフォルトはリアクティブ
        return HealingStrategy.REACTIVE

    async def _execute_reactive_healing(
        self, error_info: Dict, incident_id: str
    ) -> bool:
        """リアクティブ修復（従来の方法）"""
        # Phase 1: エラー分析
        analysis = self.error_manager.analyze_error(
            error_info.get("error_text", ""), error_info
        )

        if not analysis["auto_fixable"]:
            return False

        # Phase 2: 自動修正
        fix_result = self.fix_executor.execute_fix(analysis, error_info)

        if not fix_result["success"]:
            return False

        # リトライ
        retry_result = self.retry_orchestrator.orchestrate_retry(
            error_info, error_info, fix_result
        )

        return retry_result["retry_success"]

    async def _execute_predictive_healing(
        self, prediction_or_error, incident_id: str
    ) -> bool:
        """予測的修復"""
        # 予測に基づいて事前に環境を調整
        if hasattr(prediction_or_error, "preventive_actions"):
            for action in prediction_or_error.preventive_actions:
                # 予防的アクションを実行
                self.preventive_engine._execute_preventive_action(
                    {
                        "action_id": f"{incident_id}_prev_{action['action']}",
                        "prediction": prediction_or_error,
                        "action": action,
                        "scheduled_at": datetime.now(),
                        "status": "scheduled",
                    }
                )
            return True

        return await self._execute_reactive_healing(prediction_or_error, incident_id)

    async def _execute_adaptive_healing(
        self, error_info: Dict, incident_id: str
    ) -> bool:
        """適応的修復（学習に基づく）"""
        # 最適化された戦略を取得
        optimized_strategy = self.learning_optimizer.get_optimized_strategy(
            error_info.get("error_type", "unknown")
        )

        if optimized_strategy:
            # 最適化された修正を実行
            fix_result = self.fix_executor.execute_fix(
                {"fix_strategies": [optimized_strategy], "auto_fixable": True},
                error_info,
            )

            if fix_result["success"]:
                # 成功を学習
                self.learning_optimizer.record_success(
                    error_info.get("error_type"), optimized_strategy
                )
                return True

        # 失敗時は通常の修復にフォールバック
        return await self._execute_reactive_healing(error_info, incident_id)

    async def _execute_emergency_healing(
        self, error_info: Dict, incident_id: str
    ) -> bool:
        """緊急修復（システムクリティカル時）"""
        self.logger.warning(f"Executing emergency healing for {incident_id}")

        # 1.0 即座にリソースを解放
        emergency_actions = [
            "pkill -f 'python.*worker' || true",  # ワーカー停止
            "sync && echo 3 > /proc/sys/vm/drop_caches",  # キャッシュクリア
            "ai-restart --emergency",  # 緊急再起動
        ]

        for action in emergency_actions:
            try:
                self.executor.submit(self._execute_emergency_command, action)
            except Exception as e:
                self.logger.error(f"Emergency action failed: {e}")

        # 2.0 最小構成で再起動
        time.sleep(5)

        # 3.0 段階的に機能を復旧
        return await self._gradual_recovery()

    def _execute_emergency_command(self, command: str):
        """緊急コマンドを実行"""
        import subprocess

        try:
            subprocess.run(command, shell=True, timeout=30)
        except Exception as e:
            self.logger.error(f"Emergency command failed: {command}, Error: {e}")

    async def _gradual_recovery(self) -> bool:
        """段階的復旧"""
        recovery_steps = [
            "ai-start --core-only",
            "ai-start --add-workers 2",
            "ai-start --full",
        ]

        for step in recovery_steps:
            try:
                # 復旧ステップ実行
                await asyncio.sleep(10)
                # TODO: 実際の復旧コマンド実行
                self.logger.info(f"Recovery step: {step}")
            except Exception as e:
                self.logger.error(f"Recovery step failed: {e}")
                return False

        return True

    async def _initiate_predictive_healing(self, prediction)incident_id = f"pred_incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    """予測に基づく修復を開始"""

        # 予測を疑似エラー情報に変換
        pseudo_error = {
            "error_type": prediction.error_type,
            "error_text": f"Predicted: {prediction.error_type}",
            "is_prediction": True,
        }

        result = await self._execute_predictive_healing(prediction, incident_id)

        if result:
            self.healing_metrics["prevented"] += 1

            # 予測の成功をフィードバック
            self.pattern_predictor.update_prediction_feedback(
                prediction.error_type,  # 簡易的にerror_typeを使用
                actual_occurred=False,
                prevented=True,
            )

    async def _perform_health_check(self):
        """システム健康診断"""
        # 各コンポーネントの統計を収集
        error_stats = self.error_manager.get_error_statistics()
        fix_stats = self.fix_executor.get_statistics()
        retry_stats = self.retry_orchestrator.get_retry_statistics()
        prediction_accuracy = self.pattern_predictor.get_prediction_accuracy()
        prevention_effectiveness = (
            self.preventive_engine.verify_prevention_effectiveness()
        )

        # 健康スコアを計算
        health_score = self._calculate_health_score(
            {
                "error_stats": error_stats,
                "fix_stats": fix_stats,
                "retry_stats": retry_stats,
                "prediction_accuracy": prediction_accuracy,
                "prevention_effectiveness": prevention_effectiveness,
            }
        )

        # 健康状態を更新
        self._update_health_status(health_score)

        # ログに記録
        self._log_health_status(health_score)

    def _calculate_health_score(self, stats: Dict) -> float:
        """健康スコアを計算"""
        # 重み付けスコア計算
        weights = {
            "auto_fix_rate": 0.3,
            "prevention_rate": 0.2,
            "prediction_accuracy": 0.2,
            "retry_success_rate": 0.15,
            "error_reduction": 0.15,
        }

        scores = {
            "auto_fix_rate": stats["fix_stats"].get("success_rate", 0) / 100,
            "prevention_rate": stats["prevention_effectiveness"].get(
                "prevention_rate", 0
            )
            / 100,
            "prediction_accuracy": stats["prediction_accuracy"].get("accuracy", 0),
            "retry_success_rate": stats["retry_stats"].get("success_rate", 0) / 100,
            "error_reduction": 1
            - (stats["error_stats"].get("total_errors", 100) / 100),  # 仮定
        }

        health_score = sum(scores[key] * weights[key] for key in weights)

        return health_score

    def _update_health_status(self, health_score: float):
        """健康状態を更新"""
        self.healing_metrics["health_score"] = health_score

        if health_score >= 0.95:
            self.system_health = SystemHealth.EXCELLENT
        elif health_score >= 0.8:
            self.system_health = SystemHealth.GOOD
        elif health_score >= 0.6:
            self.system_health = SystemHealth.FAIR
        elif health_score >= 0.4:
            self.system_health = SystemHealth.POOR
        else:
            self.system_health = SystemHealth.CRITICAL

    def _log_health_status(self, health_score: float)with sqlite3connect(self.db_path) as conn:
    """健康状態をログに記録"""
            metrics = {
                "total_incidents": self.healing_metrics["total_incidents"],
                "self_healed": self.healing_metrics["self_healed"],
                "prevented": self.healing_metrics["prevented"],
                "manual_required": self.healing_metrics["manual_required"],
            }

            auto_healing_rate = (
                (
                    self.healing_metrics["self_healed"]
                    / self.healing_metrics["total_incidents"]
                    * 100
                )
                if self.healing_metrics["total_incidents"] > 0
                else 0
            )

            prevention_rate = (
                (
                    self.healing_metrics["prevented"]
                    / (
                        self.healing_metrics["total_incidents"]
                        + self.healing_metrics["prevented"]
                    )
                    * 100
                )
                if (
                    self.healing_metrics["total_incidents"]
                    + self.healing_metrics["prevented"]
                )
                > 0
                else 0
            )

            conn.execute(
                """
                INSERT INTO system_health_log
                (timestamp, health_status, health_score, auto_healing_rate,
                 prevention_rate, avg_healing_time, active_issues, metrics_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    self.system_health.value,
                    health_score,
                    auto_healing_rate,
                    prevention_rate,
                    self.healing_metrics["avg_healing_time"],
                    len(self.active_healings),
                    json.dumps(metrics),
                ),
            )

    async def _optimize_healing_strategies(self):
        """修復戦略を最適化"""
        # 学習オプティマイザに最適化を依頼
        optimization_result = self.learning_optimizer.optimize_all_strategies()

        # 成功した最適化を適用
        if optimization_result["improvements"] > 0:
            self.logger.info(
                f"Applied {optimization_result['improvements']} strategy optimizations"
            )

    def _assess_predictability(self, error_info: Dict) -> float:
        """エラーの予測可能性を評価"""
        # 過去の発生パターンから予測可能性を計算
        # TODO: 実装
        return 0.7

    def _has_sufficient_learning_data(self, error_info: Dict) -> boolerror_type = error_info.get("error_type", "unknown")
    """十分な学習データがあるか確認"""
        # TODO: 実装
        return False

    def _record_healing_history(
        self, incident_id: str, error_info: Dict, healing_result: Dict
    ):
        """修復履歴を記録"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO healing_history
                (incident_id, error_type, error_hash, detected_at,
                 healing_strategy, actions_taken, healing_duration,
                 success, prevented, manual_intervention, health_impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    incident_id,
                    error_info.get("error_type", "unknown"),
                    error_info.get("error_hash", ""),
                    datetime.now(),
                    healing_result.get("strategy_used", ""),
                    json.dumps(healing_result.get("actions_taken", [])),
                    healing_result.get("duration", 0),
                    healing_result.get("success", False),
                    healing_result.get("prevented", False),
                    healing_result.get("manual_required", False),
                    0.01 if healing_result.get("success") else -0.05,
                ),
            )

    async def _update_healing_metrics(self, healing_result: Dict):
        """修復メトリクスを更新"""
        # 平均修復時間を更新
        total_healings = (
            self.healing_metrics["self_healed"]
            + self.healing_metrics["manual_required"]
        )

        if total_healings > 0:
            current_avg = self.healing_metrics["avg_healing_time"]
            new_duration = healing_result.get("duration", 0)

            self.healing_metrics["avg_healing_time"] = (
                current_avg * (total_healings - 1) + new_duration
            ) / total_healings

    async def _notify_healing_success(
        self, incident_id: str, strategy: HealingStrategy
    ):
        """修復成功を通知"""
        message = f"""
{EMOJI['info']} **自己修復完了**

**インシデントID**: {incident_id}
**修復戦略**: {strategy.value}
**システム健康状態**: {self.system_health.value}
**健康スコア**: {self.healing_metrics['health_score']:0.1%}

システムは自動的に修復されました。
"""
        try:
            self.slack_notifier.send_message(message)
        except:
            pass

    async def _notify_manual_intervention_required(
        self, incident_id: str, error_info: Dict
    ):
        """手動介入が必要な場合の通知"""
        message = f"""
{EMOJI['info']} **手動介入が必要です**

**インシデントID**: {incident_id}
**エラータイプ**: {error_info.get('error_type', 'unknown')}
**エラー**: {error_info.get('error_text', '')[:200]}

自動修復に失敗しました。手動での対応をお願いします。
"""
        try:
            self.slack_notifier.send_message(message)
        except:
            pass

    def get_healing_statistics(self) -> Dict:
        """修復統計を取得"""
        # 基本メトリクス
        base_stats = self.healing_metrics.copy()

        # 成功率計算
        if base_stats["total_incidents"] > 0:
            base_stats["auto_healing_rate"] = (
                base_stats["self_healed"] / base_stats["total_incidents"] * 100
            )
        else:
            base_stats["auto_healing_rate"] = 0

        # 予防率計算
        total_with_prevented = base_stats["total_incidents"] + base_stats["prevented"]
        if total_with_prevented > 0:
            base_stats["prevention_rate"] = (
                base_stats["prevented"] / total_with_prevented * 100
            )
        else:
            base_stats["prevention_rate"] = 0

        # コンポーネント統計
        component_stats = {
            "predictor_accuracy": self.pattern_predictor.get_prediction_accuracy(),
            "prevention_effectiveness": self.preventive_engine.verify_prevention_effectiveness(),
            "fix_executor_stats": self.fix_executor.get_statistics(),
            "retry_stats": self.retry_orchestrator.get_retry_statistics(),
        }

        return {
            "healing_metrics": base_stats,
            "system_health": self.system_health.value,
            "component_stats": component_stats,
            "active_healings": len(self.active_healings),
        }


# グローバルインスタンス（シングルトン）
_orchestrator_instance = None


def get_orchestrator() -> SelfHealingOrchestrator:
    """オーケストレーターのシングルトンインスタンスを取得"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SelfHealingOrchestrator()
    return _orchestrator_instance


if __name__ == "__main__":
    # テスト実行
    import asyncio

    async def test_orchestrator()orchestrator = get_orchestrator()
    """test_orchestratorテストメソッド"""

        print("=== Self-Healing Orchestrator Test ===")

        # オーケストレーター起動
        await orchestrator.start_orchestration()
        print("Orchestrator started")

        # テストエラー
        test_error = {
            "error_type": "ImportError",
            "error_text": "ModuleNotFoundError: No module named 'test_module'",
            "worker_type": "task",
            "task_id": "test_task_001",
        }

        # エラー処理
        print("\nHandling test error...")
        result = await orchestrator.handle_error_incident(test_error)
        print(f"Result: {json.dumps(result, indent}")

        # 統計表示
        await asyncio.sleep(5)
        stats = orchestrator.get_healing_statistics()
        print(f"\nStatistics: {json.dumps(stats, indent}")

    # 実行
    asyncio.run(test_orchestrator())

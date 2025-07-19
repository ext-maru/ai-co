#!/usr/bin/env python3
"""
🚨 Enhanced Incident Sage - 強化版インシデント賢者
Phase 26: 追跡システム統合による予防的危機管理
Created: 2025-07-17
Author: Claude Elder
Version: 2.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Elder Flow追跡システム
from libs.elder_flow.tracking.database import ElderFlowTrackingDB
from libs.four_sages.incident.automatic_response_system import AutomaticResponseSystem

# 新しい統合コンポーネント
from libs.four_sages.incident.failure_pattern_detector import FailurePatternDetector
from libs.four_sages.incident.incident_predictor import IncidentPredictor

# 既存のIncident Sage
from libs.four_sages.incident.incident_sage import (
    AlertLevel,
    IncidentCategory,
    IncidentEntry,
    IncidentSage,
    IncidentSeverity,
    IncidentStatus,
)
from libs.four_sages.incident.preventive_alert_system import PreventiveAlertSystem

logger = logging.getLogger("enhanced_incident_sage")


class EnhancedIncidentSage(IncidentSage):
    """
    強化版インシデント賢者
    追跡システム統合による予防的危機管理機能を追加
    """

    def __init__(self, tracking_db_path: str = "elder_flow_tracking.db"):
        """強化版初期化"""
        super().__init__()

        # 追跡データベース
        self.tracking_db = ElderFlowTrackingDB(tracking_db_path)

        # 統合コンポーネント
        self.failure_detector = FailurePatternDetector(
            tracking_db_path=tracking_db_path,
            incident_db_path=str(self.database.db_path),
        )
        self.alert_system = PreventiveAlertSystem(self)
        self.response_system = AutomaticResponseSystem(self)
        self.predictor = IncidentPredictor(self.failure_detector)

        # 統合設定
        self.integration_config = {
            "pattern_analysis_interval": 3600,  # 1時間ごと
            "prediction_interval": 300,  # 5分ごと
            "auto_response_enabled": True,
            "preventive_alerts_enabled": True,
        }

        # 統合メトリクス
        self.integration_metrics = {
            "patterns_detected": 0,
            "predictions_made": 0,
            "preventive_alerts": 0,
            "auto_responses": 0,
            "incidents_prevented": 0,
        }

        # バックグラウンドタスク
        self.background_tasks = []

        logger.info("🚨 Enhanced Incident Sage initialized with tracking integration")

    async def initialize_integration(self):
        """統合システム初期化"""
        try:
            logger.info("🔧 Initializing Enhanced Incident Sage integration...")

            # 追跡データベース初期化
            await self.tracking_db.initialize()

            # 初期パターン分析
            await self.failure_detector.analyze_historical_failures(days_back=30)

            # バックグラウンドタスク開始
            if self.integration_config["pattern_analysis_interval"] > 0:
                self.background_tasks.append(
                    asyncio.create_task(self._pattern_analysis_loop())
                )

            if self.integration_config["prediction_interval"] > 0:
                self.background_tasks.append(
                    asyncio.create_task(self._prediction_loop())
                )

            logger.info("✅ Integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Integration initialization failed: {e}")
            return False

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """拡張リクエスト処理"""
        request_type = request.get("type", "unknown")

        # 新しいリクエストタイプ
        if request_type == "analyze_patterns":
            return await self._analyze_patterns_request(request)
        elif request_type == "predict_risk":
            return await self._predict_risk_request(request)
        elif request_type == "get_integration_status":
            return await self._get_integration_status_request(request)
        elif request_type == "configure_integration":
            return await self._configure_integration_request(request)
        else:
            # 既存のリクエスト処理
            return await super().process_request(request)

    async def _create_incident_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント作成リクエスト（拡張版）"""
        # 親クラスの処理を実行
        result = await super()._create_incident_request(request)

        if result.get("success"):
            incident_id = result.get("incident_id")

            # 自動対応チェック
            if self.integration_config["auto_response_enabled"]:
                incident = await self.database.retrieve_incident(incident_id)
                if incident:
                    response_result = await self.response_system.handle_incident(
                        incident
                    )
                    if response_result.get("handled"):
                        self.integration_metrics["auto_responses"] += 1
                        result["auto_response"] = response_result

        return result

    async def monitor_tracking_metrics(self, metrics: Dict[str, float]):
        """追跡メトリクス監視"""
        try:
            # 予防的アラートチェック
            if self.integration_config["preventive_alerts_enabled"]:
                alert_result = await self.alert_system.monitor_metrics(metrics)

                if alert_result.get("alerts_generated", 0) > 0:
                    self.integration_metrics["preventive_alerts"] += alert_result[
                        "alerts_generated"
                    ]

                    # 高リスクアラートの場合、予測を実行
                    for alert in alert_result.get("alerts", []):
                        if alert["severity"] in ["critical", "emergency"]:
                            await self._trigger_prediction(metrics)

        except Exception as e:
            logger.error(f"❌ Tracking metrics monitoring failed: {e}")

    async def _pattern_analysis_loop(self):
        """パターン分析ループ"""
        while True:
            try:
                interval = self.integration_config["pattern_analysis_interval"]
                await asyncio.sleep(interval)

                logger.info("🔍 Running scheduled pattern analysis...")

                # パターン分析実行
                result = await self.failure_detector.analyze_historical_failures(
                    days_back=7
                )

                if result.get("success"):
                    patterns_found = result.get("patterns_found", 0)
                    self.integration_metrics["patterns_detected"] += patterns_found

                    logger.info(
                        f"✅ Pattern analysis completed: {patterns_found} patterns found"
                    )

            except Exception as e:
                logger.error(f"❌ Pattern analysis loop error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def _prediction_loop(self):
        """予測ループ"""
        while True:
            try:
                interval = self.integration_config["prediction_interval"]
                await asyncio.sleep(interval)

                # 現在のシステム状態を取得
                current_state = await self._get_system_state()

                # リスク予測実行
                prediction = await self.predictor.predict_incident_risk(current_state)
                self.integration_metrics["predictions_made"] += 1

                # 高リスクの場合はアラート
                if prediction.risk_level in ["high", "critical"]:
                    await self._handle_high_risk_prediction(prediction)

            except Exception as e:
                logger.error(f"❌ Prediction loop error: {e}")
                await asyncio.sleep(60)

    async def _get_system_state(self) -> Dict[str, Any]:
        """現在のシステム状態取得"""
        try:
            # 追跡データベースから最新メトリクスを取得
            recent_tasks = await self.tracking_db.get_all_tracked_tasks()

            # メトリクス計算
            total_tasks = len(recent_tasks)
            failed_tasks = sum(1 for t in recent_tasks if t.get("status") == "failed")

            metrics = {
                "error_rate": failed_tasks / total_tasks if total_tasks > 0 else 0,
                "response_time": 2.5,  # プレースホルダー
                "cpu_usage": 65.0,  # プレースホルダー
                "memory_usage": 70.0,  # プレースホルダー
                "active_connections": 150,
            }

            # 履歴情報
            history = {
                "failures_1h": failed_tasks,
                "failures_24h": failed_tasks * 10,  # プレースホルダー
            }

            return {
                "metrics": metrics,
                "history": history,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get system state: {e}")
            return {"metrics": {}, "history": {}}

    async def _trigger_prediction(self, metrics: Dict[str, float]):
        """予測トリガー"""
        try:
            current_state = {
                "metrics": metrics,
                "history": {},
                "timestamp": datetime.now().isoformat(),
            }

            prediction = await self.predictor.predict_incident_risk(current_state)

            if prediction.risk_level in ["high", "critical"]:
                await self._handle_high_risk_prediction(prediction)

        except Exception as e:
            logger.error(f"❌ Prediction trigger failed: {e}")

    async def _handle_high_risk_prediction(self, prediction):
        """高リスク予測の処理"""
        try:
            # 予防的インシデント作成
            incident_response = await self.process_request(
                {
                    "type": "create_incident",
                    "title": f"Predicted {prediction.risk_level} risk incident",
                    "description": f"Risk score: {prediction.risk_score:.2f}, "
                    f"Top factors: {prediction.contributing_factors[:3]}",
                    "category": "system_failure",  # 予測から最も可能性の高いカテゴリ
                    "severity": (
                        "high" if prediction.risk_level == "critical" else "medium"
                    ),
                    "tags": ["predicted", "preventive"],
                    "metadata": {
                        "prediction": prediction.to_dict(),
                        "preventive": True,
                    },
                }
            )

            if incident_response.get("success"):
                self.integration_metrics["incidents_prevented"] += 1
                logger.warning(
                    f"🔮 Preventive incident created: {incident_response['incident_id']}"
                )

        except Exception as e:
            logger.error(f"❌ High risk prediction handling failed: {e}")

    # 新しいリクエストハンドラー
    async def _analyze_patterns_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """パターン分析リクエスト"""
        days_back = request.get("days_back", 30)
        return await self.failure_detector.analyze_historical_failures(days_back)

    async def _predict_risk_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リスク予測リクエスト"""
        current_state = request.get("state", await self._get_system_state())
        prediction = await self.predictor.predict_incident_risk(current_state)

        return {"success": True, "prediction": prediction.to_dict()}

    async def _get_integration_status_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統合ステータス取得リクエスト"""
        return {
            "success": True,
            "integration_status": {
                "config": self.integration_config,
                "metrics": self.integration_metrics,
                "components": {
                    "failure_detector": "active",
                    "alert_system": "active",
                    "response_system": "active",
                    "predictor": "active",
                },
                "background_tasks": len(self.background_tasks),
            },
        }

    async def _configure_integration_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統合設定リクエスト"""
        config_updates = request.get("config", {})

        for key, value in config_updates.items():
            if key in self.integration_config:
                self.integration_config[key] = value

        return {"success": True, "updated_config": self.integration_config}

    def get_capabilities(self) -> List[str]:
        """拡張能力一覧"""
        base_capabilities = super().get_capabilities()
        enhanced_capabilities = [
            "failure_pattern_detection",
            "predictive_incident_analysis",
            "preventive_alert_generation",
            "automatic_incident_response",
            "tracking_system_integration",
            "ml_based_risk_prediction",
            "proactive_incident_prevention",
        ]
        return base_capabilities + enhanced_capabilities

    async def shutdown(self):
        """シャットダウン処理"""
        logger.info("🛑 Shutting down Enhanced Incident Sage...")

        # バックグラウンドタスクをキャンセル
        for task in self.background_tasks:
            task.cancel()

        # タスクの完了を待つ
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        logger.info("✅ Enhanced Incident Sage shutdown complete")


# シングルトンインスタンス
_enhanced_incident_sage = None


def get_enhanced_incident_sage() -> EnhancedIncidentSage:
    """Enhanced Incident Sage のシングルトンインスタンス取得"""
    global _enhanced_incident_sage
    if _enhanced_incident_sage is None:
        _enhanced_incident_sage = EnhancedIncidentSage()
    return _enhanced_incident_sage


# エクスポート
__all__ = ["EnhancedIncidentSage", "get_enhanced_incident_sage"]

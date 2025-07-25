#!/usr/bin/env python3
"""
🚨 Preventive Alert System - 予防的アラートシステム
Phase 26: Incident Sage統合実装
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from scipy import stats

# Elders Legacy Integration
from core.elders_legacy import EldersServiceLegacy
from libs.four_sages.incident.incident_sage import (
    AlertLevel,
    IncidentCategory,
    IncidentSage,
    IncidentSeverity,
)

logger = logging.getLogger("preventive_alert_system")


@dataclass
class MetricWindow:
    """メトリクス時間窓データ"""

    metric_name: str
    values: deque
    timestamps: deque
    window_size: int  # 秒単位

    def add_value(self, value: float, timestamp: datetime):
        """値を追加"""
        self.values.append(value)
        self.timestamps.append(timestamp)

        # 古いデータを削除
        cutoff = timestamp - timedelta(seconds=self.window_size)
        while self.timestamps and self.timestamps[0] < cutoff:
            self.values.popleft()
            self.timestamps.popleft()

    def get_statistics(self) -> Dict[str, float]:
        """統計情報取得"""
        if not self.values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0}

        values_array = np.array(self.values)
        return {
            "mean": float(np.mean(values_array)),
            "std": float(np.std(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "count": len(self.values),
        }


@dataclass
class PreventiveAlert:
    """予防的アラートデータ構造"""

    alert_id: str
    alert_type: str
    severity: AlertLevel
    message: str
    context: Dict[str, Any]
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    incident_id: Optional[str] = None
    actions_taken: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "incident_id": self.incident_id,
            "actions_taken": self.actions_taken,
            "metadata": self.metadata,
        }


class PreventiveAlertSystem(EldersServiceLegacy):
    """予防的アラートシステム"""

    def __init__(self, incident_sage: IncidentSage):
        """初期化メソッド"""
        super().__init__(name="PreventiveAlertSystem", service_type="monitoring")
        self.incident_sage = incident_sage
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[PreventiveAlert] = []
        self.escalation_policy: Dict[str, Dict[str, Any]] = {}
        self.metric_windows: Dict[str, MetricWindow] = {}
        self.alert_handlers: Dict[str, Callable] = {}
        self.suppression_rules: Dict[str, Dict[str, Any]] = {}

        # アラート統計
        self.alert_stats = {
            "total_alerts": 0,
            "alerts_by_severity": defaultdict(int),
            "alerts_by_type": defaultdict(int),
            "false_positive_rate": 0.0,
        }

        # デフォルトルール設定
        self._configure_default_rules()

        logger.info("🚨 Preventive Alert System initialized")

    def _configure_default_rules(self):
        """デフォルトアラートルール設定"""
        self.alert_rules = {
            "quality_degradation": {
                "metric": "quality_score",
                "warning": 0.85,
                "critical": 0.70,
                "window": 300,  # 5分間
                "trend_analysis": True,
            },
            "failure_rate": {
                "metric": "failure_rate",
                "warning": 0.10,
                "critical": 0.25,
                "window": 600,  # 10分間
                "consecutive_checks": 3,
            },
            "response_time": {
                "metric": "response_time",
                "warning": 5.0,
                "critical": 10.0,
                "window": 180,  # 3分間
                "percentile": 95,  # 95パーセンタイル
            },
            "error_spike": {
                "metric": "error_count",
                "baseline_multiplier": 2.0,  # ベースラインの2倍で警告
                "critical_multiplier": 5.0,  # 5倍で緊急
                "window": 300,
                "min_baseline_count": 10,
            },
            "resource_exhaustion": {
                "metric": "resource_usage",
                "warning": 0.80,
                "critical": 0.90,
                "window": 300,
                "prediction_enabled": True,
            },
        }

        # エスカレーションポリシー
        self.escalation_policy = {
            AlertLevel.WARNING: {
                "initial_delay": 300,  # 5分後にエスカレーション
                "escalate_to": AlertLevel.ALERT,
            },
            AlertLevel.ALERT: {
                "initial_delay": 600,  # 10分後にエスカレーション
                "escalate_to": AlertLevel.EMERGENCY,
            },
            AlertLevel.EMERGENCY: {
                "initial_delay": 0,  # 即座に最高レベルへ
                "notify_channels": ["incident_sage", "pager", "slack"],
            },
        }

        # アラート抑制ルール（重複アラート防止）
        self.suppression_rules = {
            "duplicate_suppression": {
                "enabled": True,
                "window": 300,  # 5分間
                "similarity_threshold": 0.9,
            },
            "rate_limiting": {
                "enabled": True,
                "max_alerts_per_minute": 10,
                "max_alerts_per_type": 5,
            },
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        request_type = request.get("type", "monitor")

        if request_type == "monitor":
            return await self._monitor_metrics(request)
        elif request_type == "configure_rule":
            return await self._configure_rule(request)
        elif request_type == "get_alerts":
            return await self._get_alerts(request)
        elif request_type == "acknowledge_alert":
            return await self._acknowledge_alert(request)
        elif request_type == "resolve_alert":
            return await self._resolve_alert(request)
        elif request_type == "get_statistics":
            return await self._get_statistics(request)
        else:
            return {"success": False, "error": f"Unknown request type: {request_type}"}

    async def monitor_metrics(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """メトリクス監視"""
        try:
            timestamp = datetime.now()
            alerts_generated = []

            # 各メトリクスを時間窓に追加
            for metric_name, value in metrics.items():
                if metric_name not in self.metric_windows:
                    # デフォルト10分窓
                    self.metric_windows[metric_name] = MetricWindow(
                        metric_name=metric_name,
                        values=deque(),
                        timestamps=deque(),
                        window_size=600,
                    )

                self.metric_windows[metric_name].add_value(value, timestamp)

            # 各ルールをチェック
            for rule_name, rule_config in self.alert_rules.items():
                alert = await self._check_rule(rule_name, rule_config, metrics)
                if alert:
                    # 重複チェック
                    if not await self._is_duplicate_alert(alert):
                        alerts_generated.append(alert)
                        await self._process_alert(alert)

            # トレンド分析
            trend_alerts = await self._analyze_trends()
            alerts_generated.extend(trend_alerts)

            return {
                "success": True,
                "alerts_generated": len(alerts_generated),
                "alerts": [alert.to_dict() for alert in alerts_generated],
                "current_metrics": metrics,
            }

        except Exception as e:
            logger.error(f"❌ Metric monitoring failed: {e}")
            return {"success": False, "error": str(e)}

    async def _check_rule(
        self,
        rule_name: str,
        rule_config: Dict[str, Any],
        current_metrics: Dict[str, float],
    ) -> Optional[PreventiveAlert]:
        """ルールチェック"""
        metric_name = rule_config.get("metric")
        if metric_name not in current_metrics:
            return None

        current_value = current_metrics[metric_name]

        # 閾値チェック
        if "warning" in rule_config and "critical" in rule_config:
            warning_threshold = rule_config["warning"]
            critical_threshold = rule_config["critical"]

            severity = None
            if rule_name in ["quality_degradation"]:
                # 低い値が悪い
                if current_value <= critical_threshold:
                    severity = AlertLevel.EMERGENCY
                elif current_value <= warning_threshold:
                    severity = AlertLevel.WARNING
            else:
                # 高い値が悪い
                if current_value >= critical_threshold:
                    severity = AlertLevel.EMERGENCY
                elif current_value >= warning_threshold:
                    severity = AlertLevel.WARNING

            if severity:
                return await self._create_alert(
                    alert_type=rule_name,
                    severity=severity,
                    context={
                        "metric": metric_name,
                        "current_value": current_value,
                        "threshold": (
                            warning_threshold
                            if severity == AlertLevel.WARNING
                            else critical_threshold
                        ),
                        "rule_config": rule_config,
                    },
                )

        # ベースライン比較
        if "baseline_multiplier" in rule_config:
            return await self._check_baseline_rule(
                rule_name, rule_config, current_value
            )

        return None

    async def _check_baseline_rule(
        self, rule_name: str, rule_config: Dict[str, Any], current_value: float
    ) -> Optional[PreventiveAlert]:
        """ベースライン比較ルールチェック"""
        metric_name = rule_config.get("metric")
        window = self.metric_windows.get(metric_name)

        if not window or len(window.values) < rule_config.get("min_baseline_count", 10):
            return None

        stats = window.get_statistics()
        baseline = stats["mean"]

        if baseline == 0:
            return None

        ratio = current_value / baseline
        warning_multiplier = rule_config.get("baseline_multiplier", 2.0)
        critical_multiplier = rule_config.get("critical_multiplier", 5.0)

        severity = None
        if ratio >= critical_multiplier:
            severity = AlertLevel.EMERGENCY
        elif ratio >= warning_multiplier:
            severity = AlertLevel.WARNING

        if severity:
            return await self._create_alert(
                alert_type=f"{rule_name}_spike",
                severity=severity,
                context={
                    "metric": metric_name,
                    "current_value": current_value,
                    "baseline": baseline,
                    "ratio": ratio,
                    "statistics": stats,
                },
            )

        return None

    async def _analyze_trends(self) -> List[PreventiveAlert]:
        """トレンド分析"""
        alerts = []

        for metric_name, window in self.metric_windows.items():
            if len(window.values) < 10:
                continue

            # 線形回帰によるトレンド検出
            values = list(window.values)
            timestamps = [
                (t - window.timestamps[0]).total_seconds() for t in window.timestamps
            ]

            if len(values) >= 5:
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    timestamps, values
                )

                # 有意な上昇トレンド検出
                if p_value < 0.5 and slope > 0:
                    # 現在の増加率を計算
                    current_rate = slope * 60  # 分あたりの増加

                    # 将来の予測
                    future_minutes = 10
                    predicted_value = values[-1] + (current_rate * future_minutes)

                    # 予測値が閾値を超える場合はアラート
                    for rule_name, rule_config in self.alert_rules.items():
                        if rule_config.get("metric") == metric_name:
                            threshold = rule_config.get("critical", float("inf"))
                            if predicted_value >= threshold:
                                alert = await self._create_alert(
                                    alert_type=f"{metric_name}_trend_warning",
                                    severity=AlertLevel.WARNING,
                                    context={
                                        "metric": metric_name,
                                        "current_value": values[-1],
                                        "trend_slope": slope,
                                        "predicted_value": predicted_value,
                                        "time_to_threshold": future_minutes,
                                        "confidence": abs(r_value),
                                    },
                                )
                                if alert:
                                    alerts.append(alert)

        return alerts

    async def _create_alert(
        self, alert_type: str, severity: AlertLevel, context: Dict[str, Any]
    ) -> PreventiveAlert:
        """アラート作成"""
        alert = PreventiveAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            message=self._format_alert_message(alert_type, severity, context),
            context=context,
            created_at=datetime.now(),
        )

        # 統計更新
        self.alert_stats["total_alerts"] += 1
        self.alert_stats["alerts_by_severity"][severity.value] += 1
        self.alert_stats["alerts_by_type"][alert_type] += 1

        return alert

    def _format_alert_message(
        self, alert_type: str, severity: AlertLevel, context: Dict[str, Any]
    ) -> str:
        """アラートメッセージフォーマット"""
        metric = context.get("metric", "unknown")
        current_value = context.get("current_value", 0)

        messages = {
            "quality_degradation": f"Quality score degraded to {current_value:0.2f}",
            "failure_rate": f"Failure rate increased to {current_value:0.2%}",
            "response_time": f"Response time increased to {current_value:0.2f}s",
            "error_spike": f"Error rate spiked to {current_value:0.f} errors/min",
            "resource_exhaustion": f"Resource usage at {current_value:0.1%}",
        }

        base_message = messages.get(alert_type, f"{metric} alert triggered")

        if "trend_warning" in alert_type:
            predicted = context.get("predicted_value", 0)
            minutes = context.get("time_to_threshold", 0)
            base_message = f"{metric} trending up, will reach critical in {minutes} minutes (predicted: " \
                "{predicted:0.2f})"

        return f"[{severity.value.upper()}] {base_message}"

    async def _is_duplicate_alert(self, alert: PreventiveAlert) -> bool:
        """重複アラートチェック"""
        if not self.suppression_rules["duplicate_suppression"]["enabled"]:
            return False

        window = self.suppression_rules["duplicate_suppression"]["window"]
        threshold = self.suppression_rules["duplicate_suppression"][
            "similarity_threshold"
        ]

        cutoff = datetime.now() - timedelta(seconds=window)
        recent_alerts = [a for a in self.alert_history if a.created_at > cutoff]

        for recent in recent_alerts:
            if recent.alert_type == alert.alert_type:
                # コンテキストの類似度チェック
                similarity = self._calculate_similarity(alert.context, recent.context)
                if similarity >= threshold:
                    return True

        return False

    def _calculate_similarity(self, context1: Dict, context2: Dict) -> float:
        """コンテキスト類似度計算"""
        if not context1 or not context2:
            return 0.0

        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0

        matches = 0
        for key in common_keys:
            if context1[key] == context2[key]:
                matches += 1
            elif isinstance(context1[key], (int, float)) and isinstance(
                context2[key], (int, float)
            ):
                # 数値の場合は近似値チェック
                if (
                    abs(context1[key] - context2[key])
                    / max(abs(context1[key]), abs(context2[key]), 1)
                    < 0.1
                ):
                    matches += 0.5

        return matches / len(common_keys)

    async def _process_alert(self, alert: PreventiveAlert):
        """アラート処理"""
        # 履歴に追加
        self.alert_history.append(alert)

        # Incident Sageに通知
        await self._notify_incident_sage(alert)

        # カスタムハンドラー実行
        if alert.alert_type in self.alert_handlers:
            await self.alert_handlers[alert.alert_type](alert)

        # エスカレーション判定
        if alert.severity in [AlertLevel.EMERGENCY, AlertLevel.ALERT]:
            await self._escalate_alert(alert)

        logger.warning(f"🚨 Alert generated: {alert.message}")

    async def _notify_incident_sage(self, alert: PreventiveAlert):
        """Incident Sageへの通知"""
        try:
            # アラートをインシデントとして登録
            response = await self.incident_sage.process_request(
                {
                    "type": "create_alert",
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "data": {
                        "alert_id": alert.alert_id,
                        "context": alert.context,
                        "metadata": alert.metadata,
                    },
                }
            )

            if response.get("success"):
                alert.incident_id = response.get("alert_id")
                logger.info(f"✅ Alert forwarded to Incident Sage: {alert.incident_id}")

        except Exception as e:
            logger.error(f"❌ Failed to notify Incident Sage: {e}")

    async def _escalate_alert(self, alert: PreventiveAlert):
        """アラートエスカレーション"""
        escalation_config = self.escalation_policy.get(alert.severity)
        if not escalation_config:
            return

        # エスカレーション遅延
        delay = escalation_config.get("initial_delay", 0)
        if delay > 0:
            await asyncio.sleep(delay)

        # アラートがまだアクティブか確認
        if alert.resolved_at:
            return

        # エスカレーション実行
        escalate_to = escalation_config.get("escalate_to")
        if escalate_to:
            alert.severity = escalate_to
            alert.actions_taken.append(f"Escalated to {escalate_to.value}")

        # 通知チャネル
        notify_channels = escalation_config.get("notify_channels", [])
        for channel in notify_channels:
            await self._notify_channel(channel, alert)

    async def _notify_channel(self, channel: str, alert: PreventiveAlert):
        """通知チャネルへの送信"""
        logger.info(f"📢 Notifying {channel}: {alert.message}")
        # 実際の通知実装はチャネルごとに異なる

    async def register_alert_handler(self, alert_type: str, handler: Callable):
        """カスタムアラートハンドラー登録"""
        self.alert_handlers[alert_type] = handler
        logger.info(f"✅ Registered handler for {alert_type}")

    async def _monitor_metrics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス監視リクエスト処理"""
        metrics = request.get("metrics", {})
        return await self.monitor_metrics(metrics)

    async def _configure_rule(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ルール設定リクエスト処理"""
        rule_name = request.get("rule_name")
        rule_config = request.get("rule_config")

        if not rule_name or not rule_config:
            return {"success": False, "error": "rule_name and rule_config required"}

        self.alert_rules[rule_name] = rule_config
        return {"success": True, "message": f"Rule {rule_name} configured"}

    async def _get_alerts(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """アラート取得リクエスト処理"""
        limit = request.get("limit", 100)
        severity = request.get("severity")
        alert_type = request.get("alert_type")
        active_only = request.get("active_only", False)

        alerts = self.alert_history[-limit:]

        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if active_only:
            alerts = [a for a in alerts if not a.resolved_at]

        return {
            "success": True,
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
        }

    async def _acknowledge_alert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """アラート確認リクエスト処理"""
        alert_id = request.get("alert_id")

        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.acknowledged_at = datetime.now()
                alert.actions_taken.append("Acknowledged")
                return {"success": True, "message": "Alert acknowledged"}

        return {"success": False, "error": "Alert not found"}

    async def _resolve_alert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """アラート解決リクエスト処理"""
        alert_id = request.get("alert_id")
        resolution = request.get("resolution", "Resolved")

        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.resolved_at = datetime.now()
                alert.actions_taken.append(f"Resolved: {resolution}")
                return {"success": True, "message": "Alert resolved"}

        return {"success": False, "error": "Alert not found"}

    async def _get_statistics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """統計取得リクエスト処理"""
        return {
            "success": True,
            "statistics": {
                "total_alerts": self.alert_stats["total_alerts"],
                "by_severity": dict(self.alert_stats["alerts_by_severity"]),
                "by_type": dict(self.alert_stats["alerts_by_type"]),
                "false_positive_rate": self.alert_stats["false_positive_rate"],
                "active_alerts": sum(
                    1 for a in self.alert_history if not a.resolved_at
                ),
                "average_resolution_time": self._calculate_avg_resolution_time(),
            },
        }

    def _calculate_avg_resolution_time(self) -> float:
        """平均解決時間計算"""
        resolved_alerts = [a for a in self.alert_history if a.resolved_at]
        if not resolved_alerts:
            return 0.0

        total_time = sum(
            (a.resolved_at - a.created_at).total_seconds() for a in resolved_alerts
        )
        return total_time / len(resolved_alerts)

    def get_capabilities(self) -> List[str]:
        """能力一覧"""
        return [
            "real_time_monitoring",
            "threshold_based_alerts",
            "trend_analysis",
            "predictive_alerts",
            "alert_suppression",
            "escalation_management",
            "custom_handlers",
            "statistical_analysis",
        ]


# エクスポート
__all__ = ["PreventiveAlertSystem", "PreventiveAlert", "MetricWindow"]

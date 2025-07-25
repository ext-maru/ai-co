"""
Quality Metrics Monitor - 品質メトリクス監視システム

Issue #309: 自動化品質パイプライン実装 - Phase 4
目的: UnifiedQualityPipeline の品質メトリクス監視・アラートシステム
方針: リアルタイム監視・Elder Council承認率追跡・パイプライン効率アラート
"""

import asyncio
import time
import logging
import json
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from collections import deque
import threading
from enum import Enum


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class MetricType(Enum):
    """メトリクス種別"""
    QUALITY_SCORE = "quality_score"
    EXECUTION_TIME = "execution_time"
    ELDER_APPROVAL_RATE = "elder_approval_rate"
    PIPELINE_EFFICIENCY = "pipeline_efficiency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class QualityMetric:
    """品質メトリクス"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    pipeline_id: str
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityAlert:
    """品質アラート"""
    alert_id: str
    alert_level: AlertLevel
    metric_type: MetricType
    message: str
    current_value: float
    threshold_value: float
    pipeline_id: Optional[str]
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    elder_council_notified: bool = False


@dataclass
class MonitoringReport:
    """監視レポート"""
    report_id: str
    period_start: datetime
    period_end: datetime
    total_executions: int
    successful_executions: int
    average_quality_score: float
    elder_approval_rate: float
    average_execution_time: float
    pipeline_efficiency_trend: str
    active_alerts: List[QualityAlert]
    resolved_alerts: List[QualityAlert]
    recommendations: List[str]
    elder_council_summary: Dict[str, Any]
    timestamp: datetime


class QualityMetricsMonitor:
    """
    品質メトリクス監視システム
    
    UnifiedQualityPipeline の実行を監視し、品質メトリクスを収集・分析
    アラート生成・Elder Council報告・トレンド分析を自動実行
    """
    
    def __init__(self, monitoring_interval: float = 30.0):
        self.monitor_id = "QMM-ELDER-001"
        self.logger = self._setup_logger()
        self.monitoring_interval = monitoring_interval
        
        # メトリクス閾値設定
        self.thresholds = {
            MetricType.QUALITY_SCORE: {
                "warning": 85.0,
                "critical": 75.0,
                "emergency": 60.0
            },
            MetricType.EXECUTION_TIME: {
                "warning": 20.0,  # 20秒
                "critical": 30.0,  # 30秒
                "emergency": 45.0  # 45秒
            },
            MetricType.ELDER_APPROVAL_RATE: {
                "warning": 90.0,  # 90%
                "critical": 80.0,  # 80%
                "emergency": 70.0  # 70%
            },
            MetricType.PIPELINE_EFFICIENCY: {
                "warning": 70.0,  # 70%
                "critical": 60.0,  # 60%
                "emergency": 50.0  # 50%
            },
            MetricType.ERROR_RATE: {
                "warning": 5.0,   # 5%
                "critical": 10.0,  # 10%
                "emergency": 20.0  # 20%
            }
        }
        
        # メトリクス履歴（最新1000件）
        self.metrics_history = {
            metric_type: deque(maxlen=1000) 
            for metric_type in MetricType
        }
        
        # アクティブアラート管理
        self.active_alerts = {}
        self.resolved_alerts = deque(maxlen=500)
        
        # アラート通知コールバック
        self.alert_callbacks = []
        
        # 監視スレッド
        self._monitoring_active = False
        self._monitoring_thread = None
        
        # Elder Council報告設定
        self.elder_council_reporting = {
            "enabled": True,
            "report_interval": 3600.0,  # 1時間毎
            "last_report_time": datetime.now(),
            "auto_escalation": True
        }
        
        self.logger.info(f"📊 Quality Metrics Monitor initialized: {self.monitor_id}")
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("quality_metrics_monitor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start_monitoring(self):
        """監視開始"""
        if self._monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        
        self.logger.info(f"🔄 Quality monitoring started (interval: {self.monitoring_interval}s)")
    
    def stop_monitoring(self):
        """監視停止"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)
        
        self.logger.info("⏹️ Quality monitoring stopped")
    
    def record_pipeline_execution(
        self, 
        pipeline_result,
        execution_time: float,
        pipeline_id: str
    ):
        """
        パイプライン実行結果記録
        
        Args:
            pipeline_result: UnifiedQualityResult
            execution_time: 実行時間
            pipeline_id: パイプラインID
        """
        timestamp = datetime.now()
        
        # 品質スコアメトリクス
        if hasattr(pipeline_result, 'unified_quality_score'):
            self._record_metric(
                MetricType.QUALITY_SCORE,
                pipeline_result.unified_quality_score,
                timestamp,
                pipeline_id,
                {"overall_status": pipeline_result.overall_status}
            )
        
        # 実行時間メトリクス
        self._record_metric(
            MetricType.EXECUTION_TIME,
            execution_time,
            timestamp,
            pipeline_id
        )
        
        # Elder承認率計算・記録
        elder_approval = 1.0 if pipeline_result.overall_status == "ELDER_APPROVED" else 0.0
        self._record_metric(
            MetricType.ELDER_APPROVAL_RATE,
            elder_approval,
            timestamp,
            pipeline_id
        )
        
        # パイプライン効率メトリクス
        if hasattr(pipeline_result, 'pipeline_efficiency'):
            self._record_metric(
                MetricType.PIPELINE_EFFICIENCY,
                pipeline_result.pipeline_efficiency,
                timestamp,
                pipeline_id
            )
        
        # エラー率メトリクス
        error_rate = 0.0 if pipeline_result.overall_status != "ELDER_REJECTED" else 1.0
        self._record_metric(
            MetricType.ERROR_RATE,
            error_rate,
            timestamp,
            pipeline_id
        )
        
        self.logger.info(f"📈 Pipeline metrics recorded: {pipeline_id}")
    
    def _record_metric(
        self,
        metric_type: MetricType,
        value: float,
        timestamp: datetime,
        pipeline_id: str,
        additional_data: Dict[str, Any] = None
    ):
        """メトリクス記録"""
        metric = QualityMetric(
            metric_type=metric_type,
            value=value,
            timestamp=timestamp,
            pipeline_id=pipeline_id,
            additional_data=additional_data or {}
        )
        
        self.metrics_history[metric_type].append(metric)
        
        # 閾値チェック・アラート生成
        self._check_threshold_and_alert(metric)
    
    def _check_threshold_and_alert(self, metric: QualityMetric):
        """閾値チェック・アラート生成"""
        if metric.metric_type not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric.metric_type]
        alert_level = None
        threshold_value = None
        
        # メトリクス種別による閾値判定ロジック
        if metric.metric_type in [MetricType.QUALITY_SCORE, MetricType.ELDER_APPROVAL_RATE, MetricType.PIPELINE_EFFICIENCY]:
            # 値が低いほど悪い（品質スコア、承認率、効率）
            if metric.value <= thresholds["emergency"]:
                alert_level = AlertLevel.EMERGENCY
                threshold_value = thresholds["emergency"]
            elif metric.value <= thresholds["critical"]:
                alert_level = AlertLevel.CRITICAL
                threshold_value = thresholds["critical"]
            elif metric.value <= thresholds["warning"]:
                alert_level = AlertLevel.WARNING
                threshold_value = thresholds["warning"]
        
        elif metric.metric_type in [MetricType.EXECUTION_TIME, MetricType.ERROR_RATE]:
            # 値が高いほど悪い（実行時間、エラー率）
            if metric.value >= thresholds["emergency"]:
                alert_level = AlertLevel.EMERGENCY
                threshold_value = thresholds["emergency"]
            elif metric.value >= thresholds["critical"]:
                alert_level = AlertLevel.CRITICAL
                threshold_value = thresholds["critical"]
            elif metric.value >= thresholds["warning"]:
                alert_level = AlertLevel.WARNING
                threshold_value = thresholds["warning"]
        
        # アラート生成
        if alert_level:
            self._generate_alert(
                alert_level,
                metric.metric_type,
                metric.value,
                threshold_value,
                metric.pipeline_id
            )
    
    def _generate_alert(
        self,
        alert_level: AlertLevel,
        metric_type: MetricType,
        current_value: float,
        threshold_value: float,
        pipeline_id: Optional[str]
    ):
        """アラート生成"""
        alert_id = f"ALERT-{int(time.time())}-{metric_type.value}"
        
        # アラートメッセージ生成
        message = self._generate_alert_message(
            alert_level, metric_type, current_value, threshold_value
        )
        
        alert = QualityAlert(
            alert_id=alert_id,
            alert_level=alert_level,
            metric_type=metric_type,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
            pipeline_id=pipeline_id,
            timestamp=datetime.now()
        )
        
        # 重複アラート回避（同じメトリクス種別の既存アラートをチェック）
        existing_key = f"{metric_type.value}-{alert_level.value}"
        if existing_key not in self.active_alerts:
            self.active_alerts[existing_key] = alert
            
            # アラート通知
            self._notify_alert(alert)
            
            # Elder Council自動エスカレーション
            if (alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY] and 
                self.elder_council_reporting["auto_escalation"]):
                self._escalate_to_elder_council(alert)
            
            self.logger.warning(f"🚨 {alert_level.value} Alert generated: {message}")
    
    def _generate_alert_message(
        self,
        alert_level: AlertLevel,
        metric_type: MetricType,
        current_value: float,
        threshold_value: float
    ) -> str:
        """アラートメッセージ生成"""
        metric_descriptions = {
            MetricType.QUALITY_SCORE: "品質スコア",
            MetricType.EXECUTION_TIME: "実行時間",
            MetricType.ELDER_APPROVAL_RATE: "Elder承認率",
            MetricType.PIPELINE_EFFICIENCY: "パイプライン効率",
            MetricType.ERROR_RATE: "エラー率"
        }
        
        metric_name = metric_descriptions.get(metric_type, metric_type.value)
        
        if metric_type in [MetricType.QUALITY_SCORE, MetricType.ELDER_APPROVAL_RATE, MetricType.PIPELINE_EFFICIENCY]:
            return f"{metric_name}が閾値を下回りました: {current_value:.1f} < {threshold_value:.1f}"
        else:
            return f"{metric_name}が閾値を上回りました: {current_value:.1f} > {threshold_value:.1f}"
    
    def _notify_alert(self, alert: QualityAlert):
        """アラート通知"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def _escalate_to_elder_council(self, alert: QualityAlert):
        """Elder Council エスカレーション"""
        escalation_report = {
            "escalation_type": "QUALITY_ALERT_ESCALATION",
            "alert_id": alert.alert_id,
            "alert_level": alert.alert_level.value,
            "metric_type": alert.metric_type.value,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "monitoring_authority": self.monitor_id,
            "recommended_actions": self._get_recommended_actions(alert)
        }
        
        alert.elder_council_notified = True
        
        self.logger.critical(
            f"⚠️ ELDER COUNCIL ESCALATION: {alert.alert_level.value} - {alert.message}"
        )
    
    def _get_recommended_actions(self, alert: QualityAlert) -> List[str]:
        """推奨アクション取得"""
        action_map = {
            MetricType.QUALITY_SCORE: [
                "品質基準の見直し実施",
                "追加テスト実装の検討",
                "コードレビュープロセス強化"
            ],
            MetricType.EXECUTION_TIME: [
                "パフォーマンス最適化の実行",
                "並列実行効率の改善",
                "ボトルネック分析の実施"
            ],
            MetricType.ELDER_APPROVAL_RATE: [
                "品質基準の再校正",
                "Elder判定基準の見直し",
                "自動修正機能の強化"
            ],
            MetricType.PIPELINE_EFFICIENCY: [
                "パイプライン構成の最適化",
                "リソース配分の見直し",
                "並列処理の改善"
            ],
            MetricType.ERROR_RATE: [
                "エラーハンドリングの強化",
                "自動復旧機能の実装",
                "根本原因分析の実施"
            ]
        }
        
        return action_map.get(alert.metric_type, ["詳細調査の実施"])
    
    def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """アラート解決"""
        # アクティブアラートから検索
        resolved_alert = None
        for key, alert in list(self.active_alerts.items()):
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_timestamp = datetime.now()
                resolved_alert = alert
                del self.active_alerts[key]
                break
        
        if resolved_alert:
            self.resolved_alerts.append(resolved_alert)
            self.logger.info(f"✅ Alert resolved: {alert_id} - {resolution_note}")
        else:
            self.logger.warning(f"Alert not found for resolution: {alert_id}")
    
    def get_current_metrics_summary(self) -> Dict[str, Any]:
        """現在のメトリクス概要取得"""
        summary = {}
        
        for metric_type in MetricType:
            history = self.metrics_history[metric_type]
            if not history:
                summary[metric_type.value] = {
                    "current_value": None,
                    "average_1h": None,
                    "trend": "NO_DATA"
                }
                continue
            
            # 最新値
            current_value = history[-1].value
            
            # 過去1時間の平均
            hour_ago = datetime.now() - timedelta(hours=1)
            recent_values = [
                m.value for m in history 
                if m.timestamp >= hour_ago
            ]
            average_1h = statistics.mean(recent_values) if recent_values else None
            
            # トレンド計算（簡易）
            trend = "STABLE"
            if len(recent_values) >= 10:
                first_half = statistics.mean(recent_values[:len(recent_values)//2])
                second_half = statistics.mean(recent_values[len(recent_values)//2:])
                
                if second_half > first_half * 1.05:
                    trend = "IMPROVING" if metric_type in [MetricType.QUALITY_SCORE, MetricType.ELDER_APPROVAL_RATE, MetricType.PIPELINE_EFFICIENCY] else "DEGRADING"
                elif second_half < first_half * 0.95:
                    trend = "DEGRADING" if metric_type in [MetricType.QUALITY_SCORE, MetricType.ELDER_APPROVAL_RATE, MetricType.PIPELINE_EFFICIENCY] else "IMPROVING"
            
            summary[metric_type.value] = {
                "current_value": current_value,
                "average_1h": average_1h,
                "trend": trend
            }
        
        return summary
    
    def generate_monitoring_report(
        self,
        period_hours: int = 24
    ) -> MonitoringReport:
        """監視レポート生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)
        
        # 期間内のメトリクス取得
        period_metrics = {}
        for metric_type in MetricType:
            period_metrics[metric_type] = [
                m for m in self.metrics_history[metric_type]
                if start_time <= m.timestamp <= end_time
            ]
        
        # 実行統計計算
        quality_metrics = period_metrics[MetricType.QUALITY_SCORE]
        approval_metrics = period_metrics[MetricType.ELDER_APPROVAL_RATE]
        execution_metrics = period_metrics[MetricType.EXECUTION_TIME]
        efficiency_metrics = period_metrics[MetricType.PIPELINE_EFFICIENCY]
        
        total_executions = len(quality_metrics)
        successful_executions = sum(1 for m in approval_metrics if m.value > 0.5)
        
        average_quality_score = statistics.mean([m.value for m in quality_metrics]) if quality_metrics else 0.0
        elder_approval_rate = (successful_executions / total_executions * 100.0) if total_executions > 0 else 0.0
        average_execution_time = statistics.mean([m.value for m in execution_metrics]) if execution_metrics else 0.0
        
        # 効率トレンド分析
        efficiency_trend = "STABLE"
        if len(efficiency_metrics) >= 10:
            first_half = statistics.mean([m.value for m in efficiency_metrics[:len(efficiency_metrics)//2]])
            second_half = statistics.mean([m.value for m in efficiency_metrics[len(efficiency_metrics)//2:]])
            
            if second_half > first_half * 1.05:
                efficiency_trend = "IMPROVING"
            elif second_half < first_half * 0.95:
                efficiency_trend = "DEGRADING"
        
        # アクティブ・解決済みアラート
        active_alerts = list(self.active_alerts.values())
        resolved_alerts = [a for a in self.resolved_alerts if start_time <= a.timestamp <= end_time]
        
        # 推奨事項生成
        recommendations = self._generate_monitoring_recommendations(
            average_quality_score, elder_approval_rate, average_execution_time, active_alerts
        )
        
        # Elder Council概要
        elder_council_summary = {
            "monitoring_period": f"{period_hours}時間",
            "overall_health": "GOOD" if elder_approval_rate >= 90.0 else "NEEDS_ATTENTION" if elder_approval_rate >= 75.0 else "CRITICAL",
            "critical_alerts_count": sum(1 for a in active_alerts if a.alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]),
            "quality_trend": efficiency_trend,
            "monitoring_authority": self.monitor_id
        }
        
        return MonitoringReport(
            report_id=f"QMR-{int(time.time())}",
            period_start=start_time,
            period_end=end_time,
            total_executions=total_executions,
            successful_executions=successful_executions,
            average_quality_score=average_quality_score,
            elder_approval_rate=elder_approval_rate,
            average_execution_time=average_execution_time,
            pipeline_efficiency_trend=efficiency_trend,
            active_alerts=active_alerts,
            resolved_alerts=resolved_alerts,
            recommendations=recommendations,
            elder_council_summary=elder_council_summary,
            timestamp=datetime.now()
        )
    
    def _generate_monitoring_recommendations(
        self,
        avg_quality: float,
        approval_rate: float,
        avg_execution_time: float,
        active_alerts: List[QualityAlert]
    ) -> List[str]:
        """監視推奨事項生成"""
        recommendations = []
        
        if avg_quality < 85.0:
            recommendations.append("品質スコア向上のための包括的レビュー実施")
        
        if approval_rate < 90.0:
            recommendations.append("Elder承認率改善のための品質基準見直し")
        
        if avg_execution_time > 20.0:
            recommendations.append("実行時間短縮のためのパフォーマンス最適化")
        
        if len(active_alerts) > 5:
            recommendations.append("アクティブアラート削減のための優先対応")
        
        critical_alerts = [a for a in active_alerts if a.alert_level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]]
        if critical_alerts:
            recommendations.append("緊急アラートの即座対応・根本原因調査")
        
        if not recommendations:
            recommendations.append("現在の品質レベル維持・継続監視")
        
        return recommendations
    
    def _monitoring_loop(self):
        """監視ループ（バックグラウンド実行）"""
        while self._monitoring_active:
            try:
                # Elder Council定期報告
                if self._should_generate_elder_report():
                    report = self.generate_monitoring_report()
                    self._send_elder_council_report(report)
                    self.elder_council_reporting["last_report_time"] = datetime.now()
                
                # アラート状態チェック
                self._check_alert_auto_resolution()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}", exc_info=True)
                time.sleep(self.monitoring_interval)
    
    def _should_generate_elder_report(self) -> bool:
        """Elder Council報告生成判定"""
        if not self.elder_council_reporting["enabled"]:
            return False
        
        time_since_last = datetime.now() - self.elder_council_reporting["last_report_time"]
        return time_since_last.total_seconds() >= self.elder_council_reporting["report_interval"]
    
    def _send_elder_council_report(self, report: MonitoringReport):
        """Elder Council報告送信"""
        self.logger.info(
            f"📋 Elder Council Report: {report.elder_approval_rate:.1f}% approval rate, "
            f"{len(report.active_alerts)} active alerts"
        )
    
    def _check_alert_auto_resolution(self):
        """アラート自動解決チェック"""
        current_time = datetime.now()
        auto_resolve_threshold = timedelta(hours=2)  # 2時間後に自動解決候補
        
        for key, alert in list(self.active_alerts.items()):
            if current_time - alert.timestamp > auto_resolve_threshold:
                # 最新メトリクスで閾値チェック
                if alert.metric_type in self.metrics_history:
                    recent_metrics = list(self.metrics_history[alert.metric_type])[-5:]  # 最新5件
                    if recent_metrics and self._is_alert_resolved(alert, recent_metrics):
                        self.resolve_alert(alert.alert_id, "自動解決: メトリクス改善確認")
    
    def _is_alert_resolved(self, alert: QualityAlert, recent_metrics: List[QualityMetric]) -> bool:
        """アラート解決判定"""
        if not recent_metrics:
            return False
        
        recent_values = [m.value for m in recent_metrics]
        avg_recent = statistics.mean(recent_values)
        
        # 閾値チェック（アラート生成時の逆条件）
        if alert.metric_type in [MetricType.QUALITY_SCORE, MetricType.ELDER_APPROVAL_RATE, MetricType.PIPELINE_EFFICIENCY]:
            return avg_recent > alert.threshold_value * 1.05  # 5%マージン
        elif alert.metric_type in [MetricType.EXECUTION_TIME, MetricType.ERROR_RATE]:
            return avg_recent < alert.threshold_value * 0.95  # 5%マージン
        
        return False
    
    def add_alert_callback(self, callback: Callable[[QualityAlert], None]):
        """アラート通知コールバック追加"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[QualityAlert], None]):
        """アラート通知コールバック削除"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """監視統計取得"""
        total_metrics = sum(len(history) for history in self.metrics_history.values())
        total_active_alerts = len(self.active_alerts)
        total_resolved_alerts = len(self.resolved_alerts)
        
        return {
            "monitor_id": self.monitor_id,
            "monitoring_active": self._monitoring_active,
            "total_metrics_recorded": total_metrics,
            "active_alerts_count": total_active_alerts,
            "resolved_alerts_count": total_resolved_alerts,
            "monitoring_uptime": "継続中" if self._monitoring_active else "停止中",
            "elder_council_reporting": self.elder_council_reporting["enabled"],
            "last_elder_report": self.elder_council_reporting["last_report_time"].isoformat()
        }
    
    def __del__(self):
        """クリーンアップ"""
        self.stop_monitoring()

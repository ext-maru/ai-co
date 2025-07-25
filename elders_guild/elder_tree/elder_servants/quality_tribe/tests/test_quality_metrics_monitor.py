"""
Tests for Quality Metrics Monitor - 品質メトリクス監視システムテスト

TDD Cycle: Red → Green → Refactor
Issue #309: 自動化品質パイプライン実装 - Phase 4
目的: 品質メトリクス監視システムの完全テスト
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

# Test imports
from elders_guild.elder_tree.quality.quality_metrics_monitor import (
    QualityMetricsMonitor, QualityMetric, QualityAlert, MonitoringReport,
    AlertLevel, MetricType
)


class TestQualityMetricsMonitor:
    """品質メトリクス監視システム完全テスト"""
    
    @pytest.fixture
    def monitor(self):
        """モニターインスタンス作成"""
        return QualityMetricsMonitor(monitoring_interval=0.1)  # テスト用短い間隔
    
    @pytest.fixture
    def mock_pipeline_result(self):
        """モックパイプライン結果作成"""
        result = MagicMock()
        result.unified_quality_score = 92.5
        result.overall_status = "ELDER_APPROVED"
        result.pipeline_efficiency = 88.0
        return result
    
    @pytest.fixture
    def mock_poor_pipeline_result(self):
        """低品質モックパイプライン結果作成"""
        result = MagicMock()
        result.unified_quality_score = 65.0  # 闾値以下
        result.overall_status = "ELDER_REJECTED"
        result.pipeline_efficiency = 45.0  # 闾値以下
        return result
    
    def test_quality_metrics_monitor_initialization(self, monitor):
        """🔴 Red: 品質メトリクスモニター初期化テスト"""
        assert monitor is not None
        assert monitor.monitor_id == "QMM-ELDER-001"
        assert monitor.monitoring_interval == 0.1
        assert hasattr(monitor, 'thresholds')
        assert hasattr(monitor, 'metrics_history')
        assert hasattr(monitor, 'active_alerts')
        assert hasattr(monitor, 'resolved_alerts')
        
        # 闾値設定確認
        assert MetricType.QUALITY_SCORE in monitor.thresholds
        assert monitor.thresholds[MetricType.QUALITY_SCORE]["critical"] == 75.0
        assert monitor.thresholds[MetricType.EXECUTION_TIME]["warning"] == 20.0
        
        # メトリクス履歴初期化確認
        assert len(monitor.metrics_history) == len(MetricType)
        for metric_type in MetricType:
            assert metric_type in monitor.metrics_history
    
    def test_pipeline_execution_recording(self, monitor, mock_pipeline_result):
        """🔴 Red: パイプライン実行記録テスト"""
        pipeline_id = "TEST-PIPELINE-001"
        execution_time = 15.5
        
        # 実行記録
        monitor.record_pipeline_execution(
            mock_pipeline_result, execution_time, pipeline_id
        )
        
        # メトリクス記録確認
        assert len(monitor.metrics_history[MetricType.QUALITY_SCORE]) == 1
        assert len(monitor.metrics_history[MetricType.EXECUTION_TIME]) == 1
        assert len(monitor.metrics_history[MetricType.ELDER_APPROVAL_RATE]) == 1
        assert len(monitor.metrics_history[MetricType.PIPELINE_EFFICIENCY]) == 1
        assert len(monitor.metrics_history[MetricType.ERROR_RATE]) == 1
        
        # 各メトリクス値確認
        quality_metric = monitor.metrics_history[MetricType.QUALITY_SCORE][0]
        assert quality_metric.value == 92.5
        assert quality_metric.pipeline_id == pipeline_id
        
        execution_metric = monitor.metrics_history[MetricType.EXECUTION_TIME][0]
        assert execution_metric.value == 15.5
        
        approval_metric = monitor.metrics_history[MetricType.ELDER_APPROVAL_RATE][0]
        assert approval_metric.value == 1.0  # ELDER_APPROVED = 1.0
        
        error_metric = monitor.metrics_history[MetricType.ERROR_RATE][0]
        assert error_metric.value == 0.0  # 成功時は0.0
    
    def test_threshold_alert_generation(self, monitor, mock_poor_pipeline_result):
        """🔴 Red: 闾値アラート生成テスト"""
        pipeline_id = "TEST-PIPELINE-POOR"
        execution_time = 35.0  # 闾値超過 (critical: 30.0)
        
        # 低品質結果記録
        monitor.record_pipeline_execution(
            mock_poor_pipeline_result, execution_time, pipeline_id
        )
        
        # アラート生成確認
        assert len(monitor.active_alerts) > 0
        
        # 品質スコアアラート確認 (65.0 < 75.0)
        quality_alert_key = f"{MetricType.QUALITY_SCORE.value}-{AlertLevel.CRITICAL.value}"
        assert quality_alert_key in monitor.active_alerts
        
        quality_alert = monitor.active_alerts[quality_alert_key]
        assert quality_alert.alert_level == AlertLevel.CRITICAL
        assert quality_alert.current_value == 65.0
        assert quality_alert.threshold_value == 75.0
        
        # 実行時間アラート確認 (35.0 > 30.0)
        execution_alert_key = f"{MetricType.EXECUTION_TIME.value}-{AlertLevel.CRITICAL.value}"
        assert execution_alert_key in monitor.active_alerts
        
        execution_alert = monitor.active_alerts[execution_alert_key]
        assert execution_alert.alert_level == AlertLevel.CRITICAL
        assert execution_alert.current_value == 35.0
        assert execution_alert.threshold_value == 30.0
    
    def test_alert_level_classification(self, monitor):
        """🔴 Red: アラートレベル分類テスト"""
        pipeline_id = "TEST-ALERT-LEVELS"
        
        # Warningレベルテスト (品質スコア: 80.0 < 85.0)
        warning_result = MagicMock()
        warning_result.unified_quality_score = 80.0
        warning_result.overall_status = "ELDER_CONDITIONAL"
        warning_result.pipeline_efficiency = 75.0
        
        monitor.record_pipeline_execution(warning_result, 15.0, pipeline_id)
        
        warning_alert_key = f"{MetricType.QUALITY_SCORE.value}-{AlertLevel.WARNING.value}"
        assert warning_alert_key in monitor.active_alerts
        assert monitor.active_alerts[warning_alert_key].alert_level == AlertLevel.WARNING
        
        # Emergencyレベルテスト (品質スコア: 55.0 < 60.0)
        monitor.active_alerts.clear()  # クリア
        
        emergency_result = MagicMock()
        emergency_result.unified_quality_score = 55.0
        emergency_result.overall_status = "ELDER_REJECTED"
        emergency_result.pipeline_efficiency = 40.0
        
        monitor.record_pipeline_execution(emergency_result, 50.0, pipeline_id)
        
        emergency_alert_key = f"{MetricType.QUALITY_SCORE.value}-{AlertLevel.EMERGENCY.value}"
        assert emergency_alert_key in monitor.active_alerts
        assert monitor.active_alerts[emergency_alert_key].alert_level == AlertLevel.EMERGENCY
    
    def test_alert_callback_system(self, monitor):
        """🔴 Red: アラートコールバックシステムテスト"""
        # コールバック関数設定
        callback_calls = []
        
        def test_callback(alert: QualityAlert):
            callback_calls.append(alert)
        
        monitor.add_alert_callback(test_callback)
        
        # アラート発生させる
        poor_result = MagicMock()
        poor_result.unified_quality_score = 70.0  # Criticalレベル
        poor_result.overall_status = "ELDER_REJECTED"
        poor_result.pipeline_efficiency = 55.0
        
        monitor.record_pipeline_execution(poor_result, 25.0, "TEST-CALLBACK")
        
        # コールバック呼び出し確認
        assert len(callback_calls) > 0
        
        # コールバック削除テスト
        monitor.remove_alert_callback(test_callback)
        callback_calls.clear()
        
        monitor.record_pipeline_execution(poor_result, 25.0, "TEST-CALLBACK-2")
        assert len(callback_calls) == 0  # コールバック削除後は呼び出しなし
    
    def test_elder_council_escalation(self, monitor):
        """🔴 Red: Elder Councilエスカレーションテスト"""
        # エスカレーション有効化
        monitor.elder_council_reporting["auto_escalation"] = True
        
        # Emergencyレベルアラート発生
        emergency_result = MagicMock()
        emergency_result.unified_quality_score = 45.0  # Emergencyレベル
        emergency_result.overall_status = "ELDER_REJECTED"
        emergency_result.pipeline_efficiency = 35.0
        
        monitor.record_pipeline_execution(emergency_result, 50.0, "TEST-ESCALATION")
        
        # エスカレーション確認
        emergency_alerts = [
            alert for alert in monitor.active_alerts.values()
            if alert.alert_level == AlertLevel.EMERGENCY and alert.elder_council_notified
        ]
        assert len(emergency_alerts) > 0
    
    def test_alert_resolution(self, monitor):
        """🔴 Red: アラート解決テスト"""
        # アラート発生
        poor_result = MagicMock()
        poor_result.unified_quality_score = 70.0
        poor_result.overall_status = "ELDER_REJECTED"
        poor_result.pipeline_efficiency = 55.0
        
        monitor.record_pipeline_execution(poor_result, 25.0, "TEST-RESOLUTION")
        
        # アクティブアラート存在確認
        assert len(monitor.active_alerts) > 0
        
        # アラートID取得
        alert_id = list(monitor.active_alerts.values())[0].alert_id
        
        # アラート解決
        monitor.resolve_alert(alert_id, "Test resolution")
        
        # 解決確認
        resolved_alert_found = False
        for resolved_alert in monitor.resolved_alerts:
            if resolved_alert.alert_id == alert_id:
                assert resolved_alert.resolved is True
                assert resolved_alert.resolution_timestamp is not None
                resolved_alert_found = True
                break
        
        assert resolved_alert_found
        
        # アクティブアラートから削除確認
        active_alert_exists = any(
            alert.alert_id == alert_id for alert in monitor.active_alerts.values()
        )
        assert not active_alert_exists
    
    def test_current_metrics_summary(self, monitor, mock_pipeline_result):
        """🔴 Red: 現在メトリクス概要テスト"""
        # 初期状態（データなし）
        summary = monitor.get_current_metrics_summary()
        assert isinstance(summary, dict)
        assert len(summary) == len(MetricType)
        
        for metric_type in MetricType:
            assert metric_type.value in summary
            assert summary[metric_type.value]["current_value"] is None
            assert summary[metric_type.value]["trend"] == "NO_DATA"
        
        # メトリクスデータ追加
        for i in range(10):
            result = MagicMock()
            result.unified_quality_score = 90.0 + i  # 漸増トレンド
            result.overall_status = "ELDER_APPROVED"
            result.pipeline_efficiency = 80.0 + i
            
            monitor.record_pipeline_execution(result, 15.0, f"TEST-{i}")
        
        # データあり概要
        summary = monitor.get_current_metrics_summary()
        
        quality_summary = summary[MetricType.QUALITY_SCORE.value]
        assert quality_summary["current_value"] == 99.0  # 最新値
        assert quality_summary["average_1h"] is not None
        assert quality_summary["trend"] in ["IMPROVING", "STABLE", "DEGRADING"]
    
    def test_monitoring_report_generation(self, monitor, mock_pipeline_result):
        """🔴 Red: 監視レポート生成テスト"""
        # テストデータ追加
        for i in range(5):
            result = MagicMock()
            result.unified_quality_score = 85.0 + i * 2
            result.overall_status = "ELDER_APPROVED" if i < 4 else "ELDER_REJECTED"
            result.pipeline_efficiency = 75.0 + i * 3
            
            monitor.record_pipeline_execution(result, 18.0 + i, f"TEST-REPORT-{i}")
        
        # レポート生成 (1時間分)
        report = monitor.generate_monitoring_report(period_hours=1)
        
        assert isinstance(report, MonitoringReport)
        assert report.report_id.startswith("QMR-")
        assert report.total_executions == 5
        assert report.successful_executions == 4  # 4回成功
        assert report.elder_approval_rate == 80.0  # 4/5 * 100
        assert report.average_quality_score > 0.0
        assert report.average_execution_time > 0.0
        assert report.pipeline_efficiency_trend in ["IMPROVING", "STABLE", "DEGRADING"]
        assert isinstance(report.active_alerts, list)
        assert isinstance(report.resolved_alerts, list)
        assert isinstance(report.recommendations, list)
        assert isinstance(report.elder_council_summary, dict)
        assert report.timestamp is not None
        
        # Elder Council概要確認
        elder_summary = report.elder_council_summary
        assert "overall_health" in elder_summary
        assert elder_summary["overall_health"] in ["GOOD", "NEEDS_ATTENTION", "CRITICAL"]
        assert "monitoring_authority" in elder_summary
        assert elder_summary["monitoring_authority"] == monitor.monitor_id
    
    def test_monitoring_loop_start_stop(self, monitor):
        """🔴 Red: 監視ループ開始・停止テスト"""
        # 初期状態
        assert not monitor._monitoring_active
        assert monitor._monitoring_thread is None
        
        # 監視開始
        monitor.start_monitoring()
        assert monitor._monitoring_active is True
        assert monitor._monitoring_thread is not None
        
        # 短時間待機
        time.sleep(0.2)
        
        # 監視停止
        monitor.stop_monitoring()
        assert monitor._monitoring_active is False
    
    def test_monitoring_statistics(self, monitor, mock_pipeline_result):
        """🔴 Red: 監視統計テスト"""
        # 初期統計
        stats = monitor.get_monitoring_statistics()
        assert isinstance(stats, dict)
        assert stats["monitor_id"] == "QMM-ELDER-001"
        assert stats["monitoring_active"] is False
        assert stats["total_metrics_recorded"] == 0
        assert stats["active_alerts_count"] == 0
        assert stats["resolved_alerts_count"] == 0
        
        # データ追加後
        monitor.record_pipeline_execution(mock_pipeline_result, 15.0, "STATS-TEST")
        
        stats = monitor.get_monitoring_statistics()
        assert stats["total_metrics_recorded"] > 0
        assert "elder_council_reporting" in stats
        assert "last_elder_report" in stats
    
    def test_recommended_actions_generation(self, monitor):
        """🔴 Red: 推奨アクション生成テスト"""
        # アラート作成
        quality_alert = QualityAlert(
            alert_id="TEST-ALERT-001",
            alert_level=AlertLevel.CRITICAL,
            metric_type=MetricType.QUALITY_SCORE,
            message="品質スコア低下",
            current_value=70.0,
            threshold_value=75.0,
            pipeline_id="TEST-PIPELINE",
            timestamp=datetime.now()
        )
        
        # 推奨アクション取得
        actions = monitor._get_recommended_actions(quality_alert)
        
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # 品質スコア関連の推奨事項確認
        assert any("品質基準" in action for action in actions)
        
        # 実行時間アラートの場合
        execution_alert = QualityAlert(
            alert_id="TEST-ALERT-002",
            alert_level=AlertLevel.WARNING,
            metric_type=MetricType.EXECUTION_TIME,
            message="実行時間超過",
            current_value=25.0,
            threshold_value=20.0,
            pipeline_id="TEST-PIPELINE",
            timestamp=datetime.now()
        )
        
        execution_actions = monitor._get_recommended_actions(execution_alert)
        assert any("パフォーマンス" in action for action in execution_actions)
    
    def test_alert_auto_resolution_logic(self, monitor):
        """🔴 Red: アラート自動解決ロジックテスト"""
        # アラート作成（過去のタイムスタンプ）
        old_alert = QualityAlert(
            alert_id="OLD-ALERT",
            alert_level=AlertLevel.WARNING,
            metric_type=MetricType.QUALITY_SCORE,
            message="古いアラート",
            current_value=80.0,
            threshold_value=85.0,
            pipeline_id="TEST",
            timestamp=datetime.now() - timedelta(hours=3)  # 3時間前
        )
        
        # アクティブアラートに追加
        alert_key = f"{old_alert.metric_type.value}-{old_alert.alert_level.value}"
        monitor.active_alerts[alert_key] = old_alert
        
        # 最新の改善されたメトリクス追加
        for i in range(5):
            improved_metric = QualityMetric(
                metric_type=MetricType.QUALITY_SCORE,
                value=90.0 + i,  # 闾値を上回る改善値
                timestamp=datetime.now(),
                pipeline_id="TEST"
            )
            monitor.metrics_history[MetricType.QUALITY_SCORE].append(improved_metric)
        
        # 解決判定テスト
        recent_metrics = list(monitor.metrics_history[MetricType.QUALITY_SCORE])[-5:]
        is_resolved = monitor._is_alert_resolved(old_alert, recent_metrics)
        
        assert is_resolved is True  # 改善されたので解決されるべき
    
    def test_quality_metric_dataclass(self):
        """🔴 Red: QualityMetricデータクラステスト"""
        timestamp = datetime.now()
        metric = QualityMetric(
            metric_type=MetricType.QUALITY_SCORE,
            value=92.5,
            timestamp=timestamp,
            pipeline_id="TEST-PIPELINE-001",
            additional_data={"status": "ELDER_APPROVED"}
        )
        
        assert metric.metric_type == MetricType.QUALITY_SCORE
        assert metric.value == 92.5
        assert metric.timestamp == timestamp
        assert metric.pipeline_id == "TEST-PIPELINE-001"
        assert metric.additional_data["status"] == "ELDER_APPROVED"
    
    def test_quality_alert_dataclass(self):
        """🔴 Red: QualityAlertデータクラステスト"""
        timestamp = datetime.now()
        alert = QualityAlert(
            alert_id="ALERT-TEST-001",
            alert_level=AlertLevel.WARNING,
            metric_type=MetricType.EXECUTION_TIME,
            message="実行時間が闾値を超過しました",
            current_value=25.0,
            threshold_value=20.0,
            pipeline_id="TEST-PIPELINE",
            timestamp=timestamp
        )
        
        assert alert.alert_id == "ALERT-TEST-001"
        assert alert.alert_level == AlertLevel.WARNING
        assert alert.metric_type == MetricType.EXECUTION_TIME
        assert alert.current_value == 25.0
        assert alert.threshold_value == 20.0
        assert alert.resolved is False  # デフォルト値
        assert alert.elder_council_notified is False  # デフォルト値
    
    def test_monitoring_report_dataclass(self):
        """🔴 Red: MonitoringReportデータクラステスト"""
        start_time = datetime.now() - timedelta(hours=24)
        end_time = datetime.now()
        timestamp = datetime.now()
        
        report = MonitoringReport(
            report_id="QMR-TEST-001",
            period_start=start_time,
            period_end=end_time,
            total_executions=100,
            successful_executions=95,
            average_quality_score=91.5,
            elder_approval_rate=95.0,
            average_execution_time=18.5,
            pipeline_efficiency_trend="IMPROVING",
            active_alerts=[],
            resolved_alerts=[],
            recommendations=["Continue current quality practices"],
            elder_council_summary={"health": "GOOD"},
            timestamp=timestamp
        )
        
        assert report.report_id == "QMR-TEST-001"
        assert report.total_executions == 100
        assert report.successful_executions == 95
        assert report.elder_approval_rate == 95.0
        assert report.pipeline_efficiency_trend == "IMPROVING"
        assert len(report.recommendations) == 1
        assert report.elder_council_summary["health"] == "GOOD"


# Integration tests
class TestQualityMetricsMonitorIntegration:
    """品質メトリクスモニター統合テスト"""
    
    @pytest.mark.integration
    def test_real_pipeline_monitoring_integration(self):
        """🔴 Red: 実際パイプライン監視統合テスト（スキップ可能）"""
        pytest.skip("実装完了後に有効化")
        
        # Real integration with UnifiedQualityPipeline
        # Will be enabled after implementation
    
    @pytest.mark.performance
    def test_monitoring_performance_benchmarks(self):
        """🔴 Red: 監視性能ベンチマークテスト"""
        pytest.skip("実装完了後に有効化")
        
        # Performance benchmarking will be added after implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

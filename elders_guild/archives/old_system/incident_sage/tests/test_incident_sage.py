"""
Incident Sage テストスイート
==========================

インシデント対応・品質監視賢者のテスト

Author: Claude Elder
Created: 2025-07-22
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from pathlib import Path

# インポートパスを追加
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from elders_guild_dev.incident_sage.soul import IncidentSage
from elders_guild_dev.incident_sage.abilities.incident_models import (
    Incident, IncidentSeverity, IncidentStatus, IncidentCategory,
    QualityMetric, QualityStandard, QualityAssessment,
    IncidentResponse, AlertRule, MonitoringTarget
)
from elders_guild_dev.shared_libs.soul_base import BaseSoul


class TestIncidentSage:
    """Incident Sage核心機能テスト"""
    
    @pytest.fixture
    def incident_sage(self, tmp_path):
        """テスト用Incident Sageインスタンス"""
        return IncidentSage(data_dir=tmp_path / "test_incident_sage_data")
    
    def test_initialization(self, incident_sage):
        """初期化テスト"""
        assert isinstance(incident_sage, BaseSoul)
        assert incident_sage.soul_type == "incident_sage"
        assert incident_sage.domain == "incident_management"
        assert incident_sage.soul_name == "Incident Sage"
        
        # 初期データ構造確認
        assert hasattr(incident_sage, 'incidents')
        assert hasattr(incident_sage, 'quality_standards')
        assert hasattr(incident_sage, 'alert_rules')
        assert hasattr(incident_sage, 'monitoring_targets')
    
    @pytest.mark.asyncio
    async def test_incident_detection(self, incident_sage):
        """インシデント検知テスト"""
        # 異常データでインシデント検知
        anomaly_data = {
            "component": "test_service",
            "metric": "error_rate",
            "value": 25.0,
            "threshold": 5.0,
            "severity": "high"
        }
        
        incident = await incident_sage.detect_incident(anomaly_data)
        
        assert isinstance(incident, Incident)
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.DETECTED
        assert "test_service" in incident.affected_components
        assert incident.confidence_score > 0.5
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, incident_sage):
        """品質評価テスト"""
        # 品質基準設定
        quality_standard = QualityStandard(
            name="Elder Guild Standard",
            compliance_threshold=95.0,
            metrics={
                "test_coverage": QualityMetric(
                    name="Test Coverage",
                    target_value=95.0,
                    threshold_min=90.0
                ),
                "code_quality": QualityMetric(
                    name="Code Quality",
                    target_value=90.0,
                    threshold_min=80.0
                )
            }
        )
        
        await incident_sage.register_quality_standard(quality_standard)
        
        # コンポーネント品質評価
        assessment_data = {
            "component": "test_module",
            "metrics": {
                "test_coverage": 88.0,  # 基準以下
                "code_quality": 92.0    # 基準以上
            }
        }
        
        assessment = await incident_sage.assess_quality(
            quality_standard.standard_id, 
            assessment_data
        )
        
        assert isinstance(assessment, QualityAssessment)
        assert not assessment.is_compliant  # カバレッジが基準以下なので非準拠
        assert len(assessment.violations) > 0
        assert assessment.overall_score < 95.0
    
    @pytest.mark.asyncio
    async def test_incident_response(self, incident_sage):
        """インシデント対応テスト"""
        # インシデント作成
        incident = Incident(
            title="Critical Service Down",
            severity=IncidentSeverity.CRITICAL,
            category=IncidentCategory.AVAILABILITY,
            affected_components=["main_service"]
        )
        
        await incident_sage.register_incident(incident)
        
        # 自動対応実行
        response = await incident_sage.respond_to_incident(incident.incident_id)
        
        assert isinstance(response, IncidentResponse)
        assert response.incident_id == incident.incident_id
        assert response.status in ["pending", "in_progress", "completed", "failed"]
        assert len(response.execution_steps) > 0
    
    @pytest.mark.asyncio
    async def test_alert_rule_management(self, incident_sage):
        """アラートルール管理テスト"""
        # アラートルール作成
        alert_rule = AlertRule(
            name="High Error Rate Alert",
            condition_expression="error_rate > 5.0",
            threshold_value=5.0,
            severity=IncidentSeverity.HIGH,
            auto_response_enabled=True
        )
        
        await incident_sage.create_alert_rule(alert_rule)
        
        # ルール評価
        metric_data = {
            "error_rate": 8.0,
            "component": "test_service"
        }
        
        triggered_alerts = await incident_sage.evaluate_alert_rules(metric_data)
        
        assert len(triggered_alerts) > 0
        assert triggered_alerts[0].severity == IncidentSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_monitoring_target_health_check(self, incident_sage):
        """監視対象ヘルスチェックテスト"""
        # 監視対象登録
        target = MonitoringTarget(
            name="Test Service",
            type="service",
            endpoint_url="http://localhost:8080",
            health_check_path="/health"
        )
        
        await incident_sage.register_monitoring_target(target)
        
        # ヘルスチェック実行（モック）
        with pytest.MonkeyPatch().context() as mp:
            async def mock_health_check(target_id):
                """mock_health_checkメソッド"""
                return {
                    "status": "healthy",
                    "response_time_ms": 150,
                    "uptime": 99.5
                }
            
            mp.setattr(incident_sage, "_perform_health_check", mock_health_check)
            
            health_result = await incident_sage.check_target_health(target.target_id)
            
            assert health_result["status"] == "healthy"
            assert health_result["response_time_ms"] > 0
    
    def test_incident_severity_escalation(self, incident_sage):
        """インシデント重要度エスカレーションテスト"""
        # 軽微なインシデント
        low_incident = Incident(
            severity=IncidentSeverity.LOW,
            detected_at=datetime.now() - timedelta(hours=2)
        )
        
        # エスカレーション判定
        should_escalate = incident_sage.should_escalate_incident(low_incident)
        
        # 2時間経過した軽微インシデントは通常エスカレーション不要
        assert should_escalate is False
        
        # クリティカルインシデント
        critical_incident = Incident(
            severity=IncidentSeverity.CRITICAL,
            detected_at=datetime.now() - timedelta(minutes=10)
        )
        
        should_escalate = incident_sage.should_escalate_incident(critical_incident)
        
        # 10分経過したクリティカルインシデントはエスカレーション必要
        assert should_escalate is True
    
    @pytest.mark.asyncio
    async def test_incident_pattern_learning(self, incident_sage):
        """インシデントパターン学習テスト"""
        # 類似インシデントを複数作成
        incidents = [
            Incident(
                title="Service Timeout",
                category=IncidentCategory.PERFORMANCE,
                root_cause="Database connection pool exhausted",
                tags=["timeout", "database", "connection"]
            ),
            Incident(
                title="API Timeout",
                category=IncidentCategory.PERFORMANCE, 
                root_cause="Database query timeout",
                tags=["timeout", "database", "query"]
            )
        ]
        
        for incident in incidents:
            await incident_sage.register_incident(incident)
        
        # パターン学習実行
        learned_patterns = await incident_sage.learn_incident_patterns()
        
        assert len(learned_patterns) > 0
        # パフォーマンスカテゴリのパターンが学習されているはず
        perf_patterns = [p for p in learned_patterns if "performance" in p.get("category", "").lower()]
        assert len(perf_patterns) > 0
    
    def test_quality_metric_trend_analysis(self, incident_sage):
        """品質メトリクストレンド分析テスト"""
        # 時系列メトリクス
        metrics = [
            QualityMetric(
                name="Test Coverage",
                value=85.0,
                measured_at=datetime.now() - timedelta(hours=3)
            ),
            QualityMetric(
                name="Test Coverage", 
                value=87.0,
                measured_at=datetime.now() - timedelta(hours=2)
            ),
            QualityMetric(
                name="Test Coverage",
                value=90.0,
                measured_at=datetime.now() - timedelta(hours=1)
            )
        ]
        
        trend = incident_sage.analyze_metric_trend(metrics)
        
        assert trend["direction"] == "improving"  # 値が向上傾向
        assert trend["rate"] > 0  # 正の変化率
    
    @pytest.mark.asyncio
    async def test_automated_remediation(self, incident_sage):
        """自動修復テスト"""
        # 既知パターンのインシデント
        incident = Incident(
            title="High Memory Usage",
            category=IncidentCategory.PERFORMANCE,
            affected_components=["worker_process"],
            root_cause="Memory leak in background task"
        )
        
        await incident_sage.register_incident(incident)
        
        # 自動修復実行
        remediation_result = await incident_sage.attempt_automated_remediation(incident.incident_id)
        
        assert remediation_result is not None
        assert "status" in remediation_result
        assert "actions_taken" in remediation_result
    
    @pytest.mark.asyncio
    async def test_incident_correlation(self, incident_sage):
        """インシデント相関分析テスト"""
        # 関連する複数インシデント
        incidents = [
            Incident(
                title="Database Connection Error",
                affected_components=["database"],
                detected_at=datetime.now() - timedelta(minutes=5)
            ),
            Incident(
                title="API Response Slow", 
                affected_components=["api_service"],
                detected_at=datetime.now() - timedelta(minutes=3)
            ),
            Incident(
                title="User Session Timeout",
                affected_components=["web_frontend"],
                detected_at=datetime.now() - timedelta(minutes=1)
            )
        ]
        
        for incident in incidents:
            await incident_sage.register_incident(incident)
        
        # 相関分析実行
        correlations = await incident_sage.analyze_incident_correlations()
        
        assert len(correlations) > 0
        # 時系列で関連する問題として認識されるはず
        assert any(len(corr.get("related_incidents", [])) > 1 for corr in correlations)
    
    @pytest.mark.asyncio 
    async def test_elder_tree_a2a_communication(self, incident_sage):
        """Elder Tree A2A通信テスト"""
        # 他の賢者への通信テスト
        test_message = {
            "type": "incident_alert",
            "incident_id": "test_incident_001",
            "severity": "high",
            "requires_collaboration": True
        }
        
        # Knowledge Sageへの通信（モック）
        response = await incident_sage.send_message_to_sage("knowledge_sage", test_message)
        
        # A2A通信の基本構造確認
        assert "status" in response
        assert response.get("status") in ["success", "error", "timeout"]
    
    @pytest.mark.asyncio
    async def test_integration_with_other_sages(self, incident_sage):
        """他賢者との統合テスト"""
        # Task Sageとの連携テスト
        incident = Incident(
            title="Critical Bug in Production",
            severity=IncidentSeverity.CRITICAL,
            category=IncidentCategory.QUALITY
        )
        
        await incident_sage.register_incident(incident)
        
        # タスク作成要求
        task_creation_request = await incident_sage.request_task_creation(incident.incident_id)
        
        assert "task_type" in task_creation_request
        assert task_creation_request["task_type"] == "incident_resolution"
        assert task_creation_request["priority"] == "critical"
        
        # RAG Sageとの連携テスト
        similar_incidents = await incident_sage.search_similar_incidents(incident.title)
        
        assert isinstance(similar_incidents, list)
        # 実際の検索結果は空でも構造は正しいはず
        
    def test_iron_will_compliance(self, incident_sage):
        """Iron Will遵守確認テスト"""
        # TODO, FIXME, WORKAROUNDが存在しないことを確認
        sage_code = incident_sage.__class__.__module__
        
        # ソースコード取得
        import inspect
        source = inspect.getsource(incident_sage.__class__)
        
        # Iron Will違反チェック
        forbidden_patterns = ["TODO", "FIXME", "WORKAROUND", "HACK", "XXX"]
        violations = [pattern for pattern in forbidden_patterns if pattern in source]
        
        assert len(violations) == 0, f"Iron Will violations found: {violations}"
        
        # 完全実装確認
        assert hasattr(incident_sage, 'detect_incident')
        assert hasattr(incident_sage, 'respond_to_incident') 
        assert hasattr(incident_sage, 'assess_quality')
        assert hasattr(incident_sage, 'create_alert_rule')
        
    def test_metrics_and_monitoring(self, incident_sage):
        """メトリクス・監視機能テスト"""
        # 基本メトリクス確認
        metrics = incident_sage.get_operational_metrics()
        
        expected_metrics = [
            "incidents_detected", "incidents_resolved", 
            "average_resolution_time", "quality_assessments_performed",
            "alert_rules_active", "monitoring_targets_healthy"
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))


if __name__ == "__main__":
    """テスト実行"""
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
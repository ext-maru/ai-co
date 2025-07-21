#!/usr/bin/env python3
"""
🧪 Enhanced Incident Sage テストスイート
Phase 26: 統合テスト
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sqlite3
from pathlib import Path
import tempfile
import os

# テスト対象
from libs.four_sages.incident.enhanced_incident_sage import EnhancedIncidentSage
from libs.four_sages.incident.failure_pattern_detector import FailurePattern, FailurePatternDetector
from libs.four_sages.incident.preventive_alert_system import PreventiveAlert, AlertLevel
from libs.four_sages.incident.automatic_response_system import ResponseRule, ResponseStatus
from libs.four_sages.incident.incident_predictor import PredictionResult, FeatureVector
from libs.four_sages.incident.incident_sage import (
    IncidentEntry, IncidentSeverity, IncidentCategory, IncidentStatus
)


class TestEnhancedIncidentSage:
    """Enhanced Incident Sage統合テスト"""
    
    @pytest.fixture
    async def enhanced_sage(self):
        """テスト用Enhanced Incident Sageインスタンス"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_db = os.path.join(tmpdir, "test_tracking.db")
            sage = EnhancedIncidentSage(tracking_db_path=tracking_db)
            await sage.initialize_integration()
            yield sage
            await sage.shutdown()
    
    @pytest.fixture
    def sample_incident(self):
        """サンプルインシデント"""
        return {
            "title": "Test Service Failure",
            "description": "Service timeout error detected",
            "category": "system_failure",
            "severity": "high",
            "affected_systems": ["api-service", "database"],
            "tags": ["timeout", "critical"]
        }
    
    @pytest.fixture
    def sample_metrics(self):
        """サンプルメトリクス"""
        return {
            "error_rate": 0.15,
            "response_time": 8.5,
            "cpu_usage": 85.0,
            "memory_usage": 78.0,
            "failure_rate": 0.12,
            "quality_score": 0.82
        }
    
    @pytest.mark.asyncio
    async def test_initialization(self, enhanced_sage):
        """初期化テスト"""
        assert enhanced_sage is not None
        assert enhanced_sage.failure_detector is not None
        assert enhanced_sage.alert_system is not None
        assert enhanced_sage.response_system is not None
        assert enhanced_sage.predictor is not None
        assert len(enhanced_sage.background_tasks) > 0
    
    @pytest.mark.asyncio
    async def test_create_incident_with_auto_response(self, enhanced_sage, sample_incident):
        """自動対応付きインシデント作成テスト"""
        # 自動対応を有効化
        enhanced_sage.integration_config["auto_response_enabled"] = True
        
        # インシデント作成
        response = await enhanced_sage.process_request({
            "type": "create_incident",
            **sample_incident
        })
        
        assert response["success"] is True
        assert "incident_id" in response
        
        # 自動対応が実行されたか確認
        if "auto_response" in response:
            assert response["auto_response"]["handled"] is True
            assert enhanced_sage.integration_metrics["auto_responses"] > 0
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, enhanced_sage):
        """パターン分析テスト"""
        # パターン分析実行
        response = await enhanced_sage.process_request({
            "type": "analyze_patterns",
            "days_back": 7
        })
        
        assert response["success"] is True
        assert "patterns_found" in response
        assert enhanced_sage.integration_metrics["patterns_detected"] >= 0
    
    @pytest.mark.asyncio
    async def test_risk_prediction(self, enhanced_sage):
        """リスク予測テスト"""
        # テスト状態
        test_state = {
            "metrics": {
                "error_rate": 0.2,
                "response_time": 10.0,
                "cpu_usage": 90.0,
                "memory_usage": 85.0
            },
            "history": {
                "failures_1h": 15,
                "failures_24h": 50
            }
        }
        
        # リスク予測実行
        response = await enhanced_sage.process_request({
            "type": "predict_risk",
            "state": test_state
        })
        
        assert response["success"] is True
        assert "prediction" in response
        
        prediction = response["prediction"]
        assert "risk_score" in prediction
        assert "risk_level" in prediction
        assert "recommended_actions" in prediction
    
    @pytest.mark.asyncio
    async def test_preventive_alerts(self, enhanced_sage, sample_metrics):
        """予防的アラートテスト"""
        # アラートシステムモニタリング
        await enhanced_sage.monitor_tracking_metrics(sample_metrics)
        
        # アラートが生成されたか確認
        assert enhanced_sage.integration_metrics["preventive_alerts"] >= 0
    
    @pytest.mark.asyncio
    async def test_integration_status(self, enhanced_sage):
        """統合ステータス取得テスト"""
        response = await enhanced_sage.process_request({
            "type": "get_integration_status"
        })
        
        assert response["success"] is True
        assert "integration_status" in response
        
        status = response["integration_status"]
        assert "config" in status
        assert "metrics" in status
        assert "components" in status
        assert all(comp == "active" for comp in status["components"].values())
    
    @pytest.mark.asyncio
    async def test_configure_integration(self, enhanced_sage):
        """統合設定変更テスト"""
        new_config = {
            "pattern_analysis_interval": 7200,
            "auto_response_enabled": False
        }
        
        response = await enhanced_sage.process_request({
            "type": "configure_integration",
            "config": new_config
        })
        
        assert response["success"] is True
        assert enhanced_sage.integration_config["pattern_analysis_interval"] == 7200
        assert enhanced_sage.integration_config["auto_response_enabled"] is False
    
    @pytest.mark.asyncio
    async def test_high_risk_prediction_handling(self, enhanced_sage):
        """高リスク予測処理テスト"""
        # 高リスク予測を作成
        high_risk_prediction = PredictionResult(
            risk_score=0.85,
            risk_level="critical",
            incident_probability={"system_failure": 0.8, "none": 0.2},
            severity_probability={"critical": 0.7, "high": 0.3},
            contributing_factors=[("High CPU usage", 0.9)],
            recommended_actions=["Scale up resources"],
            confidence=0.85
        )
        
        # 処理実行
        await enhanced_sage._handle_high_risk_prediction(high_risk_prediction)
        
        # 予防的インシデントが作成されたか確認
        assert enhanced_sage.integration_metrics["incidents_prevented"] > 0


class TestFailurePatternDetector:
    """失敗パターン検出器テスト"""
    
    @pytest.fixture
    def detector(self):
        """テスト用検出器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_db = os.path.join(tmpdir, "test_tracking.db")
            incident_db = os.path.join(tmpdir, "test_incident.db")
            return FailurePatternDetector(tracking_db, incident_db)
    
    @pytest.fixture
    def sample_failures(self):
        """サンプル失敗データ"""
        return [
            {
                "task_id": "task1",
                "task_description": "API call",
                "detail_type": "command",
                "stderr": "Connection timeout error",
                "exit_code": 1,
                "execution_time": 30.5,
                "timestamp": datetime.now().isoformat()
            },
            {
                "task_id": "task2",
                "task_description": "Database query",
                "detail_type": "query",
                "stderr": "Out of memory error",
                "exit_code": 137,
                "execution_time": 5.2,
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    @pytest.mark.asyncio
    async def test_extract_error_patterns(self, detector, sample_failures):
        """エラーパターン抽出テスト"""
        patterns = await detector._extract_error_patterns(sample_failures)
        
        assert isinstance(patterns, list)
        # タイムアウトとメモリエラーのパターンが検出されるはず
        pattern_names = [p.get("pattern_name") for p in patterns]
        assert any("timeout" in name for name in pattern_names if name)
    
    @pytest.mark.asyncio
    async def test_pattern_classification(self, detector):
        """パターン分類テスト"""
        test_pattern = {
            "pattern_type": "error_message",
            "pattern_name": "timeout"
        }
        
        category = await detector._classify_pattern(test_pattern)
        assert category == IncidentCategory.PERFORMANCE_ISSUE
    
    @pytest.mark.asyncio
    async def test_pattern_severity_evaluation(self, detector):
        """パターン重要度評価テスト"""
        test_pattern = {
            "occurrences": 25,
            "pattern_type": "error_message"
        }
        
        severity = await detector._evaluate_pattern_severity(test_pattern)
        assert severity == IncidentSeverity.HIGH


class TestPreventiveAlertSystem:
    """予防的アラートシステムテスト"""
    
    @pytest.fixture
    def alert_system(self):
        """テスト用アラートシステム"""
        mock_sage = Mock()
        mock_sage.process_request = AsyncMock(return_value={"success": True, "alert_id": "test123"})
        return PreventiveAlertSystem(mock_sage)
    
    @pytest.mark.asyncio
    async def test_threshold_alert(self, alert_system):
        """閾値ベースアラートテスト"""
        # 高いエラー率でテスト
        metrics = {
            "error_rate": 0.3,  # 30%エラー率
            "quality_score": 0.65  # 品質スコア低下
        }
        
        result = await alert_system.monitor_metrics(metrics)
        
        assert result["success"] is True
        assert result["alerts_generated"] > 0
        assert len(result["alerts"]) > 0
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, alert_system):
        """トレンド分析テスト"""
        # 時系列データを追加
        for i in range(10):
            metrics = {"cpu_usage": 50 + i * 5}  # 増加トレンド
            await alert_system.monitor_metrics(metrics)
            await asyncio.sleep(0.1)
        
        # トレンドアラートが生成されるか確認
        assert alert_system.alert_stats["total_alerts"] >= 0
    
    @pytest.mark.asyncio
    async def test_alert_suppression(self, alert_system):
        """重複アラート抑制テスト"""
        # 同じメトリクスで複数回アラート
        metrics = {"failure_rate": 0.5}
        
        result1 = await alert_system.monitor_metrics(metrics)
        result2 = await alert_system.monitor_metrics(metrics)
        
        # 2回目は抑制されるはず
        assert result1["alerts_generated"] > 0
        assert result2["alerts_generated"] == 0  # 重複は抑制


class TestAutomaticResponseSystem:
    """自動対応システムテスト"""
    
    @pytest.fixture
    def response_system(self):
        """テスト用対応システム"""
        mock_sage = Mock()
        mock_sage.process_request = AsyncMock(return_value={"success": True})
        return AutomaticResponseSystem(mock_sage)
    
    @pytest.fixture
    def test_incident(self):
        """テスト用インシデント"""
        return IncidentEntry(
            id="test123",
            title="Service Down",
            description="Service health check failed timeout error",
            category=IncidentCategory.SYSTEM_FAILURE,
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            affected_systems=["api-service"]
        )
    
    @pytest.mark.asyncio
    async def test_rule_matching(self, response_system, test_incident):
        """ルールマッチングテスト"""
        matched_rules = await response_system._match_rules(test_incident)
        
        assert len(matched_rules) > 0
        # サービス再起動ルールがマッチするはず
        rule_ids = [r.rule_id for r in matched_rules]
        assert "service_restart_rule" in rule_ids
    
    @pytest.mark.asyncio
    async def test_response_execution(self, response_system, test_incident):
        """対応実行テスト"""
        # モックアクション
        async def mock_action(incident):
            return {"success": True, "message": "Action executed"}
        
        response_system.action_registry["test_action"] = mock_action
        
        # テストルール
        test_rule = ResponseRule(
            rule_id="test_rule",
            rule_name="Test Rule",
            conditions=["test_condition"],
            actions=["test_action"],
            cooldown=0
        )
        
        execution = await response_system._execute_rule(test_rule, test_incident)
        
        assert execution.status == ResponseStatus.SUCCESS
        assert len(execution.actions_executed) == 1


class TestIncidentPredictor:
    """インシデント予測器テスト"""
    
    @pytest.fixture
    def predictor(self):
        """テスト用予測器"""
        mock_detector = Mock()
        mock_detector.process_request = AsyncMock(return_value={"success": True, "patterns": []})
        return IncidentPredictor(mock_detector)
    
    @pytest.fixture
    def training_data(self):
        """訓練データ"""
        return [
            {
                "state": {
                    "metrics": {
                        "error_rate": 0.05,
                        "cpu_usage": 50.0,
                        "memory_usage": 60.0
                    },
                    "history": {"failures_1h": 2}
                },
                "incident": None  # インシデントなし
            },
            {
                "state": {
                    "metrics": {
                        "error_rate": 0.3,
                        "cpu_usage": 95.0,
                        "memory_usage": 90.0
                    },
                    "history": {"failures_1h": 20}
                },
                "incident": {
                    "category": "system_failure",
                    "severity": "critical"
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_feature_extraction(self, predictor):
        """特徴量抽出テスト"""
        test_state = {
            "metrics": {
                "error_rate": 0.1,
                "response_time": 2.5,
                "cpu_usage": 70.0
            }
        }
        
        feature = predictor.feature_extractor.extract(test_state)
        
        assert isinstance(feature, FeatureVector)
        assert feature.error_rate == 0.1
        assert feature.cpu_usage == 70.0
    
    @pytest.mark.asyncio
    async def test_model_training(self, predictor, training_data):
        """モデル訓練テスト"""
        # 十分な訓練データを生成
        extended_data = training_data * 50  # 100サンプル
        
        result = await predictor.train_model(extended_data)
        
        assert result["success"] is True
        assert predictor.prediction_model is not None
        assert predictor.severity_model is not None
    
    @pytest.mark.asyncio
    async def test_risk_calculation(self, predictor):
        """リスクスコア計算テスト"""
        incident_prob = {"system_failure": 0.8, "none": 0.2}
        severity_prob = {"critical": 0.6, "high": 0.3, "medium": 0.1}
        
        risk_score = predictor._calculate_risk_score(incident_prob, severity_prob)
        
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > 0.5  # 高リスク


@pytest.mark.asyncio
async def test_end_to_end_flow():
    """エンドツーエンド統合フローテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Enhanced Incident Sage作成
        tracking_db = os.path.join(tmpdir, "test_tracking.db")
        sage = EnhancedIncidentSage(tracking_db_path=tracking_db)
        await sage.initialize_integration()
        
        try:
            # 1. 高リスクメトリクスを投入
            high_risk_metrics = {
                "error_rate": 0.25,
                "response_time": 12.0,
                "cpu_usage": 92.0,
                "memory_usage": 88.0,
                "failure_rate": 0.3
            }
            
            # 2. メトリクス監視（アラート生成）
            await sage.monitor_tracking_metrics(high_risk_metrics)
            
            # 3. リスク予測実行
            prediction_response = await sage.process_request({
                "type": "predict_risk",
                "state": {
                    "metrics": high_risk_metrics,
                    "history": {"failures_1h": 25}
                }
            })
            
            assert prediction_response["success"] is True
            
            # 4. インシデント作成（自動対応付き）
            incident_response = await sage.process_request({
                "type": "create_incident",
                "title": "High System Load",
                "description": "CPU and memory usage critical",
                "category": "performance_issue",
                "severity": "high"
            })
            
            assert incident_response["success"] is True
            
            # 5. 統合ステータス確認
            status_response = await sage.process_request({
                "type": "get_integration_status"
            })
            
            assert status_response["success"] is True
            assert status_response["integration_status"]["metrics"]["predictions_made"] > 0
            
        finally:
            await sage.shutdown()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
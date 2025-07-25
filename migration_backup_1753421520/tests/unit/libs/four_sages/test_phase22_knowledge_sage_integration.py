#!/usr/bin/env python3
"""
Phase 22 Knowledge Sage Integration Test Suite
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0 - Comprehensive Integration Tests
"""

import asyncio
import pytest
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト対象モジュール
from libs.four_sages.knowledge.knowledge_sage import KnowledgeSage, KnowledgeType, KnowledgeConfidence
from libs.four_sages.knowledge.tracking_data_integrator import TrackingDataIntegrator
from libs.four_sages.knowledge.execution_linked_knowledge_entry import ExecutionLinkedKnowledgeEntry
from libs.four_sages.knowledge.pattern_extraction_engine import PatternExtractionEngine
from libs.four_sages.knowledge.predictive_recommendation_system import PredictiveRecommendationSystem
from libs.four_sages.knowledge.self_evolving_knowledge_manager import SelfEvolvingKnowledgeManager

class TestPhase22KnowledgeSageIntegration:
    """Phase 22 Knowledge Sage 統合テストクラス"""
    
    @pytest.fixture
    def knowledge_sage(self):
        """Knowledge Sage インスタンス作成"""
        return KnowledgeSage()
    
    @pytest.fixture
    def sample_execution_data(self):
        """サンプル実行データ"""
        return [
            {
                "task_id": f"task_{i}",
                "description": f"Test task {i}",
                "priority": "medium",
                "status": "completed" if i % 2 == 0 else "failed",
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "execution_time_seconds": 120.0 + i * 10,
                "overall_score": 0.8 + (i % 3) * 0.1,
                "iron_will_compliant": i % 2 == 0,
                "execution_details": [
                    {
                        "phase": "preparation",
                        "success": True,
                        "execution_time": 30.0
                    },
                    {
                        "phase": "execution",
                        "success": i % 2 == 0,
                        "execution_time": 90.0
                    }
                ],
                "logs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": f"Task {i} log entry"
                    }
                ],
                "quality_metrics": {
                    "test_coverage": 0.85,
                    "code_quality": 0.9
                },
                "sage_advice": {
                    "task_sage": {
                        "advice": "Optimize execution",
                        "confidence": 0.8
                    }
                }
            }
            for i in range(10)
        ]
    
    @pytest.mark.asyncio
    async def test_knowledge_sage_initialization(self, knowledge_sage):
        """Knowledge Sage 初期化テスト"""
        # 基本初期化の確認
        assert knowledge_sage is not None
        assert knowledge_sage.sage_name == "Knowledge Sage"
        assert knowledge_sage.tracking_enabled == True
        
        # 遅延初期化コンポーネントの確認
        assert knowledge_sage.tracking_integrator is None
        assert knowledge_sage.pattern_engine is None
        assert knowledge_sage.recommendation_system is None
        assert knowledge_sage.evolution_manager is None
        
        # 能力の確認
        capabilities = knowledge_sage.get_capabilities()
        assert "tracking_integration" in capabilities
        assert "pattern_analysis" in capabilities
        assert "predictive_recommendation" in capabilities
        assert "evolution_management" in capabilities
        assert "knowledge_enhancement" in capabilities
    
    @pytest.mark.asyncio
    async def test_tracking_component_initialization(self, knowledge_sage):
        """追跡コンポーネント初期化テスト"""
        # コンポーネントの初期化
        result = await knowledge_sage._ensure_tracking_components()
        
        assert result == True
        assert knowledge_sage.tracking_integrator is not None
        assert knowledge_sage.pattern_engine is not None
        assert knowledge_sage.recommendation_system is not None
        assert knowledge_sage.evolution_manager is not None
    
    @pytest.mark.asyncio
    async def test_tracking_integration_request(self, knowledge_sage):
        """追跡統合リクエストテスト"""
        # ステータス取得
        status_result = await knowledge_sage.process_request({
            "type": "tracking_integration",
            "integration_type": "status"
        })
        
        assert status_result["success"] == True
        assert "tracking_enabled" in status_result
        assert "components" in status_result
        
        # データ同期
        sync_result = await knowledge_sage.process_request({
            "type": "tracking_integration",
            "integration_type": "data_sync"
        })
        
        assert sync_result["success"] == True
        assert "sync_result" in sync_result
    
    @pytest.mark.asyncio
    async def test_pattern_analysis_request(self, knowledge_sage):
        """パターン分析リクエストテスト"""
        # パターン抽出
        pattern_result = await knowledge_sage.process_request({
            "type": "pattern_analysis",
            "analysis_type": "execution_patterns",
            "days": 30
        })
        
        assert pattern_result["success"] == True
        assert "patterns" in pattern_result
        
        # 異常検知
        anomaly_result = await knowledge_sage.process_request({
            "type": "pattern_analysis",
            "analysis_type": "anomaly_detection",
            "days": 30
        })
        
        assert anomaly_result["success"] == True
        assert "anomalies" in anomaly_result
    
    @pytest.mark.asyncio
    async def test_predictive_recommendation_request(self, knowledge_sage):
        """予測推奨リクエストテスト"""
        # 実行予測
        prediction_result = await knowledge_sage.process_request({
            "type": "predictive_recommendation",
            "recommendation_type": "execution_prediction",
            "task_description": "Test task for prediction",
            "context": {
                "priority": "high",
                "historical_success_rate": 0.85
            }
        })
        
        assert prediction_result["success"] == True
        assert "prediction" in prediction_result
        assert "predicted_value" in prediction_result["prediction"]
        assert "confidence" in prediction_result["prediction"]
        
        # 推奨事項生成
        recommendation_result = await knowledge_sage.process_request({
            "type": "predictive_recommendation",
            "recommendation_type": "recommendations",
            "user_context": {
                "historical_success_rate": 0.8,
                "avg_execution_time": 120.0
            }
        })
        
        assert recommendation_result["success"] == True
        assert "recommendations" in recommendation_result
    
    @pytest.mark.asyncio
    async def test_evolution_management_request(self, knowledge_sage):
        """進化管理リクエストテスト"""
        # 進化状況取得
        status_result = await knowledge_sage.process_request({
            "type": "evolution_management",
            "evolution_type": "status"
        })
        
        assert status_result["success"] == True
        assert "evolution_status" in status_result
        
        # 自動進化実行
        auto_result = await knowledge_sage.process_request({
            "type": "evolution_management",
            "evolution_type": "auto_evolve"
        })
        
        assert auto_result["success"] == True
        assert "auto_evolution_result" in auto_result
    
    @pytest.mark.asyncio
    async def test_knowledge_enhancement_request(self, knowledge_sage):
        """知識強化リクエストテスト"""
        # 品質洞察取得
        insights_result = await knowledge_sage.process_request({
            "type": "knowledge_enhancement",
            "enhancement_type": "quality_insights",
            "days": 30
        })
        
        assert insights_result["success"] == True
        assert "quality_insights" in insights_result
        
        # 知識エントリを作成
        knowledge_entry = await knowledge_sage.process_request({
            "type": "store_knowledge",
            "title": "Test Knowledge for Enhancement",
            "content": "This is a test knowledge entry for enhancement testing",
            "knowledge_type": "factual",
            "confidence": "medium",
            "tags": ["test", "enhancement"]
        })
        
        assert knowledge_entry["success"] == True
        knowledge_id = knowledge_entry["knowledge_id"]
        
        # 実行連携知識作成
        enhancement_result = await knowledge_sage.process_request({
            "type": "knowledge_enhancement",
            "enhancement_type": "execution_linked_knowledge",
            "knowledge_id": knowledge_id
        })
        
        assert enhancement_result["success"] == True
        assert "enhanced_knowledge" in enhancement_result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, knowledge_sage):
        """エラーハンドリングテスト"""
        # 無効なリクエストタイプ
        invalid_result = await knowledge_sage.process_request({
            "type": "invalid_request_type"
        })
        
        assert invalid_result["success"] == False
        assert "error" in invalid_result
        
        # 無効な統合タイプ
        invalid_integration = await knowledge_sage.process_request({
            "type": "tracking_integration",
            "integration_type": "invalid_type"
        })
        
        assert invalid_integration["success"] == False
        assert "error" in invalid_integration
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, knowledge_sage):
        """後方互換性テスト"""
        # 既存の機能が正常に動作することを確認
        
        # 知識保存
        store_result = await knowledge_sage.process_request({
            "type": "store_knowledge",
            "title": "Backward Compatibility Test",
            "content": "Testing backward compatibility",
            "knowledge_type": "factual",
            "confidence": "high"
        })
        
        assert store_result["success"] == True
        knowledge_id = store_result["knowledge_id"]
        
        # 知識検索
        search_result = await knowledge_sage.process_request({
            "type": "search_knowledge",
            "query": "Backward Compatibility",
            "limit": 10
        })
        
        assert search_result["success"] == True
        assert len(search_result["results"]) > 0
        
        # 知識取得
        retrieve_result = await knowledge_sage.process_request({
            "type": "retrieve_knowledge",
            "knowledge_id": knowledge_id
        })
        
        assert retrieve_result["success"] == True
        assert retrieve_result["knowledge"]["title"] == "Backward Compatibility Test"
        
        # ヘルスチェック
        health_result = await knowledge_sage.process_request({
            "type": "health_check"
        })
        
        assert health_result["success"] == True
        assert health_result["status"] == "healthy"

class TestTrackingDataIntegrator:
    """TrackingDataIntegrator テストクラス"""
    
    @pytest.fixture
    def integrator(self):
        """TrackingDataIntegrator インスタンス"""
        return TrackingDataIntegrator()
    
    @pytest.fixture
    def sample_execution_data(self):
        """サンプル実行データ"""
        return [
            {
                "task_id": f"task_{i}",
                "status": "completed" if i % 2 == 0 else "failed",
                "execution_time_seconds": 120.0 + i * 10,
                "overall_score": 0.8 + (i % 3) * 0.1,
                "iron_will_compliant": i % 2 == 0,
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "execution_details": [],
                "logs": [],
                "quality_metrics": {},
                "sage_advice": {}
            }
            for i in range(10)
        ]
    
    @pytest.mark.asyncio
    async def test_execution_data_retrieval(self, integrator):
        """実行データ取得テスト"""
        # 期間指定でのデータ取得
        data = await integrator.get_execution_data(days=7)
        assert isinstance(data, list)
        
        # 特定タスクIDでのデータ取得
        task_data = await integrator.get_execution_data(task_id="non_existent_task")
        assert isinstance(task_data, list)
        assert len(task_data) == 0
    
    @pytest.mark.asyncio
    async def test_pattern_analysis(self, integrator, sample_execution_data):
        """パターン分析テスト"""
        patterns = await integrator.analyze_execution_patterns(sample_execution_data)
        assert isinstance(patterns, list)
        
        # パターンの構造確認
        for pattern in patterns:
            assert hasattr(pattern, 'pattern_type')
            assert hasattr(pattern, 'frequency')
            assert hasattr(pattern, 'confidence')
            assert hasattr(pattern, 'recommendations')
    
    @pytest.mark.asyncio
    async def test_metrics_extraction(self, integrator, sample_execution_data):
        """メトリクス抽出テスト"""
        metrics = await integrator.extract_execution_metrics(sample_execution_data)
        assert isinstance(metrics, list)
        
        # メトリクスの構造確認
        for metric in metrics:
            assert hasattr(metric, 'task_id')
            assert hasattr(metric, 'execution_time')
            assert hasattr(metric, 'success_rate')
            assert hasattr(metric, 'quality_score')
    
    @pytest.mark.asyncio
    async def test_quality_insights(self, integrator):
        """品質洞察テスト"""
        insights = await integrator.get_quality_insights(days=30)
        assert isinstance(insights, dict)
        
        # 期待されるキーの確認
        assert "metrics_summary" in insights
        assert "execution_patterns" in insights
        assert "quality_trends" in insights
        assert "recommendations" in insights

class TestExecutionLinkedKnowledgeEntry:
    """ExecutionLinkedKnowledgeEntry テストクラス"""
    
    @pytest.fixture
    def knowledge_entry(self):
        """ExecutionLinkedKnowledgeEntry インスタンス"""
        return ExecutionLinkedKnowledgeEntry(
            id="test_entry_001",
            title="Test Knowledge Entry",
            content="This is a test knowledge entry with execution linking",
            knowledge_type=KnowledgeType.FACTUAL,
            confidence=KnowledgeConfidence.MEDIUM,
            tags={"test", "execution", "linked"}
        )
    
    def test_execution_evidence_addition(self, knowledge_entry):
        """実行証拠追加テスト"""
        from libs.four_sages.knowledge.execution_linked_knowledge_entry import ExecutionEvidence, ExecutionContext
        
        evidence = ExecutionEvidence(
            task_id="test_task_001",
            execution_time=120.0,
            success_rate=0.85,
            quality_score=0.9,
            iron_will_compliant=True,
            execution_context=ExecutionContext.TASK_EXECUTION
        )
        
        result = knowledge_entry.add_execution_evidence(evidence)
        assert result == True
        assert len(knowledge_entry.execution_evidence) == 1
        assert "test_task_001" in knowledge_entry.related_tasks
    
    def test_confidence_score_calculation(self, knowledge_entry):
        """信頼度スコア計算テスト"""
        score = knowledge_entry.get_confidence_score()
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_execution_summary(self, knowledge_entry):
        """実行サマリーテスト"""
        summary = knowledge_entry.get_execution_summary()
        assert isinstance(summary, dict)
        assert "total_executions" in summary
        assert "success_rate" in summary
        assert "avg_execution_time" in summary
        assert "avg_quality_score" in summary
    
    def test_prediction_capability(self, knowledge_entry):
        """予測機能テスト"""
        from libs.four_sages.knowledge.execution_linked_knowledge_entry import ExecutionContext
        
        prediction = knowledge_entry.predict_execution_outcome(ExecutionContext.TASK_EXECUTION)
        assert isinstance(prediction, dict)
        assert "predicted_success_rate" in prediction
        assert "predicted_execution_time" in prediction
        assert "confidence" in prediction
    
    def test_verification_need_assessment(self, knowledge_entry):
        """検証必要性評価テスト"""
        needs_verification = knowledge_entry.needs_verification()
        assert isinstance(needs_verification, bool)
    
    def test_dictionary_conversion(self, knowledge_entry):
        """辞書変換テスト"""
        knowledge_dict = knowledge_entry.to_dict()
        assert isinstance(knowledge_dict, dict)
        
        # 基本フィールドの確認
        assert "id" in knowledge_dict
        assert "title" in knowledge_dict
        assert "content" in knowledge_dict
        
        # 拡張フィールドの確認
        assert "execution_evidence" in knowledge_dict
        assert "verification_history" in knowledge_dict
        assert "execution_summary" in knowledge_dict
        assert "confidence_score" in knowledge_dict
        assert "needs_verification" in knowledge_dict

class TestPatternExtractionEngine:
    """PatternExtractionEngine テストクラス"""
    
    @pytest.fixture
    def pattern_engine(self):
        """PatternExtractionEngine インスタンス"""
        return PatternExtractionEngine()
    
    @pytest.fixture
    def sample_execution_data(self):
        """サンプル実行データ"""
        return [
            {
                "task_id": f"task_{i}",
                "status": "completed" if i % 2 == 0 else "failed",
                "execution_time_seconds": 120.0 + i * 10,
                "overall_score": 0.8 + (i % 3) * 0.1,
                "iron_will_compliant": i % 2 == 0,
                "execution_details": [],
                "quality_metrics": {}
            }
            for i in range(20)
        ]
    
    @pytest.mark.asyncio
    async def test_pattern_extraction(self, pattern_engine, sample_execution_data):
        """パターン抽出テスト"""
        patterns = await pattern_engine.extract_execution_patterns(sample_execution_data)
        assert isinstance(patterns, list)
        
        # パターンの構造確認
        for pattern in patterns:
            assert hasattr(pattern, 'cluster_id')
            assert hasattr(pattern, 'pattern_type')
            assert hasattr(pattern, 'members')
            assert hasattr(pattern, 'characteristics')
            assert hasattr(pattern, 'quality_metrics')
            assert hasattr(pattern, 'confidence')
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, pattern_engine, sample_execution_data):
        """異常検知テスト"""
        patterns = await pattern_engine.extract_execution_patterns(sample_execution_data)
        if patterns:
            anomalies = await pattern_engine.identify_anomalous_patterns(patterns)
            assert isinstance(anomalies, list)
            
            # 異常の構造確認
            for anomaly in anomalies:
                assert "pattern" in anomaly
                assert "anomaly_score" in anomaly
                assert "anomaly_type" in anomaly
                assert "impact_assessment" in anomaly
    
    @pytest.mark.asyncio
    async def test_pattern_evolution_analysis(self, pattern_engine, sample_execution_data):
        """パターン進化分析テスト"""
        patterns = await pattern_engine.extract_execution_patterns(sample_execution_data)
        if patterns:
            evolution = await pattern_engine.analyze_pattern_evolution(patterns)
            assert isinstance(evolution, list)
            
            # 進化の構造確認
            for evo in evolution:
                assert hasattr(evo, 'pattern_id')
                assert hasattr(evo, 'evolution_type')
                assert hasattr(evo, 'trend_direction')
                assert hasattr(evo, 'confidence')

class TestPredictiveRecommendationSystem:
    """PredictiveRecommendationSystem テストクラス"""
    
    @pytest.fixture
    def recommendation_system(self):
        """PredictiveRecommendationSystem インスタンス"""
        return PredictiveRecommendationSystem()
    
    @pytest.fixture
    def sample_execution_data(self):
        """サンプル実行データ"""
        return [
            {
                "task_id": f"task_{i}",
                "description": f"Sample task {i}",
                "status": "completed" if i % 2 == 0 else "failed",
                "execution_time_seconds": 120.0 + i * 10,
                "overall_score": 0.8 + (i % 3) * 0.1,
                "iron_will_compliant": i % 2 == 0,
                "priority": "high" if i % 3 == 0 else "medium",
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "execution_details": [],
                "logs": [],
                "quality_metrics": {},
                "sage_advice": {}
            }
            for i in range(30)
        ]
    
    @pytest.mark.asyncio
    async def test_model_training(self, recommendation_system, sample_execution_data):
        """モデル訓練テスト"""
        accuracy = await recommendation_system.train_prediction_models(sample_execution_data)
        assert isinstance(accuracy, dict)
        
        # 精度メトリクスの確認
        if accuracy:
            assert "execution_time" in accuracy
            assert "success_rate" in accuracy
            assert "quality_score" in accuracy
    
    @pytest.mark.asyncio
    async def test_execution_outcome_prediction(self, recommendation_system, sample_execution_data):
        """実行結果予測テスト"""
        # モデルを訓練
        await recommendation_system.train_prediction_models(sample_execution_data)
        
        # 予測実行
        prediction = await recommendation_system.predict_execution_outcome(
            "Test task for prediction",
            {"priority": "high", "historical_success_rate": 0.85}
        )
        
        assert hasattr(prediction, 'predicted_value')
        assert hasattr(prediction, 'confidence')
        assert hasattr(prediction, 'prediction_interval')
        assert hasattr(prediction, 'model_accuracy')
    
    @pytest.mark.asyncio
    async def test_recommendation_generation(self, recommendation_system):
        """推奨事項生成テスト"""
        recommendations = await recommendation_system.generate_recommendations(
            {"historical_success_rate": 0.8, "avg_execution_time": 120.0},
            "optimization"
        )
        
        assert isinstance(recommendations, list)
        
        # 推奨事項の構造確認
        for rec in recommendations:
            assert hasattr(rec, 'recommendation_id')
            assert hasattr(rec, 'title')
            assert hasattr(rec, 'description')
            assert hasattr(rec, 'priority')
            assert hasattr(rec, 'confidence')
            assert hasattr(rec, 'expected_impact')
    
    @pytest.mark.asyncio
    async def test_feedback_processing(self, recommendation_system):
        """フィードバック処理テスト"""
        recommendation_id = "test_recommendation_001"
        feedback = {
            "rating": 0.8,
            "user_id": "test_user",
            "helpful": True
        }
        
        result = await recommendation_system.update_recommendation_feedback(
            recommendation_id, feedback
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, recommendation_system):
        """パフォーマンスメトリクステスト"""
        performance = await recommendation_system.get_recommendation_performance(days=30)
        assert isinstance(performance, dict)
        
        # パフォーマンスメトリクスの確認
        assert "total_recommendations" in performance
        assert "total_feedback" in performance
        assert "feedback_rate" in performance
        assert "model_accuracy" in performance

class TestSelfEvolvingKnowledgeManager:
    """SelfEvolvingKnowledgeManager テストクラス"""
    
    @pytest.fixture
    def evolution_manager(self):
        """SelfEvolvingKnowledgeManager インスタンス"""
        return SelfEvolvingKnowledgeManager()
    
    @pytest.mark.asyncio
    async def test_population_initialization(self, evolution_manager):
        """集団初期化テスト"""
        result = await evolution_manager.initialize_knowledge_population()
        assert isinstance(result, bool)
        
        # 集団の確認
        assert isinstance(evolution_manager.knowledge_population, list)
    
    @pytest.mark.asyncio
    async def test_evolution_status(self, evolution_manager):
        """進化状況テスト"""
        status = await evolution_manager.get_evolution_status()
        assert isinstance(status, dict)
        assert "status" in status
    
    @pytest.mark.asyncio
    async def test_auto_evolution(self, evolution_manager):
        """自動進化テスト"""
        # 初期化
        await evolution_manager.initialize_knowledge_population()
        
        # 自動進化実行
        result = await evolution_manager.auto_evolve()
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_knowledge_base_evolution(self, evolution_manager):
        """知識ベース進化テスト"""
        # 初期化
        await evolution_manager.initialize_knowledge_population()
        
        # 進化実行（小規模）
        result = await evolution_manager.evolve_knowledge_base(generations=2)
        
        # 結果の確認
        if result:
            assert hasattr(result, 'generation_number')
            assert hasattr(result, 'fitness_scores')
            assert hasattr(result, 'best_individual')
            assert hasattr(result, 'diversity_index')

# 統合テストの実行
if __name__ == "__main__":
    print("🧪 Phase 22 Knowledge Sage Integration Tests Starting...")
    
    # テストの実行
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("✅ Phase 22 Knowledge Sage Integration Tests Completed")
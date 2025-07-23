#!/usr/bin/env python3
"""
🧠 Learning Magic テストスイート
===============================

Learning Magic（学習魔法）の包括的なテストスイート。
自己進化、パターン学習、知識統合をテスト。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
from typing import Dict, Any, List
import json
import tempfile
from pathlib import Path
from datetime import datetime

# テスト対象をインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ancient_magic.learning_magic.learning_magic import LearningMagic


class TestLearningMagic:


"""Learning Magic テストクラス"""
        """Learning Magic インスタンスを作成"""
        return LearningMagic()
        
    @pytest.fixture
    def sample_knowledge_base(self):

        """テスト用知識ベース""" [
                {
                    "pattern": "TDD Implementation",
                    "success_rate": 0.95,
                    "usage_count": 150,
                    "feedback_score": 4.8
                },
                {
                    "pattern": "Microservices Architecture", 
                    "success_rate": 0.87,
                    "usage_count": 89,
                    "feedback_score": 4.2
                }
            ],
            "failure_cases": [
                {
                    "case": "Memory leak in batch processing",
                    "frequency": 12,
                    "resolution_time": "2 hours",
                    "learned_fix": "Use context managers for resource cleanup"
                }
            ],
            "optimization_history": [
                {
                    "component": "database_queries",
                    "before_performance": 500,  # ms
                    "after_performance": 50,   # ms  
                    "optimization": "Added indexes and query optimization"
                }
            ]
        }
        
    @pytest.fixture
    def mock_sage_responses(self):

                """モック賢者応答""" {
                "patterns_identified": 15,
                "knowledge_gaps": ["advanced_security", "performance_tuning"],
                "confidence": 0.85
            },
            "task": {
                "completed_tasks": 240,
                "success_rate": 0.92,
                "bottlenecks": ["code_review", "testing"]
            },
            "incident": {
                "incidents_resolved": 45,
                "resolution_time_avg": "1.5 hours",
                "preventable_incidents": 0.30
            },
            "rag": {
                "search_accuracy": 0.88,
                "knowledge_coverage": 0.75,
                "response_time": "200ms"
            }
        }
        
    # Phase 1: 基本的な学習機能（Basic Learning）
    async def test_learn_from_success_pattern(self, learning_magic):

    """成功パターンからの学習テスト""" "API endpoint optimization",
            "method": "Caching strategy implementation",
            "result": {
                "performance_improvement": 0.70,
                "resource_reduction": 0.45,
                "user_satisfaction": 0.95
            },
            "context": {
                "technology": "FastAPI",
                "data_size": "medium",
                "user_load": "high"
            }
        }
        
        result = await learning_magic.learn_from_success(success_case)
        
        assert result["success"] is True
        assert "learned_pattern" in result
        pattern = result["learned_pattern"]
        assert pattern["pattern_type"] == "optimization"
        assert pattern["confidence_score"] >= 0.7
        assert "replication_guide" in pattern
        assert "applicable_contexts" in pattern
        
    async def test_learn_from_failure_case(self, learning_magic):

            """失敗ケースからの学習テスト""" "Database connection pool exhaustion",
            "root_cause": "Unclosed connections in error handling paths",
            "impact": {
                "downtime": "15 minutes",
                "affected_users": 1500,
                "revenue_loss": 5000
            },
            "resolution": {
                "immediate_fix": "Restart service with increased pool size",
                "permanent_fix": "Add connection cleanup in finally blocks",
                "prevention": "Add connection monitoring alerts"
            }
        }
        
        result = await learning_magic.learn_from_failure(failure_case)
        
        assert result["success"] is True
        assert "learned_lesson" in result
        lesson = result["learned_lesson"]
        assert lesson["lesson_type"] == "prevention"
        assert lesson["criticality"] == "high"
        assert "prevention_strategies" in lesson
        assert "early_warning_signs" in lesson
        assert "automated_checks" in lesson
        
    async def test_identify_learning_opportunities(self, learning_magic, sample_knowledge_base):

            """学習機会の特定テスト"""
            assert "domain" in opportunity
            assert "learning_type" in opportunity
            assert "expected_benefit" in opportunity
            assert "effort_estimate" in opportunity
            
    # Phase 2: 知識統合（Knowledge Integration）
    async def test_integrate_sage_knowledge(self, learning_magic, mock_sage_responses):

    """4賢者知識統合テスト"""
        """パターン合成テスト"""
        individual_patterns = [
            {
                "domain": "backend",
                "pattern": "Database connection pooling",
                "effectiveness": 0.85
            },
            {
                "domain": "frontend", 
                "pattern": "Component lazy loading",
                "effectiveness": 0.78
            },
            {
                "domain": "infrastructure",
                "pattern": "Auto-scaling based on metrics",
                "effectiveness": 0.92
            }
        ]
        
        result = await learning_magic.synthesize_patterns(individual_patterns)
        
        assert result["success"] is True
        synthesized = result["synthesized_patterns"]
        
        # 合成パターンが生成されているか確認
        assert "universal_patterns" in synthesized
        assert "domain_specific_adaptations" in synthesized
        
        # 汎用パターンの品質確認
        universal = synthesized["universal_patterns"]
        for pattern in universal:
            assert "core_principle" in pattern
            assert "adaptability_score" in pattern
            assert pattern["adaptability_score"] >= 0.6
            
    # Phase 3: 自己進化（Self Evolution）
    async def test_evolve_system_capabilities(self, learning_magic):

    """システム能力進化テスト""" {
                "knowledge": {"accuracy": 0.85, "response_time": 0.3},
                "task": {"completion_rate": 0.90, "efficiency": 0.75},
                "incident": {"resolution_time": 0.8, "prevention_rate": 0.65},
                "rag": {"search_precision": 0.88, "relevance": 0.82}
            },
            "elder_servants_status": {
                "implemented": 19,
                "total": 32,
                "average_performance": 0.78
            },
            "overall_metrics": {
                "system_reliability": 0.92,
                "user_satisfaction": 0.85,
                "development_speed": 0.70
            }
        }
        
        result = await learning_magic.evolve_system_capabilities(current_state)
        
        assert result["success"] is True
        evolution = result["evolution_plan"]
        
        # 進化計画の要素確認
        assert "capability_enhancements" in evolution
        assert "new_features" in evolution
        assert "optimization_targets" in evolution
        assert "implementation_roadmap" in evolution
        
        # 各項目の詳細確認
        enhancements = evolution["capability_enhancements"]
        for enhancement in enhancements:
            assert "target_component" in enhancement
            assert "current_level" in enhancement
            assert "target_level" in enhancement
            assert "improvement_method" in enhancement
            
    async def test_predict_system_growth(self, learning_magic):

            """システム成長予測テスト""" [
                {"date": "2025-01-01", "metric": "response_time", "value": 0.5},
                {"date": "2025-02-01", "metric": "response_time", "value": 0.4},
                {"date": "2025-03-01", "metric": "response_time", "value": 0.35}
            ],
            "feature_adoption": [
                {"feature": "TDD_workflow", "adoption_rate": 0.8, "month": 1},
                {"feature": "TDD_workflow", "adoption_rate": 0.9, "month": 2},
                {"feature": "TDD_workflow", "adoption_rate": 0.95, "month": 3}
            ],
            "user_feedback": [
                {"period": "Q1", "satisfaction": 0.75, "usage": 1000},
                {"period": "Q2", "satisfaction": 0.82, "usage": 1200},
                {"period": "Q3", "satisfaction": 0.85, "usage": 1400}
            ]
        }
        
        result = await learning_magic.predict_system_growth(historical_data, months_ahead=6)
        
        assert result["success"] is True
        predictions = result["predictions"]
        
        # 予測の構造確認
        assert "performance_forecast" in predictions
        assert "feature_evolution" in predictions
        assert "capacity_requirements" in predictions
        assert "risk_factors" in predictions
        
        # 予測精度の確認
        forecast = predictions["performance_forecast"]
        for metric in forecast:
            assert "confidence_interval" in metric
            assert metric["confidence"] >= 0.6
            
    # Phase 4: メタ学習（Meta Learning）
    async def test_learn_how_to_learn(self, learning_magic):

    """学習方法の学習テスト""" [
                {
                    "method": "pattern_recognition",
                    "data_size": 1000,
                    "learning_time": 30,  # minutes
                    "accuracy_improvement": 0.15,
                    "retention_rate": 0.90
                },
                {
                    "method": "failure_analysis",
                    "data_size": 50,
                    "learning_time": 60,
                    "accuracy_improvement": 0.25,
                    "retention_rate": 0.95
                }
            ],
            "learning_failures": [
                {
                    "method": "brute_force_memorization",
                    "reason": "low_retention",
                    "retention_rate": 0.40
                }
            ]
        }
        
        result = await learning_magic.learn_how_to_learn(learning_history)
        
        assert result["success"] is True
        meta_learning = result["meta_learning"]
        
        # メタ学習結果の確認
        assert "optimal_methods" in meta_learning
        assert "method_selection_rules" in meta_learning
        assert "learning_efficiency_predictors" in meta_learning
        
        # 最適化された学習戦略の確認
        optimal_methods = meta_learning["optimal_methods"]
        for method in optimal_methods:
            assert "method_name" in method
            assert "effectiveness_score" in method
            assert "recommended_contexts" in method
            
    # Phase 5: 協調学習（Collaborative Learning）
    async def test_learn_from_servant_interactions(self, learning_magic):

    """サーバント間相互作用からの学習テスト""" [
                {
                    "servants": ["CodeCrafter", "QualityGuardian"],
                    "task": "API endpoint implementation",
                    "interaction_pattern": "sequential_handoff",
                    "success_metrics": {
                        "quality_score": 0.92,
                        "completion_time": 45,  # minutes
                        "error_rate": 0.02
                    }
                },
                {
                    "servants": ["SecurityGuard", "PerformanceTuner"],
                    "task": "system_optimization",
                    "interaction_pattern": "parallel_validation",
                    "success_metrics": {
                        "security_score": 0.95,
                        "performance_gain": 0.35,
                        "coordination_overhead": 0.10
                    }
                }
            ],
            "failed_collaborations": [
                {
                    "servants": ["DocForge", "TestForge"],
                    "task": "documentation_generation",
                    "failure_reason": "conflicting_output_formats",
                    "resolution": "standardized_interface_definition"
                }
            ]
        }
        
        result = await learning_magic.learn_from_servant_interactions(servant_interactions)
        
        assert result["success"] is True
        collaboration_insights = result["collaboration_insights"]
        
        # 協調学習結果の確認
        assert "optimal_collaboration_patterns" in collaboration_insights
        assert "servant_compatibility_matrix" in collaboration_insights
        assert "coordination_best_practices" in collaboration_insights
        
        # パターンの品質確認
        patterns = collaboration_insights["optimal_collaboration_patterns"]
        for pattern in patterns:
            assert "pattern_name" in pattern
            assert "success_rate" in pattern
            assert "recommended_use_cases" in pattern
            assert pattern["success_rate"] >= 0.75
            
    # Phase 6: 継続学習（Continuous Learning）
    async def test_continuous_learning_cycle(self, learning_magic):

    """継続学習サイクルテスト""" "daily",
            "data_sources": ["sage_interactions", "servant_performance", "user_feedback"],
            "learning_targets": ["pattern_recognition", "performance_optimization"],
            "retention_period": "90_days"
        }
        
        result = await learning_magic.start_continuous_learning(cycle_config)
        
        assert result["success"] is True
        cycle_status = result["cycle_status"]
        
        # 継続学習システムの確認
        assert cycle_status["status"] == "active"
        assert "next_learning_session" in cycle_status
        assert "learning_queue" in cycle_status
        assert "performance_metrics" in cycle_status
        
        # 学習キューの内容確認
        queue = cycle_status["learning_queue"]
        assert len(queue) > 0
        for item in queue:
            assert "data_source" in item
            assert "learning_type" in item
            assert "priority" in item
            assert "estimated_duration" in item
            
    async def test_measure_learning_effectiveness(self, learning_magic):

            """学習効果測定テスト""" "learning_session_001",
            "start_time": "2025-01-01T10:00:00",
            "end_time": "2025-01-01T10:30:00",
            "learning_type": "pattern_recognition",
            "data_processed": 500,
            "patterns_discovered": 12,
            "pre_test_score": 0.70,
            "post_test_score": 0.85,
            "retention_test_score": 0.82  # 1週間後
        }
        
        result = await learning_magic.measure_learning_effectiveness(learning_session_data)
        
        assert result["success"] is True
        effectiveness = result["effectiveness_metrics"]
        
        # 効果測定指標の確認
        assert "learning_gain" in effectiveness
        assert "retention_rate" in effectiveness
        assert "knowledge_transfer_score" in effectiveness
        assert "learning_efficiency" in effectiveness
        
        # 学習効果の品質確認
        assert effectiveness["learning_gain"] > 0
        assert effectiveness["retention_rate"] >= 0.8
        assert effectiveness["learning_efficiency"] > 0
        
    # Phase 7: Elder Tree統合テスト
    async def test_elder_tree_learning_integration(self, learning_magic):

    """Elder Tree学習統合テスト""" {
                "4_sages_metrics": {
                    "knowledge_sage": {"query_accuracy": 0.87, "response_time": 0.25},
                    "task_sage": {"task_completion": 0.93, "resource_efficiency": 0.81},
                    "incident_sage": {"resolution_speed": 0.78, "prevention_rate": 0.65},
                    "rag_sage": {"search_precision": 0.89, "context_relevance": 0.84}
                },
                "servant_performance": {
                    "active_servants": 19,
                    "average_quality_score": 0.82,
                    "collaboration_efficiency": 0.76
                }
            },
            "user_interactions": {
                "session_count": 1250,
                "satisfaction_score": 0.86,
                "feature_usage": {
                    "tdd_workflow": 0.92,
                    "code_review": 0.78,
                    "automated_testing": 0.85
                }
            }
        }
        
        result = await learning_magic.integrate_with_elder_tree(elder_tree_data)
        
        assert result["success"] is True
        integration = result["integration_result"]
        
        # Elder Tree統合結果の確認
        assert "system_improvements" in integration
        assert "sage_enhancements" in integration  
        assert "servant_optimizations" in integration
        assert "user_experience_upgrades" in integration
        
        # 改善提案の品質確認
        improvements = integration["system_improvements"]
        for improvement in improvements:
            assert "component" in improvement
            assert "current_performance" in improvement
            assert "target_performance" in improvement
            assert "implementation_plan" in improvement


@pytest.mark.asyncio
class TestLearningMagicIntegration:

            """Learning Magic統合テスト"""
        """4賢者学習協調テスト"""
        learning_magic = LearningMagic()
        
        # 4賢者からの学習データを模擬
        sage_learning_data = {
            "knowledge_sage": {
                "new_patterns": 5,
                "knowledge_quality_improvement": 0.12,
                "learning_session_duration": 20
            },
            "task_sage": {
                "workflow_optimizations": 3,
                "efficiency_gain": 0.18,
                "automation_opportunities": 7
            },
            "incident_sage": {
                "prevention_strategies": 4,
                "resolution_time_improvement": 0.25,
                "false_positive_reduction": 0.15
            },
            "rag_sage": {
                "search_accuracy_improvement": 0.08,
                "context_understanding_gain": 0.20,
                "response_relevance_boost": 0.13
            }
        }
        
        result = await learning_magic.coordinate_sage_learning(sage_learning_data)
        
        assert result["success"] is True
        assert "learning_synthesis" in result
        assert "cross_sage_insights" in result
        assert result["overall_system_improvement"] > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
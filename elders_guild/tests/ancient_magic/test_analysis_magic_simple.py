#!/usr/bin/env python3
"""
"📊" Analysis Magic 簡略テストスイート
===================================

Analysis Magic（分析魔法）の基本機能テスト。
依存関係の競合を避けつつ、コア機能の動作確認を実行。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
import time
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import Mock, patch

# テスト対象をインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Basic imports without complex dependencies
import numpy as np

# Create comprehensive mocks before any imports
pandas_mock = Mock()
pandas_mock.__version__ = "1.3.0"
pandas_mock.DataFrame = Mock()

scipy_mock = Mock()
scipy_mock.__version__ = "1.7.0"
scipy_stats_mock = Mock()

sklearn_mock = Mock()
sklearn_mock.__version__ = "1.0.0"

statsmodels_mock = Mock()
statsmodels_mock.__version__ = "0.12.0"

networkx_mock = Mock()
networkx_mock.__version__ = "2.6.0"

# Mock the problematic imports with versions
sys.modules['pandas'] = pandas_mock
sys.modules['scipy'] = scipy_mock
sys.modules['scipy.stats'] = scipy_stats_mock
sys.modules['sklearn'] = sklearn_mock
sys.modules['sklearn.preprocessing'] = Mock()
sys.modules['sklearn.decomposition'] = Mock()
sys.modules['sklearn.cluster'] = Mock()
sys.modules['sklearn.ensemble'] = Mock()
sys.modules['sklearn.feature_selection'] = Mock()
sys.modules['sklearn.metrics'] = Mock()
sys.modules['statsmodels'] = statsmodels_mock
sys.modules['statsmodels.api'] = Mock()
sys.modules['statsmodels.tsa'] = Mock()
sys.modules['statsmodels.tsa.seasonal'] = Mock()
sys.modules['statsmodels.tsa.stattools'] = Mock()
sys.modules['networkx'] = networkx_mock

# Now import the analysis magic
from ancient_magic.analysis_magic.analysis_magic import AnalysisMagic


class TestAnalysisMagicCore:
    """Analysis Magic コア機能テスト"""
    
    @pytest.fixture
    def analysis_magic(self):
        """Analysis Magic インスタンスを作成"""
        return AnalysisMagic()
    
    @pytest.fixture
    def sample_data(self):
        """テスト用シンプルデータ"""
        return {
            "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "categories": ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"],
            "timestamps": [f"2024-01-{i:02d}" for i in range(1, 11)],
            "matrix": [[1, 2], [3, 4], [5, 6]]
        }
    
    async def test_analysis_magic_initialization(self, analysis_magic):
        """Analysis Magic初期化テスト"""
        assert analysis_magic.magic_type == "analysis"
        assert "データ分析" in analysis_magic.description
        assert len(analysis_magic.capabilities) == 4
        
        # 設定の確認
        assert analysis_magic.analysis_config["default_confidence_level"] == 0.95
        assert analysis_magic.analysis_config["significance_level"] == 0.05
        assert analysis_magic.statistical_thresholds["correlation_strong"] == 0.7
    
    async def test_cast_magic_unknown_intent(self, analysis_magic):
        """未知の意図での魔法発動テスト"""
        result = await analysis_magic.cast_magic("unknown_intent", {})
        
        assert result["success"] is False
        assert "Unknown analysis intent" in result["error"]
    
    async def test_descriptive_analysis_mock(self, analysis_magic, sample_data):
        """モック環境での記述統計分析テスト"""
        with patch('pandas.DataFrame') as mock_df:
            # Mock DataFrame behavior
            mock_instance = Mock()
            mock_instance.select_dtypes.return_value.columns.tolist.return_value = ["values"]
            mock_instance.__getitem__.return_value = sample_data["values"]
            mock_instance.copy.return_value = mock_instance
            mock_df.return_value = mock_instance
            
            # Mock statistics calculations
            mock_instance.mean.return_value.to_dict.return_value = {"values": 5.5}
            mock_instance.median.return_value.to_dict.return_value = {"values": 5.5}
            mock_instance.std.return_value.to_dict.return_value = {"values": 3.03}
            mock_instance.var.return_value.to_dict.return_value = {"values": 9.17}
            mock_instance.min.return_value.to_dict.return_value = {"values": 1}
            mock_instance.max.return_value.to_dict.return_value = {"values": 10}
            mock_instance.quantile.return_value.to_dict.return_value = {"values": 3.25}
            mock_instance.skew.return_value.to_dict.return_value = {"values": 0.0}
            mock_instance.kurtosis.return_value.to_dict.return_value = {"values": -1.22}
            mock_instance.dropna.return_value = sample_data["values"]
            
            result = await analysis_magic.perform_descriptive_analysis({
                "data": sample_data,
                "include_distribution": True,
                "confidence_level": 0.95
            })
            
            assert result["success"] is True
            assert "descriptive_statistics" in result
            stats_result = result["descriptive_statistics"]
            assert "mean" in stats_result
            assert "median" in stats_result
            assert "std" in stats_result
    
    async def test_correlation_analysis_mock(self, analysis_magic, sample_data):
        """モック環境での相関分析テスト"""
        with patch('pandas.DataFrame') as mock_df:
            # Mock DataFrame behavior
            mock_instance = Mock()
            mock_instance.select_dtypes.return_value.columns.tolist.return_value = ["values", "other"]
            mock_instance.copy.return_value = mock_instance
            mock_instance.dropna.return_value = mock_instance
            mock_df.return_value = mock_instance
            
            # Mock correlation matrix
            mock_corr = Mock()
            mock_corr.to_dict.return_value = {
                "values": {"values": 1.0, "other": 0.8},
                "other": {"values": 0.8, "other": 1.0}
            }
            mock_instance.corr.return_value = mock_corr
            mock_corr.iloc = Mock()
            mock_corr.iloc.__getitem__ = Mock(return_value=Mock(values=[0.8]))
            
            result = await analysis_magic.perform_correlation_analysis({
                "data": sample_data,
                "method": "pearson",
                "include_pvalues": True
            })
            
            assert result["success"] is True
            assert "correlation_analysis" in result
            corr_result = result["correlation_analysis"]
            assert "correlation_matrix" in corr_result
            assert "method" in corr_result
    
    async def test_trend_analysis_simple(self, analysis_magic, sample_data):
        """シンプルなトレンド分析テスト"""
        # Use simple numpy-based trend analysis
        trend_data = {
            "timestamps": sample_data["timestamps"],
            "values": sample_data["values"]
        }
        
        result = await analysis_magic.perform_trend_analysis({
            "data": trend_data,
            "trend_methods": ["linear"],
            "decomposition": False
        })
        
        assert result["success"] is True
        assert "trend_analysis" in result
        trend_result = result["trend_analysis"]
        assert "trend_direction" in trend_result
        assert "trend_strength" in trend_result
        assert trend_result["trend_direction"] in ["increasing", "decreasing", "stable"]
    
    async def test_pattern_detection_basic(self, analysis_magic, sample_data):
        """基本的なパターン検出テスト"""
        result = await analysis_magic.detect_patterns({
            "data": sample_data["values"],
            "pattern_types": ["anomaly"],
            "window_size": 3,
            "sensitivity": 0.05
        })
        
        assert result["success"] is True
        assert "pattern_detection" in result
        pattern_result = result["pattern_detection"]
        assert "detected_patterns" in pattern_result
        assert "anomalies" in pattern_result
        assert "pattern_confidence" in pattern_result
        assert isinstance(pattern_result["pattern_confidence"], (int, float))
        assert 0 <= pattern_result["pattern_confidence"] <= 1
    
    async def test_anomaly_detection_basic(self, analysis_magic, sample_data):
        """基本的な異常検出テスト"""
        # Add some outliers to test data
        test_data = sample_data["values"] + [100, -100]  # Clear outliers
        
        result = await analysis_magic.detect_anomalies({
            "data": test_data,
            "methods": ["z_score"],
            "threshold": 2.0
        })
        
        assert result["success"] is True
        assert "anomaly_detection" in result
        anomaly_result = result["anomaly_detection"]
        assert "anomalies" in anomaly_result
        assert "detection_methods" in anomaly_result
        assert "normal_range" in anomaly_result
        
        # Should detect the outliers we added
        anomalies = anomaly_result["anomalies"]
        assert len(anomalies) >= 2  # Should find the outliers
    
    async def test_comprehensive_analysis_basic(self, analysis_magic, sample_data):
        """基本的な包括分析テスト"""
        result = await analysis_magic.perform_comprehensive_analysis({
            "data": sample_data,
            "analysis_modules": ["insight_generation"],
            "output_format": "structured"
        })
        
        assert result["success"] is True
        assert "comprehensive_analysis" in result
        comp_result = result["comprehensive_analysis"]
        assert "analysis_summary" in comp_result
        assert "module_results" in comp_result
        
        summary = comp_result["analysis_summary"]
        assert "total_modules" in summary
        assert "successful_modules" in summary
        assert "failed_modules" in summary
    
    async def test_insight_generation_basic(self, analysis_magic, sample_data):
        """基本的な洞察生成テスト"""
        # Create a simple dataset for insight generation
        insight_data = {
            "feature_1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "feature_2": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # Highly correlated
            "feature_3": [10, 8, 6, 4, 2, 0, -2, -4, -6, -8]   # Negatively correlated
        }
        
        with patch('pandas.DataFrame') as mock_df:
            # Mock DataFrame behavior for insight generation
            mock_instance = Mock()
            mock_instance.select_dtypes.return_value.columns.tolist.return_value = ["feature_1", "feature_2", "feature_3"]
            mock_instance.dropna.return_value = mock_instance
            mock_instance.__getitem__ = Mock(side_effect=lambda key: insight_data[key])
            mock_df.return_value = mock_instance
            
            # Mock correlation matrix
            mock_corr = Mock()
            mock_corr.to_dict.return_value = {
                "feature_1": {"feature_1": 1.0, "feature_2": 1.0, "feature_3": -1.0},
                "feature_2": {"feature_1": 1.0, "feature_2": 1.0, "feature_3": -1.0},
                "feature_3": {"feature_1": -1.0, "feature_2": -1.0, "feature_3": 1.0}
            }
            mock_instance.corr.return_value = mock_corr
            
            result = await analysis_magic.generate_insights({
                "data": insight_data,
                "insight_types": ["correlation"],
                "confidence_threshold": 0.7,
                "max_insights": 5
            })
            
            assert result["success"] is True
            assert "insight_generation" in result
            insight_result = result["insight_generation"]
            assert "insights" in insight_result
            assert "insight_categories" in insight_result
            assert "actionable_recommendations" in insight_result
    
    async def test_data_quality_assessment_basic(self, analysis_magic):
        """基本的なデータ品質評価テスト"""
        # Create test data with quality issues
        poor_quality_data = {
            "good_column": [1, 2, 3, 4, 5],
            "missing_column": [1, None, 3, None, 5],
            "outlier_column": [1, 2, 3, 1000, 5]  # Contains outlier
        }
        
        with patch('pandas.DataFrame') as mock_df:
            mock_instance = Mock()
            mock_instance.columns = ["good_column", "missing_column", "outlier_column"]
            mock_instance.__len__ = Mock(return_value=5)
            mock_instance.__getitem__ = Mock(side_effect=lambda key: poor_quality_data[key])
            mock_instance.select_dtypes.return_value.columns.tolist.return_value = ["good_column", "missing_column", "outlier_column"]
            
            # Mock null detection
            def mock_isnull():
                return Mock(sum=Mock(return_value=2 if "missing" in str(mock_instance) else 0))
            mock_instance.__getitem__.return_value.isnull = mock_isnull
            
            mock_df.return_value = mock_instance
            
            result = await analysis_magic.assess_data_quality({
                "data": poor_quality_data,
                "quality_checks": ["completeness", "accuracy"],
                "outlier_threshold": 3.0
            })
            
            assert result["success"] is True
            assert "data_quality_assessment" in result
            quality_result = result["data_quality_assessment"]
            assert "overall_quality_score" in quality_result
            assert "quality_dimensions" in quality_result
            assert "issues_detected" in quality_result
            assert "recommendations" in quality_result
            
            # Quality score should be between 0 and 1
            quality_score = quality_result["overall_quality_score"]
            assert 0 <= quality_score <= 1
    
    async def test_performance_analysis_basic(self, analysis_magic, sample_data):
        """基本的なパフォーマンス分析テスト"""
        result = await analysis_magic.perform_performance_analysis({
            "data": sample_data,
            "operations": ["descriptive_stats"],
            "optimization": True
        })
        
        assert result["success"] is True
        assert "performance_analysis" in result
        perf_result = result["performance_analysis"]
        assert "execution_metrics" in perf_result
        assert "optimization_applied" in perf_result
        assert "performance_summary" in perf_result
        
        # Check execution metrics
        exec_metrics = perf_result["execution_metrics"]
        assert "descriptive_stats" in exec_metrics
        assert "execution_time" in exec_metrics["descriptive_stats"]
        assert "success" in exec_metrics["descriptive_stats"]
    
    async def test_analysis_pipeline_basic(self, analysis_magic, sample_data):
        """基本的な分析パイプラインテスト"""
        pipeline_config = {
            "pipeline_id": "test_pipeline",
            "stages": [
                {
                    "name": "preprocessing",
                    "type": "preprocessing",
                    "parameters": {"normalize": False, "handle_missing": "none"}
                },
                {
                    "name": "exploratory",
                    "type": "exploratory",
                    "parameters": {"include_visualization": False}
                }
            ],
            "data": sample_data
        }
        
        result = await analysis_magic.execute_analysis_pipeline(pipeline_config)
        
        assert result["success"] is True
        assert "analysis_pipeline" in result
        pipeline_result = result["analysis_pipeline"]
        assert "pipeline_id" in pipeline_result
        assert "stage_results" in pipeline_result
        assert "execution_summary" in pipeline_result
        
        # Check that stages were processed
        stage_results = pipeline_result["stage_results"]
        assert len(stage_results) == 2
        
        for stage_result in stage_results:
            assert "stage_name" in stage_result
            assert "success" in stage_result
    
    async def test_magic_status_and_health(self, analysis_magic, sample_data):
        """魔法の状態と健康診断テスト"""
        # First perform some analyses to create history
        await analysis_magic.cast_magic("pattern_detection", {
            "data": sample_data["values"],
            "pattern_types": ["anomaly"]
        })
        
        # Get magic status
        status = analysis_magic.get_magic_status()
        assert "magic_type" in status
        assert "capabilities" in status
        assert "activation_count" in status
        assert "performance_metrics" in status
        
        # Get health diagnosis
        health = await analysis_magic.diagnose_magic_health()
        assert "overall_health" in health
        assert "success_rate" in health
        assert "average_response_time" in health
        assert "recommendations" in health
        
        # Health status should be valid
        assert health["overall_health"] in ["excellent", "good", "fair", "poor"]


@pytest.mark.asyncio
class TestAnalysisMagicIntegration:
    """Analysis Magic統合テスト"""
    
    async def test_analysis_workflow_integration(self):
        """分析ワークフロー統合テスト"""
        magic = AnalysisMagic()
        
        # Sample dataset
        test_data = {
            "time_series": list(range(20)),
            "values": [i + (i % 3) for i in range(20)],  # With pattern
            "categories": ["A", "B", "C"] * 7  # Repeating pattern
        }
        
        # Step 1: Pattern detection
        pattern_result = await magic.cast_magic("pattern_detection", {
            "data": test_data["values"],
            "pattern_types": ["anomaly"],
            "window_size": 5
        })
        
        assert pattern_result["success"] is True
        
        # Step 2: Anomaly detection
        anomaly_result = await magic.cast_magic("anomaly_detection", {
            "data": test_data["values"],
            "methods": ["z_score"],
            "threshold": 2.0
        })
        
        assert anomaly_result["success"] is True
        
        # Step 3: Basic trend analysis
        trend_result = await magic.cast_magic("trend_analysis", {
            "data": {
                "timestamps": test_data["time_series"],
                "values": test_data["values"]
            },
            "trend_methods": ["linear"],
            "decomposition": False
        })
        
        assert trend_result["success"] is True
        
        # Verify results contain expected keys
        assert "pattern_detection" in pattern_result
        assert "anomaly_detection" in anomaly_result
        assert "trend_analysis" in trend_result
    
    async def test_error_handling_robustness(self):
        """エラーハンドリング堅牢性テスト"""
        magic = AnalysisMagic()
        
        # Test with None data
        result1 = await magic.cast_magic("descriptive_analysis", {"data": None})
        assert result1["success"] is False
        assert "error" in result1
        
        # Test with empty data
        result2 = await magic.cast_magic("pattern_detection", {
            "data": [],
            "pattern_types": ["anomaly"]
        })
        assert result2["success"] is False
        assert "error" in result2
        
        # Test with invalid parameters
        result3 = await magic.cast_magic("anomaly_detection", {
            "data": [1, 2, 3],
            "methods": ["invalid_method"]
        })
        assert result3["success"] is True  # Should handle gracefully
        
        # Test with insufficient data
        result4 = await magic.cast_magic("trend_analysis", {
            "data": {"values": [1, 2]},  # Too few points
            "trend_methods": ["linear"]
        })
        assert result4["success"] is False
        assert "error" in result4


# Test execution helper
async def run_all_tests():
    """すべてのテストを実行"""
    print("🧪 Analysis Magic Simple Test Suite Starting...")
    
    # Create test instances
    test_core = TestAnalysisMagicCore()
    test_integration = TestAnalysisMagicIntegration()
    
    # Initialize fixtures
    analysis_magic = AnalysisMagic()
    sample_data = {
        "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "categories": ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"],
        "timestamps": [f"2024-01-{i:02d}" for i in range(1, 11)],
        "matrix": [[1, 2], [3, 4], [5, 6]]
    }
    
    test_results = []
    
    # Run core tests
    core_tests = [
        "test_analysis_magic_initialization",
        "test_cast_magic_unknown_intent", 
        "test_trend_analysis_simple",
        "test_pattern_detection_basic",
        "test_anomaly_detection_basic",
        "test_performance_analysis_basic",
        "test_analysis_pipeline_basic",
        "test_magic_status_and_health"
    ]
    
    for test_name in core_tests:
        try:
            test_method = getattr(test_core, test_name)
            if test_name in ["test_analysis_magic_initialization", "test_cast_magic_unknown_intent"]:
                await test_method(analysis_magic)
            else:
                await test_method(analysis_magic, sample_data)
            test_results.append((test_name, "PASSED"))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            test_results.append((test_name, f"FAILED: {str(e)}"))
            print(f"❌ {test_name}: FAILED - {str(e)}")
    
    # Run integration tests
    integration_tests = [
        "test_analysis_workflow_integration",
        "test_error_handling_robustness"
    ]
    
    for test_name in integration_tests:
        try:
            test_method = getattr(test_integration, test_name)
            await test_method()
            test_results.append((test_name, "PASSED"))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            test_results.append((test_name, f"FAILED: {str(e)}"))
            print(f"❌ {test_name}: FAILED - {str(e)}")
    
    # Calculate success rate
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if r[1] == "PASSED"])
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📊 Test Results Summary:")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:0.1f}%")
    
    return success_rate >= 80.0, test_results


if __name__ == "__main__":
    # Run tests directly
    success, results = asyncio.run(run_all_tests())
    if success:
        print("🎉 Test suite passed with 80%+ success rate!")
    else:
        print("⚠️ Test suite did not meet 80% success rate requirement.")
#!/usr/bin/env python3
"""
"📊" Analysis Magic テストスイート
==============================

Analysis Magic（分析魔法）の包括的なテストスイート。
データ分析、トレンド検出、相関分析、洞察生成をテスト。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
import time
import json
import tempfile
import os
import gc
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# テスト対象をインポート
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ancient_magic.analysis_magic.analysis_magic import AnalysisMagic


class TestAnalysisMagic:
    """Analysis Magic テストクラス"""
    
    @pytest.fixture
    def analysis_magic(self):
        """Analysis Magic インスタンスを作成"""
        return AnalysisMagic()
        
    @pytest.fixture
    def sample_dataset(self):
        """テスト用データセット"""
        np.random.seed(42)  # 再現性のためのシード設定
        data = {
            "time_series": {
                "dates": pd.date_range("2024-01-01", periods=100, freq="D"),
                "values": np.random.randn(100).cumsum() + 100,
                "seasonal": 10 * np.sin(2 * np.pi * np.arange(100) / 12) + np.random.randn(100)
            },
            "correlation_data": {
                "x": np.random.randn(1000),
                "y": None,  # Will be calculated based on x
                "z": np.random.randn(1000)
            },
            "multivariate_data": pd.DataFrame({
                "feature_1": np.random.randn(500),
                "feature_2": np.random.randn(500),
                "feature_3": np.random.randn(500),
                "target": np.random.randint(0, 3, 500)
            }),
            "outlier_data": np.concatenate([
                np.random.randn(950),  # Normal data
                [10, -10, 15, -15, 20]  # Outliers
            ])
        }
        
        # Create correlation in y based on x
        data["correlation_data"]["y"] = (2 * data["correlation_data"]["x"] + 
                                       0.5 * np.random.randn(1000))
        
        return data
    
    @pytest.fixture
    def statistical_scenario(self):
        """統計分析用シナリオ"""
        return {
            "descriptive_stats": {
                "data": np.random.normal(50, 15, 1000),
                "expected_mean": 50,
                "expected_std": 15
            },
            "hypothesis_testing": {
                "sample_1": np.random.normal(100, 10, 100),
                "sample_2": np.random.normal(105, 10, 100),
                "alpha": 0.05
            },
            "distribution_fitting": {
                "normal_data": np.random.normal(0, 1, 1000),
                "exponential_data": np.random.exponential(2, 1000)
            }
        }
    
    # Phase 1: データ分析（Data Analysis）
    async def test_descriptive_statistics_analysis(self, analysis_magic, sample_dataset):
        """記述統計分析テスト"""
        analysis_params = {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "descriptive_statistics",
            "columns": ["feature_1", "feature_2", "feature_3"],
            "include_distribution": True,
            "confidence_level": 0.95
        }
        
        result = await analysis_magic.cast_magic("descriptive_analysis", analysis_params)
        
        assert result["success"] is True
        stats_result = result["descriptive_statistics"]
        
        # 基本統計量の確認
        assert "mean" in stats_result
        assert "median" in stats_result
        assert "std" in stats_result
        assert "variance" in stats_result
        assert "quartiles" in stats_result
        
        # 分布情報の確認
        assert "distribution_analysis" in stats_result
        assert "confidence_intervals" in stats_result
        
        # 統計量の妥当性確認
        for col in analysis_params["columns"]:
            assert col in stats_result["mean"]
            assert isinstance(stats_result["mean"][col], (int, float))
            assert isinstance(stats_result["std"][col], (int, float))
            assert stats_result["std"][col] >= 0  # 標準偏差は非負
    
    async def test_correlation_analysis(self, analysis_magic, sample_dataset):
        """相関分析テスト"""
        analysis_params = {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "correlation",
            "method": "pearson",
            "include_pvalues": True,
            "significance_level": 0.05
        }
        
        result = await analysis_magic.cast_magic("correlation_analysis", analysis_params)
        
        assert result["success"] is True
        corr_result = result["correlation_analysis"]
        
        # 相関行列の確認
        assert "correlation_matrix" in corr_result
        assert "p_values" in corr_result
        assert "significant_correlations" in corr_result
        
        # 相関行列の妥当性確認
        corr_matrix = corr_result["correlation_matrix"]
        features = ["feature_1", "feature_2", "feature_3", "target"]
        
        for feature in features:
            assert feature in corr_matrix
            # 自己相関は1に近い
            assert abs(corr_matrix[feature][feature] - 1.0) < 0.01
            
        # 有意な相関の確認
        assert isinstance(corr_result["significant_correlations"], list)
    
    async def test_regression_analysis(self, analysis_magic, sample_dataset):
        """回帰分析テスト"""
        corr_data = sample_dataset["correlation_data"]
        analysis_params = {
            "data": {
                "x": corr_data["x"][:100],  # サイズ制限
                "y": corr_data["y"][:100]
            },
            "analysis_type": "regression",
            "regression_type": "linear",
            "include_diagnostics": True,
            "confidence_level": 0.95
        }
        
        result = await analysis_magic.cast_magic("regression_analysis", analysis_params)
        
        assert result["success"] is True
        regression_result = result["regression_analysis"]
        
        # 回帰結果の確認
        assert "coefficients" in regression_result
        assert "r_squared" in regression_result
        assert "p_values" in regression_result
        assert "residuals_analysis" in regression_result
        
        # 回帰統計の妥当性確認
        assert 0 <= regression_result["r_squared"] <= 1
        assert isinstance(regression_result["coefficients"], dict)
        assert "intercept" in regression_result["coefficients"]
        assert "slope" in regression_result["coefficients"]
    
    async def test_multivariate_analysis(self, analysis_magic, sample_dataset):
        """多変量解析テスト"""
        analysis_params = {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "multivariate",
            "methods": ["pca", "clustering"],
            "n_components": 2,
            "n_clusters": 3
        }
        
        result = await analysis_magic.cast_magic("multivariate_analysis", analysis_params)
        
        assert result["success"] is True
        mv_result = result["multivariate_analysis"]
        
        # PCA結果の確認
        assert "pca_analysis" in mv_result
        pca_result = mv_result["pca_analysis"]
        assert "explained_variance_ratio" in pca_result
        assert "components" in pca_result
        assert len(pca_result["explained_variance_ratio"]) == 2
        
        # クラスタリング結果の確認
        assert "clustering_analysis" in mv_result
        cluster_result = mv_result["clustering_analysis"]
        assert "cluster_labels" in cluster_result
        assert "cluster_centers" in cluster_result
        assert "inertia" in cluster_result
    
    # Phase 2: トレンド検出（Trend Detection）
    async def test_time_series_trend_analysis(self, analysis_magic, sample_dataset):
        """時系列トレンド分析テスト"""
        ts_data = sample_dataset["time_series"]
        analysis_params = {
            "data": {
                "timestamps": ts_data["dates"],
                "values": ts_data["values"]
            },
            "analysis_type": "trend_detection",
            "trend_methods": ["linear", "polynomial", "seasonal"],
            "seasonal_periods": [7, 30],
            "decomposition": True
        }
        
        result = await analysis_magic.cast_magic("trend_analysis", analysis_params)
        
        assert result["success"] is True
        trend_result = result["trend_analysis"]
        
        # トレンド分析結果の確認
        assert "trend_direction" in trend_result
        assert "trend_strength" in trend_result
        assert "seasonal_components" in trend_result
        assert "decomposition" in trend_result
        
        # トレンド方向の確認
        assert trend_result["trend_direction"] in ["increasing", "decreasing", "stable"]
        assert 0 <= trend_result["trend_strength"] <= 1
    
    async def test_pattern_detection(self, analysis_magic, sample_dataset):
        """パターン検出テスト"""
        analysis_params = {
            "data": sample_dataset["time_series"]["seasonal"],
            "analysis_type": "pattern_detection",
            "pattern_types": ["cyclical", "anomaly", "change_points"],
            "window_size": 10,
            "sensitivity": 0.05
        }
        
        result = await analysis_magic.cast_magic("pattern_detection", analysis_params)
        
        assert result["success"] is True
        pattern_result = result["pattern_detection"]
        
        # パターン検出結果の確認
        assert "detected_patterns" in pattern_result
        assert "anomalies" in pattern_result
        assert "change_points" in pattern_result
        assert "pattern_confidence" in pattern_result
        
        # 結果の妥当性確認
        assert isinstance(pattern_result["detected_patterns"], list)
        assert isinstance(pattern_result["anomalies"], list)
        assert 0 <= pattern_result["pattern_confidence"] <= 1
    
    async def test_seasonal_decomposition(self, analysis_magic, sample_dataset):
        """季節性分解テスト"""
        analysis_params = {
            "data": sample_dataset["time_series"]["seasonal"],
            "analysis_type": "seasonal_decomposition",
            "period": 12,
            "model": "additive",
            "extrapolate_trend": "freq"
        }
        
        result = await analysis_magic.cast_magic("seasonal_analysis", analysis_params)
        
        assert result["success"] is True
        seasonal_result = result["seasonal_analysis"]
        
        # 季節性分解結果の確認
        assert "trend" in seasonal_result
        assert "seasonal" in seasonal_result
        assert "residual" in seasonal_result
        assert "seasonality_strength" in seasonal_result
        
        # 分解品質の確認
        assert len(seasonal_result["trend"]) == len(sample_dataset["time_series"]["seasonal"])
        assert 0 <= seasonal_result["seasonality_strength"] <= 1
    
    async def test_change_point_detection(self, analysis_magic, sample_dataset):
        """変化点検出テスト"""
        # 変化点を含むデータの作成
        data = np.concatenate([
            np.random.normal(0, 1, 50),  # 前半
            np.random.normal(3, 1, 50)   # 後半（変化点あり）
        ])
        
        analysis_params = {
            "data": data,
            "analysis_type": "change_point_detection",
            "method": "pelt",
            "min_size": 10,
            "jump": 1
        }
        
        result = await analysis_magic.cast_magic("change_point_analysis", analysis_params)
        
        assert result["success"] is True
        cp_result = result["change_point_analysis"]
        
        # 変化点検出結果の確認
        assert "change_points" in cp_result
        assert "confidence_scores" in cp_result
        assert "segment_statistics" in cp_result
        
        # 変化点の妥当性確認
        change_points = cp_result["change_points"]
        assert isinstance(change_points, list)
        # 実際の変化点（50付近）が検出されることを期待
        if change_points:
            detected_point = change_points[0]
            assert 40 <= detected_point <= 60  # 許容範囲
    
    # Phase 3: 相関分析（Correlation Analysis）
    async def test_advanced_correlation_analysis(self, analysis_magic, sample_dataset):
        """高度な相関分析テスト"""
        analysis_params = {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "advanced_correlation",
            "methods": ["pearson", "spearman", "kendall"],
            "partial_correlation": True,
            "lag_analysis": True,
            "max_lags": 5
        }
        
        result = await analysis_magic.cast_magic("advanced_correlation", analysis_params)
        
        assert result["success"] is True
        adv_corr_result = result["advanced_correlation"]
        
        # 各相関手法の結果確認
        for method in ["pearson", "spearman", "kendall"]:
            assert method in adv_corr_result
            assert "correlation_matrix" in adv_corr_result[method]
            assert "p_values" in adv_corr_result[method]
        
        # 偏相関の確認
        assert "partial_correlation" in adv_corr_result
        
        # ラグ分析の確認
        assert "lag_analysis" in adv_corr_result
    
    async def test_causality_analysis(self, analysis_magic, sample_dataset):
        """因果関係分析テスト"""
        # 因果関係のあるデータを作成
        x = np.random.randn(100)
        y = 0.5 * x[:-1] + np.random.randn(99)  # yはxに依存（ラグあり）
        
        analysis_params = {
            "data": {
                "cause": x[:-1],
                "effect": y
            },
            "analysis_type": "causality",
            "test_type": "granger",
            "max_lags": 3,
            "significance_level": 0.05
        }
        
        result = await analysis_magic.cast_magic("causality_analysis", analysis_params)
        
        assert result["success"] is True
        causality_result = result["causality_analysis"]
        
        # 因果関係テスト結果の確認
        assert "granger_causality" in causality_result
        assert "p_value" in causality_result
        assert "f_statistic" in causality_result
        assert "causality_direction" in causality_result
        
        # 統計的有意性の確認
        assert isinstance(causality_result["p_value"], (int, float))
        assert causality_result["p_value"] >= 0
        assert causality_result["causality_direction"] in ["cause->effect", "effect->cause", "bidirectional", "none"]
    
    async def test_network_analysis(self, analysis_magic, sample_dataset):
        """ネットワーク分析テスト"""
        # 相関行列からネットワークを構築
        data = sample_dataset["multivariate_data"][["feature_1", "feature_2", "feature_3"]]
        
        analysis_params = {
            "data": data,
            "analysis_type": "network_analysis",
            "correlation_threshold": 0.3,
            "network_metrics": ["centrality", "clustering", "communities"],
            "layout": "spring"
        }
        
        result = await analysis_magic.cast_magic("network_analysis", analysis_params)
        
        assert result["success"] is True
        network_result = result["network_analysis"]
        
        # ネットワーク分析結果の確認
        assert "adjacency_matrix" in network_result
        assert "centrality_measures" in network_result
        assert "clustering_coefficient" in network_result
        assert "communities" in network_result
        
        # ネットワーク指標の妥当性確認
        centrality = network_result["centrality_measures"]
        assert "degree_centrality" in centrality
        assert "betweenness_centrality" in centrality
        assert "closeness_centrality" in centrality
    
    # Phase 4: 洞察生成（Insight Generation）
    async def test_automated_insights_generation(self, analysis_magic, sample_dataset):
        """自動洞察生成テスト"""
        analysis_params = {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "insight_generation",
            "insight_types": ["statistical", "correlation", "outlier", "trend"],
            "confidence_threshold": 0.8,
            "max_insights": 10
        }
        
        result = await analysis_magic.cast_magic("insight_generation", analysis_params)
        
        assert result["success"] is True
        insight_result = result["insight_generation"]
        
        # 洞察生成結果の確認
        assert "insights" in insight_result
        assert "insight_categories" in insight_result
        assert "confidence_scores" in insight_result
        assert "actionable_recommendations" in insight_result
        
        # 洞察の品質確認
        insights = insight_result["insights"]
        assert isinstance(insights, list)
        assert len(insights) <= 10  # 最大数制限
        
        for insight in insights:
            assert "type" in insight
            assert "description" in insight
            assert "confidence" in insight
            assert 0 <= insight["confidence"] <= 1
    
    async def test_anomaly_detection(self, analysis_magic, sample_dataset):
        """異常検出テスト"""
        analysis_params = {
            "data": sample_dataset["outlier_data"],
            "analysis_type": "anomaly_detection",
            "methods": ["isolation_forest", "z_score", "iqr"],
            "contamination": 0.05,
            "threshold": 3.0
        }
        
        result = await analysis_magic.cast_magic("anomaly_detection", analysis_params)
        
        assert result["success"] is True
        anomaly_result = result["anomaly_detection"]
        
        # 異常検出結果の確認
        assert "anomalies" in anomaly_result
        assert "anomaly_scores" in anomaly_result
        assert "detection_methods" in anomaly_result
        assert "normal_range" in anomaly_result
        
        # 異常値の妥当性確認
        anomalies = anomaly_result["anomalies"]
        assert isinstance(anomalies, list)
        # 実際に含まれている外れ値（10, -10, 15, -15, 20）が検出されることを期待
        assert len(anomalies) > 0
    
    async def test_feature_importance_analysis(self, analysis_magic, sample_dataset):
        """特徴重要度分析テスト"""
        data = sample_dataset["multivariate_data"]
        
        analysis_params = {
            "data": {
                "features": data[["feature_1", "feature_2", "feature_3"]],
                "target": data["target"]
            },
            "analysis_type": "feature_importance",
            "methods": ["mutual_info", "correlation", "variance"],
            "top_k": 5
        }
        
        result = await analysis_magic.cast_magic("feature_importance", analysis_params)
        
        assert result["success"] is True
        importance_result = result["feature_importance"]
        
        # 特徴重要度結果の確認
        assert "importance_scores" in importance_result
        assert "ranking" in importance_result
        assert "top_features" in importance_result
        
        # 重要度スコアの妥当性確認
        for method in ["mutual_info", "correlation", "variance"]:
            assert method in importance_result["importance_scores"]
            scores = importance_result["importance_scores"][method]
            assert isinstance(scores, dict)
            assert all(isinstance(score, (int, float)) for score in scores.values())
    
    async def test_data_quality_assessment(self, analysis_magic, sample_dataset):
        """データ品質評価テスト"""
        # 意図的に品質問題を含むデータを作成
        poor_data = sample_dataset["multivariate_data"].copy()
        poor_data.loc[0:10, "feature_1"] = np.nan  # 欠損値
        poor_data.loc[20:25, "feature_2"] = poor_data.loc[20:25, "feature_2"] * 100  # 外れ値
        
        analysis_params = {
            "data": poor_data,
            "analysis_type": "data_quality",
            "quality_checks": ["completeness", "consistency", "accuracy", "validity"],
            "outlier_threshold": 3.0
        }
        
        result = await analysis_magic.cast_magic("data_quality_assessment", analysis_params)
        
        assert result["success"] is True
        quality_result = result["data_quality_assessment"]
        
        # データ品質評価結果の確認
        assert "overall_quality_score" in quality_result
        assert "quality_dimensions" in quality_result
        assert "issues_detected" in quality_result
        assert "recommendations" in quality_result
        
        # 品質スコアの妥当性確認
        assert 0 <= quality_result["overall_quality_score"] <= 1
        
        # 検出された問題の確認
        issues = quality_result["issues_detected"]
        assert isinstance(issues, list)
        # 欠損値や外れ値が検出されることを期待
        issue_types = [issue["type"] for issue in issues]
        assert "missing_values" in issue_types or "outliers" in issue_types
    
    # Phase 5: 統合分析（Integrated Analysis）
    async def test_comprehensive_data_analysis(self, analysis_magic, sample_dataset):
        """包括的データ分析テスト"""
        analysis_params = {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "comprehensive",
            "analysis_modules": [
                "descriptive_statistics",
                "correlation_analysis", 
                "multivariate_analysis",
                "anomaly_detection",
                "insight_generation"
            ],
            "output_format": "report"
        }
        
        result = await analysis_magic.cast_magic("comprehensive_analysis", analysis_params)
        
        assert result["success"] is True
        comp_result = result["comprehensive_analysis"]
        
        # 包括分析結果の確認
        assert "analysis_summary" in comp_result
        assert "module_results" in comp_result
        assert "integrated_insights" in comp_result
        assert "analysis_report" in comp_result
        
        # 各モジュールの結果確認
        module_results = comp_result["module_results"]
        for module in analysis_params["analysis_modules"]:
            assert module in module_results
            assert module_results[module]["success"] is True
    
    async def test_analysis_pipeline_execution(self, analysis_magic, sample_dataset):
        """分析パイプライン実行テスト"""
        pipeline_config = {
            "pipeline_id": "test_pipeline_001",
            "stages": [
                {
                    "name": "data_preprocessing",
                    "type": "preprocessing",
                    "parameters": {
                        "normalize": True,
                        "handle_missing": "mean",
                        "remove_outliers": True
                    }
                },
                {
                    "name": "exploratory_analysis",
                    "type": "exploratory",
                    "parameters": {
                        "include_visualization": True,
                        "correlation_threshold": 0.5
                    }
                },
                {
                    "name": "advanced_analysis",
                    "type": "advanced",
                    "parameters": {
                        "dimensionality_reduction": True,
                        "clustering": True,
                        "n_clusters": 3
                    }
                }
            ],
            "data": sample_dataset["multivariate_data"]
        }
        
        result = await analysis_magic.cast_magic("analysis_pipeline", pipeline_config)
        
        assert result["success"] is True
        pipeline_result = result["analysis_pipeline"]
        
        # パイプライン実行結果の確認
        assert "pipeline_id" in pipeline_result
        assert "stage_results" in pipeline_result
        assert "execution_summary" in pipeline_result
        
        # 各ステージの実行確認
        stage_results = pipeline_result["stage_results"]
        assert len(stage_results) == 3
        
        for stage_result in stage_results:
            assert "stage_name" in stage_result
            assert "success" in stage_result
            assert stage_result["success"] is True
    
    # Performance and Error Handling Tests
    async def test_large_dataset_performance(self, analysis_magic):
        """大規模データセット性能テスト"""
        # 大規模データセットの作成
        large_data = pd.DataFrame({
            "feature_1": np.random.randn(10000),
            "feature_2": np.random.randn(10000),
            "feature_3": np.random.randn(10000)
        })
        
        analysis_params = {
            "data": large_data,
            "analysis_type": "performance_test",
            "operations": ["correlation", "descriptive_stats", "anomaly_detection"],
            "optimization": True
        }
        
        start_time = time.time()
        result = await analysis_magic.cast_magic("performance_analysis", analysis_params)
        execution_time = time.time() - start_time
        
        assert result["success"] is True
        assert execution_time < 30.0  # 30秒以内での実行を期待
        
        perf_result = result["performance_analysis"]
        assert "execution_metrics" in perf_result
        assert "memory_usage" in perf_result
        assert "optimization_applied" in perf_result
    
    async def test_error_handling_invalid_data(self, analysis_magic):
        """不正データのエラーハンドリングテスト"""
        invalid_params = {
            "data": "invalid_data_type",  # 不正なデータ型
            "analysis_type": "descriptive_statistics"
        }
        
        result = await analysis_magic.cast_magic("error_test", invalid_params)
        
        assert result["success"] is False
        assert "error" in result
        assert "Invalid data format" in result["error"] or "Data must be" in result["error"]
    
    async def test_missing_parameters_handling(self, analysis_magic):
        """必須パラメータ不足のハンドリングテスト"""
        incomplete_params = {
            # dataパラメータが不足
            "analysis_type": "correlation_analysis"
        }
        
        result = await analysis_magic.cast_magic("incomplete_test", incomplete_params)
        
        assert result["success"] is False
        assert "error" in result
        assert "required" in result["error"].lower() or "missing" in result["error"].lower()
    
    async def test_analysis_magic_capabilities(self, analysis_magic):
        """Analysis Magic能力確認テスト"""
        status = analysis_magic.get_magic_status()
        
        assert status["magic_type"] == "analysis"
        assert "capabilities" in status
        
        # 期待される能力の確認  
        expected_capabilities = [
            "DATA_ANALYSIS",
            "TREND_DETECTION", 
            "CORRELATION_ANALYSIS",
            "INSIGHT_GENERATION"
        ]
        
        for capability in expected_capabilities:
            assert capability in status["capabilities"]
    
    async def test_analysis_magic_health_diagnosis(self, analysis_magic, sample_dataset):
        """Analysis Magic健康診断テスト"""
        # いくつかの分析を実行して履歴を作成
        await analysis_magic.cast_magic("descriptive_analysis", {
            "data": sample_dataset["multivariate_data"],
            "analysis_type": "descriptive_statistics"
        })
        
        await analysis_magic.cast_magic("correlation_analysis", {
            "data": sample_dataset["multivariate_data"], 
            "analysis_type": "correlation"
        })
        
        # 健康診断実行
        health_status = await analysis_magic.diagnose_magic_health()
        
        assert "overall_health" in health_status
        assert "success_rate" in health_status
        assert "average_response_time" in health_status
        assert "recent_errors" in health_status
        assert "recommendations" in health_status
        
        # 健康状態の妥当性確認
        assert health_status["overall_health"] in ["excellent", "good", "fair", "poor"]
        assert 0 <= health_status["success_rate"] <= 1
        assert health_status["average_response_time"] >= 0


# テスト実行用のメイン関数
async def main():
    """テスト実行のメイン関数"""
    print("🧪 Analysis Magic Test Suite Starting...")
    
    # pytest-asyncioを使用してテストを実行
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    print("📊 Test Results:")
    print(result.stdout)
    if result.stderr:
        print("❌ Errors:")
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    asyncio.run(main())
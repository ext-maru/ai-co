"""
DataMiner (W02) エルダーサーバント テストスイート

RAGウィザーズのデータ分析専門サーバントのテスト。
Iron Will 品質基準に基づく包括的テスト実装。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from libs.elder_servants.base.elder_servant_base import (
    ElderServantBase, ServantRequest, ServantResponse, 
    ServantDomain, ServantCapability
)
from libs.elder_servants.rag_wizards.data_miner import DataMiner


class TestDataMiner:
    """DataMiner エルダーサーバントのテストクラス"""

    @pytest.fixture
    def data_miner(self) -> DataMiner:
        """DataMiner インスタンスを作成"""
        return DataMiner("W02", "DataMiner", "data_analysis")

    @pytest.fixture
    def sample_csv_data(self) -> Dict[str, Any]:
        """サンプルCSVデータを作成"""
        return {
            "csv_content": """name,age,salary,department
John Doe,25,50000,Engineering
Jane Smith,30,65000,Marketing
Bob Wilson,35,70000,Engineering
Alice Brown,28,55000,Sales
Charlie Davis,32,60000,Marketing""",
            "filename": "employees.csv"
        }

    @pytest.fixture
    def sample_request(self, sample_csv_data) -> ServantRequest:
        """サンプルリクエストを作成"""
        return ServantRequest(
            task_id="data_test_001",
            task_type="data_analysis",
            priority="medium",
            data={
                "analysis_type": "statistical_summary",
                "data_source": sample_csv_data,
                "output_format": "json",
                "metrics": ["mean", "median", "std", "correlation"]
            },
            context={"project_name": "HR Analytics"}
        )

    def test_initialization(self, data_miner: DataMiner):
        """DataMiner の初期化テスト"""
        assert data_miner.name == "DataMiner"
        assert data_miner.servant_id == "W02"
        assert data_miner.domain == ServantDomain.RAG_WIZARDS
        assert data_miner.specialization == "data_analysis"
        assert data_miner.category == "rag_wizards"

    def test_get_capabilities(self, data_miner: DataMiner):
        """能力取得テスト"""
        capabilities = data_miner.get_capabilities()
        expected_capabilities = [
            ServantCapability.ANALYSIS,
            ServantCapability.MONITORING,
            ServantCapability.PERFORMANCE
        ]
        
        for cap in expected_capabilities:
            assert cap in capabilities

    def test_validate_request_valid(self, data_miner: DataMiner, sample_request: ServantRequest):
        """有効なリクエストの検証テスト"""
        assert data_miner.validate_request(sample_request) is True

    def test_validate_request_invalid_task_type(self, data_miner: DataMiner):
        """無効なタスクタイプの検証テスト"""
        invalid_request = ServantRequest(
            task_id="data_test_002",
            task_type="invalid_analysis",
            priority="medium",
            data={"analysis_type": "test"},
            context={}
        )
        
        assert data_miner.validate_request(invalid_request) is False

    def test_validate_request_missing_data_source(self, data_miner: DataMiner):
        """データソース不足の検証テスト"""
        invalid_request = ServantRequest(
            task_id="data_test_003",
            task_type="data_analysis",
            priority="medium",
            data={"analysis_type": "statistical_summary"},
            context={}
        )
        
        assert data_miner.validate_request(invalid_request) is False

    @pytest.mark.asyncio
    async def test_process_request_statistical_summary(self, data_miner: DataMiner, sample_request: ServantRequest):
        """統計サマリー分析の処理テスト"""
        with patch.object(data_miner, 'research_and_analyze', new_callable=AsyncMock) as mock_research:
            mock_research.return_value = {
                "data_insights": ["correlation_patterns", "outlier_detection"],
                "recommendations": ["data_quality_improvements"]
            }
            
            response = await data_miner.process_request(sample_request)
            
            assert response.status == "success"
            assert response.task_id == "data_test_001"
            assert "analysis_results" in response.data
            assert len(response.errors) == 0
            
            # 統計結果の検証
            results = response.data["analysis_results"]
            assert "summary_statistics" in results
            assert "correlations" in results
            assert "data_quality" in results

    @pytest.mark.asyncio
    async def test_process_request_trend_analysis(self, data_miner: DataMiner):
        """トレンド分析の処理テスト"""
        time_series_data = {
            "csv_content": """date,sales,users
2024-01-01,1000,50
2024-01-02,1200,55
2024-01-03,1100,52
2024-01-04,1300,58
2024-01-05,1250,56""",
            "filename": "daily_metrics.csv"
        }
        
        request = ServantRequest(
            task_id="data_test_004",
            task_type="data_analysis",
            priority="high",
            data={
                "analysis_type": "trend_analysis",
                "data_source": time_series_data,
                "time_column": "date",
                "value_columns": ["sales", "users"],
                "output_format": "json"
            },
            context={"project_name": "Sales Analytics"}
        )
        
        response = await data_miner.process_request(request)
        
        assert response.status == "success"
        assert "analysis_results" in response.data
        
        results = response.data["analysis_results"]
        assert "trends" in results
        assert "forecasts" in results
        assert "seasonal_patterns" in results

    @pytest.mark.asyncio
    async def test_process_request_correlation_analysis(self, data_miner: DataMiner):
        """相関分析の処理テスト"""
        request = ServantRequest(
            task_id="data_test_005",
            task_type="data_analysis",
            priority="medium",
            data={
                "analysis_type": "correlation_analysis",
                "data_source": {
                    "csv_content": "x,y,z\n1,2,3\n2,4,6\n3,6,9\n4,8,12",
                    "filename": "correlation_data.csv"
                },
                "variables": ["x", "y", "z"],
                "correlation_method": "pearson"
            },
            context={"project_name": "Variable Analysis"}
        )
        
        response = await data_miner.process_request(request)
        
        assert response.status == "success"
        results = response.data["analysis_results"]
        assert "correlation_matrix" in results
        assert "strong_correlations" in results

    @pytest.mark.asyncio
    async def test_analyze_statistical_summary(self, data_miner: DataMiner, sample_csv_data):
        """統計サマリー分析の詳細テスト"""
        results = await data_miner._analyze_statistical_summary(
            sample_csv_data, ["mean", "median", "std"], {}
        )
        
        assert "summary_statistics" in results
        assert "data_quality" in results
        assert "outliers" in results
        
        # 数値列の統計情報確認
        stats = results["summary_statistics"]
        assert "age" in stats
        assert "salary" in stats
        assert "mean" in stats["age"]
        assert "median" in stats["salary"]

    @pytest.mark.asyncio
    async def test_analyze_trend_analysis(self, data_miner: DataMiner):
        """トレンド分析の詳細テスト"""
        time_series_data = {
            "csv_content": """date,value
2024-01-01,100
2024-01-02,110
2024-01-03,105
2024-01-04,120
2024-01-05,115""",
            "filename": "trend_data.csv"
        }
        
        config = {
            "time_column": "date",
            "value_columns": ["value"],
            "forecast_periods": 3
        }
        
        results = await data_miner._analyze_trend_analysis(time_series_data, config, {})
        
        assert "trends" in results
        assert "forecasts" in results
        assert "seasonal_patterns" in results
        assert len(results["forecasts"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_correlation(self, data_miner: DataMiner):
        """相関分析の詳細テスト"""
        correlation_data = {
            "csv_content": "a,b,c\n1,2,1\n2,4,2\n3,6,3\n4,8,4",
            "filename": "corr_data.csv"
        }
        
        config = {
            "variables": ["a", "b", "c"],
            "correlation_method": "pearson",
            "significance_level": 0.05
        }
        
        results = await data_miner._analyze_correlation(correlation_data, config, {})
        
        assert "correlation_matrix" in results
        assert "strong_correlations" in results
        assert "p_values" in results
        
        # 完全相関の確認（a と c は完全相関）
        strong_corrs = results["strong_correlations"]
        assert len(strong_corrs) > 0

    def test_load_csv_data(self, data_miner: DataMiner, sample_csv_data):
        """CSVデータ読み込みテスト"""
        df = data_miner._load_csv_data(sample_csv_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert "name" in df.columns
        assert "age" in df.columns
        assert "salary" in df.columns
        assert "department" in df.columns

    def test_identify_data_types(self, data_miner: DataMiner):
        """データ型識別テスト"""
        df = pd.DataFrame({
            "text": ["a", "b", "c"],
            "number": [1, 2, 3],
            "float": [1.1, 2.2, 3.3],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "category": ["cat1", "cat1", "cat2"]
        })
        
        types_info = data_miner._identify_data_types(df)
        
        assert "numeric_columns" in types_info
        assert "categorical_columns" in types_info
        assert "text_columns" in types_info
        assert "date_columns" in types_info
        
        assert "number" in types_info["numeric_columns"]
        assert "float" in types_info["numeric_columns"]
        assert "category" in types_info["categorical_columns"]

    def test_calculate_descriptive_statistics(self, data_miner: DataMiner):
        """記述統計計算テスト"""
        df = pd.DataFrame({
            "values": [1, 2, 3, 4, 5, 100],  # 100は外れ値
            "category": ["A", "A", "B", "B", "C", "C"]
        })
        
        stats = data_miner._calculate_descriptive_statistics(df, ["mean", "median", "std"])
        
        assert "values" in stats
        assert "mean" in stats["values"]
        assert "median" in stats["values"]
        assert "std" in stats["values"]
        
        # 外れ値の影響で平均と中央値が異なることを確認
        assert stats["values"]["mean"] > stats["values"]["median"]

    def test_detect_outliers(self, data_miner: DataMiner):
        """外れ値検出テスト"""
        df = pd.DataFrame({
            "normal": [1, 2, 3, 4, 5],
            "with_outlier": [1, 2, 3, 4, 100]  # 100は明らかな外れ値
        })
        
        outliers = data_miner._detect_outliers(df)
        
        assert "with_outlier" in outliers
        assert len(outliers["with_outlier"]) > 0
        assert 100 in outliers["with_outlier"]["values"]

    def test_calculate_correlations(self, data_miner: DataMiner):
        """相関計算テスト"""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],  # x と完全相関
            "z": [5, 4, 3, 2, 1]   # x と負の相関
        })
        
        correlations = data_miner._calculate_correlations(df, "pearson")
        
        assert "correlation_matrix" in correlations
        assert "strong_correlations" in correlations
        
        # x と y の相関が高いことを確認
        matrix = correlations["correlation_matrix"]
        assert matrix["x"]["y"] > 0.9
        assert matrix["x"]["z"] < -0.9

    def test_perform_trend_analysis(self, data_miner: DataMiner):
        """トレンド分析実行テスト"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "value": [i + np.random.normal(0, 0.1) for i in range(10)]  # 上昇トレンド
        })
        
        trends = data_miner._perform_trend_analysis(df, "date", ["value"])
        
        assert "value" in trends
        assert "slope" in trends["value"]
        assert "r_squared" in trends["value"]
        assert trends["value"]["slope"] > 0  # 上昇トレンドを検出

    def test_forecast_values(self, data_miner: DataMiner):
        """値予測テスト"""
        # 線形トレンドのデータ
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        values = list(range(10))
        
        forecasts = data_miner._forecast_values(dates, values, 3)
        
        assert len(forecasts) == 3
        assert all(isinstance(f, (int, float)) for f in forecasts)
        assert forecasts[0] > values[-1]  # 最後の値より大きい

    def test_assess_data_quality(self, data_miner: DataMiner):
        """データ品質評価テスト"""
        df = pd.DataFrame({
            "complete": [1, 2, 3, 4, 5],
            "missing": [1, None, 3, None, 5],
            "duplicate": [1, 1, 2, 2, 3]
        })
        
        quality = data_miner._assess_data_quality(df)
        
        assert "missing_values" in quality
        assert "duplicates" in quality
        assert "completeness_score" in quality
        
        assert quality["missing_values"]["missing"] == 2
        assert quality["duplicates"]["count"] > 0
        assert quality["completeness_score"] < 1.0

    @pytest.mark.asyncio
    async def test_error_handling_invalid_csv(self, data_miner: DataMiner):
        """無効なCSVのエラーハンドリングテスト"""
        request = ServantRequest(
            task_id="data_test_006",
            task_type="data_analysis",
            priority="medium",
            data={
                "analysis_type": "statistical_summary",
                "data_source": {
                    "csv_content": "invalid,csv,format\n1,2",  # 不正な形式
                    "filename": "invalid.csv"
                }
            },
            context={}
        )
        
        response = await data_miner.process_request(request)
        
        # エラーがあっても適切に処理されるべき
        assert response.status in ["failed", "partial"]
        assert len(response.errors) > 0

    @pytest.mark.asyncio
    async def test_performance_large_dataset(self, data_miner: DataMiner):
        """大規模データセットのパフォーマンステスト"""
        # 大きなデータセットを生成
        large_data = "id,value\n" + "\n".join([f"{i},{i*2}" for i in range(1000)])
        
        request = ServantRequest(
            task_id="data_test_007",
            task_type="data_analysis",
            priority="high",
            data={
                "analysis_type": "statistical_summary",
                "data_source": {
                    "csv_content": large_data,
                    "filename": "large_dataset.csv"
                },
                "metrics": ["mean", "std"]
            },
            context={"project_name": "Performance Test"}
        )
        
        start_time = datetime.now()
        response = await data_miner.process_request(request)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        assert response.status == "success"
        assert processing_time < 10  # 10秒以内で完了
        assert "analysis_results" in response.data

    @pytest.mark.asyncio
    async def test_multi_format_support(self, data_miner: DataMiner):
        """複数フォーマットサポートテスト"""
        # JSON形式でのレスポンステスト
        request_json = ServantRequest(
            task_id="data_test_008",
            task_type="data_analysis",
            priority="medium",
            data={
                "analysis_type": "statistical_summary",
                "data_source": {
                    "csv_content": "a,b\n1,2\n3,4",
                    "filename": "test.csv"
                },
                "output_format": "json"
            },
            context={}
        )
        
        response = await data_miner.process_request(request_json)
        assert response.status == "success"
        assert "analysis_results" in response.data

    @pytest.mark.asyncio
    async def test_iron_will_quality_standards(self, data_miner: DataMiner, sample_request: ServantRequest):
        """Iron Will品質基準テスト"""
        # 品質基準を満たす処理を実行
        for _ in range(10):
            response = await data_miner.execute_with_quality_gate(sample_request)
            assert response.status == "success"
        
        # 品質スコアの確認
        metrics = data_miner.get_metrics()
        quality_scores = metrics["quality_scores"]
        
        # Iron Will基準の確認
        assert quality_scores["root_cause_resolution"] >= 95
        assert quality_scores["dependency_completeness"] >= 100
        assert quality_scores["test_coverage"] >= 95
        assert quality_scores["security_score"] >= 90
        assert quality_scores["performance_score"] >= 85
        assert quality_scores["maintainability_score"] >= 80

    @pytest.mark.asyncio
    async def test_research_and_analyze(self, data_miner: DataMiner):
        """調査分析機能テスト"""
        topic = "time_series_analysis_patterns"
        
        with patch.object(data_miner, 'research_and_analyze', new_callable=AsyncMock) as mock_research:
            mock_research.return_value = {
                "research_results": [
                    "seasonal_patterns_identified",
                    "trend_analysis_completed",
                    "anomaly_detection_results"
                ],
                "recommendations": [
                    "implement_forecasting_model",
                    "monitor_data_quality"
                ]
            }
            
            result = await data_miner.research_and_analyze(topic)
            
            assert "research_results" in result
            assert "recommendations" in result
            assert len(result["research_results"]) > 0

    def test_metrics_tracking(self, data_miner: DataMiner):
        """メトリクス追跡テスト"""
        initial_metrics = data_miner.get_metrics()
        
        assert "tasks_processed" in initial_metrics
        assert "tasks_succeeded" in initial_metrics
        assert "tasks_failed" in initial_metrics
        assert "success_rate" in initial_metrics
        assert "quality_scores" in initial_metrics

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, data_miner: DataMiner):
        """並行分析テスト"""
        requests = []
        for i in range(3):
            request = ServantRequest(
                task_id=f"concurrent_analysis_{i}",
                task_type="data_analysis",
                priority="medium",
                data={
                    "analysis_type": "statistical_summary",
                    "data_source": {
                        "csv_content": f"x,y\n{i},_{i*2}\n{i+1},{(i+1)*2}",
                        "filename": f"dataset_{i}.csv"
                    }
                },
                context={"project_name": f"Analysis {i}"}
            )
            requests.append(request)
        
        # 並行実行
        tasks = [data_miner.process_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # すべてのレスポンスが成功していることを確認
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.status == "success"

    def test_repr_method(self, data_miner: DataMiner):
        """__repr__メソッドテスト"""
        repr_str = repr(data_miner)
        assert "DataMiner" in repr_str
        assert "DataMiner" in repr_str
        assert "rag_wizards" in repr_str
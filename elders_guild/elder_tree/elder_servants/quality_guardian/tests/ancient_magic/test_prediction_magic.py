#!/usr/bin/env python3
"""
Test suite for Prediction Magic - The eighth Ancient Magic
Tests future prediction, risk assessment, capacity planning, and anomaly detection
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# Import the module to be tested
from elders_guild.ancient_magic.prediction_magic import (
    PredictionMagic,
    PredictionIntent,
    PredictionResult,
    FuturePredictor,
    RiskAssessor,
    CapacityPlanner,
    AnomalyDetector,
    PredictionError
)


class TestPredictionIntent:
    """Test the PredictionIntent enum and classification"""
    
    def test_intent_values(self):
        """Test that all prediction intents are defined"""
        assert PredictionIntent.FUTURE_FORECAST.value == "future_forecast"
        assert PredictionIntent.RISK_ASSESSMENT.value == "risk_assessment"
        assert PredictionIntent.CAPACITY_PLANNING.value == "capacity_planning"
        assert PredictionIntent.ANOMALY_DETECTION.value == "anomaly_detection"
        assert PredictionIntent.UNKNOWN.value == "unknown"
    
    def test_intent_from_string(self):
        """Test intent creation from string"""
        assert PredictionIntent.from_string("predict future") == PredictionIntent.FUTURE_FORECAST
        assert PredictionIntent.from_string("assess risk") == PredictionIntent.RISK_ASSESSMENT
        assert PredictionIntent.from_string("plan capacity") == PredictionIntent.CAPACITY_PLANNING
        assert PredictionIntent.from_string("detect anomaly") == PredictionIntent.ANOMALY_DETECTION
        assert PredictionIntent.from_string("random text") == PredictionIntent.UNKNOWN


class TestPredictionResult:
    """Test the PredictionResult dataclass"""
    
    def test_result_creation(self):
        """Test creating a prediction result"""
        result = PredictionResult(
            prediction_type="future_forecast",
            predictions={"values": [1, 2, 3]},
            confidence_intervals={"lower": [0.5, 1.5, 2.5], "upper": [1.5, 2.5, 3.5]},
            metrics={"rmse": 0.1, "mae": 0.08},
            metadata={"model": "ARIMA", "timestamp": "2024-01-01"}
        )
        
        assert result.prediction_type == "future_forecast"
        assert result.predictions["values"] == [1, 2, 3]
        assert result.confidence_intervals["lower"] == [0.5, 1.5, 2.5]
        assert result.metrics["rmse"] == 0.1
        assert result.metadata["model"] == "ARIMA"
    
    def test_result_to_dict(self):
        """Test converting result to dictionary"""
        result = PredictionResult(
            prediction_type="risk_assessment",
            predictions={"risk_score": 0.75},
            metrics={"accuracy": 0.92}
        )
        
        result_dict = result.to_dict()
        assert result_dict["prediction_type"] == "risk_assessment"
        assert result_dict["predictions"]["risk_score"] == 0.75
        assert result_dict["metrics"]["accuracy"] == 0.92
        assert "timestamp" in result_dict


class TestFuturePredictor:
    """Test the FuturePredictor component"""
    
    def test_predictor_initialization(self):
        """Test predictor initialization"""
        predictor = FuturePredictor()
        assert predictor is not None
        assert hasattr(predictor, 'models')
    
    def test_time_series_prediction(self):
        """Test time series forecasting"""
        predictor = FuturePredictor()
        
        # Create sample time series data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        values = np.sin(np.arange(100) * 0.1) + np.random.normal(0, 0.1, 100)
        data = pd.DataFrame({'date': dates, 'value': values})
        
        result = predictor.predict_time_series(
            data=data,
            horizon=10,
            method='auto'
        )
        
        assert 'predictions' in result
        assert 'confidence_intervals' in result
        assert len(result['predictions']) == 10
        assert 'model_used' in result
    
    @patch('statsmodels.tsa.arima.model.ARIMA')
    def test_arima_prediction(self, mock_arima):
        """Test ARIMA model prediction"""
        predictor = FuturePredictor()
        
        # Mock ARIMA model
        mock_model = Mock()
        mock_fit = Mock()
        mock_forecast = Mock(return_value=(np.array([1, 2, 3]), None, np.array([[0.5, 1.5], [1.5, 2.5], [2.5, 3.5]])))
        
        mock_arima.return_value = mock_model
        mock_model.fit.return_value = mock_fit
        mock_fit.forecast.return_value = mock_forecast.return_value
        
        data = pd.Series([1, 2, 3, 4, 5])
        result = predictor.predict_arima(data, horizon=3)
        
        assert result['predictions'] == [1, 2, 3]
        assert 'confidence_intervals' in result
    
    def test_regression_prediction(self):
        """Test regression-based prediction"""
        predictor = FuturePredictor()
        
        # Create sample regression data
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([2, 4, 6, 8, 10])
        
        result = predictor.predict_regression(
            X_train=X,
            y_train=y,
            X_future=np.array([[6], [7], [8]]),
            method='linear'
        )
        
        assert 'predictions' in result
        assert len(result['predictions']) == 3
        assert result['predictions'][0] == pytest.approx(12, rel=0.1)
    
    def test_prophet_prediction(self):
        """Test Prophet model prediction"""
        predictor = FuturePredictor()
        
        # Create sample data for Prophet
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'ds': dates,
            'y': np.sin(np.arange(100) * 0.1) + np.random.normal(0, 0.1, 100)
        })
        
        with patch('prophet.Prophet') as mock_prophet:
            # Mock Prophet behavior
            mock_model = Mock()
            mock_prophet.return_value = mock_model
            mock_model.fit.return_value = mock_model
            mock_model.make_future_dataframe.return_value = pd.DataFrame({'ds': pd.date_range(start='2024-04-10', periods=10, freq='D')})
            mock_model.predict.return_value = pd.DataFrame({
                'yhat': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'yhat_lower': [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
                'yhat_upper': [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5]
            })
            
            result = predictor.predict_prophet(data, horizon=10)
            
            assert 'predictions' in result
            assert len(result['predictions']) == 10
            assert 'confidence_intervals' in result


class TestRiskAssessor:
    """Test the RiskAssessor component"""
    
    def test_assessor_initialization(self):
        """Test risk assessor initialization"""
        assessor = RiskAssessor()
        assert assessor is not None
        assert hasattr(assessor, 'assess_risk')
    
    def test_probability_calculation(self):
        """Test probability distribution calculations"""
        assessor = RiskAssessor()
        
        # Test normal distribution risk
        result = assessor.calculate_probability(
            values=np.random.normal(100, 15, 1000),
            threshold=130,
            distribution='normal'
        )
        
        assert 'probability' in result
        assert 0 <= result['probability'] <= 1
        assert 'confidence' in result
        assert 'distribution_params' in result
    
    def test_monte_carlo_simulation(self):
        """Test Monte Carlo risk simulation"""
        assessor = RiskAssessor()
        
        def scenario_function(params):
            return params['base'] * (1 + np.random.normal(0, params['volatility']))
        
        result = assessor.monte_carlo_simulation(
            scenario_func=scenario_function,
            params={'base': 100, 'volatility': 0.2},
            iterations=1000
        )
        
        assert 'scenarios' in result
        assert len(result['scenarios']) == 1000
        assert 'statistics' in result
        assert 'percentiles' in result
        assert result['statistics']['mean'] == pytest.approx(100, rel=0.1)
    
    def test_risk_scoring(self):
        """Test risk scoring system"""
        assessor = RiskAssessor()
        
        factors = {
            'volatility': 0.3,
            'trend': -0.1,
            'outliers': 5,
            'data_quality': 0.8
        }
        
        result = assessor.calculate_risk_score(factors)
        
        assert 'risk_score' in result
        assert 0 <= result['risk_score'] <= 1
        assert 'risk_level' in result
        assert result['risk_level'] in ['low', 'medium', 'high', 'critical']
        assert 'components' in result
    
    def test_uncertainty_quantification(self):
        """Test uncertainty quantification"""
        assessor = RiskAssessor()
        
        predictions = np.array([100, 105, 110, 115, 120])
        actuals = np.array([98, 107, 108, 118, 119])
        
        result = assessor.quantify_uncertainty(predictions, actuals)
        
        assert 'uncertainty_score' in result
        assert 'confidence_level' in result
        assert 'error_distribution' in result


class TestCapacityPlanner:
    """Test the CapacityPlanner component"""
    
    def test_planner_initialization(self):
        """Test capacity planner initialization"""
        planner = CapacityPlanner()
        assert planner is not None
        assert hasattr(planner, 'plan_capacity')
    
    def test_resource_prediction(self):
        """Test resource usage prediction"""
        planner = CapacityPlanner()
        
        # Historical resource usage data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        usage = np.linspace(50, 80, 30) + np.random.normal(0, 5, 30)
        data = pd.DataFrame({'date': dates, 'usage': usage})
        
        result = planner.predict_resource_usage(
            historical_data=data,
            horizon=7,
            resource_type='cpu'
        )
        
        assert 'predictions' in result
        assert len(result['predictions']) == 7
        assert 'capacity_threshold' in result
        assert 'scaling_recommendations' in result
    
    def test_growth_curve_fitting(self):
        """Test growth curve fitting for capacity planning"""
        planner = CapacityPlanner()
        
        # Simulate growth data
        time_points = np.arange(0, 100)
        capacity = 100 / (1 + np.exp(-0.1 * (time_points - 50)))  # Logistic growth
        
        result = planner.fit_growth_curve(
            time_points=time_points,
            values=capacity,
            curve_type='logistic'
        )
        
        assert 'parameters' in result
        assert 'fitted_values' in result
        assert 'saturation_point' in result
        assert 'growth_rate' in result
    
    def test_scaling_projection(self):
        """Test scaling projections"""
        planner = CapacityPlanner()
        
        current_metrics = {
            'cpu_usage': 75,
            'memory_usage': 60,
            'storage_usage': 45,
            'request_rate': 1000
        }
        
        growth_factors = {
            'user_growth': 1.5,
            'data_growth': 2.0,
            'complexity_growth': 1.2
        }
        
        result = planner.project_scaling_needs(
            current_metrics=current_metrics,
            growth_factors=growth_factors,
            time_horizon=90  # days
        )
        
        assert 'projected_metrics' in result
        assert 'scaling_timeline' in result
        assert 'resource_requirements' in result
        assert 'cost_projection' in result
    
    def test_seasonality_adjustment(self):
        """Test seasonality adjustment in capacity planning"""
        planner = CapacityPlanner()
        
        # Create data with weekly seasonality
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        base = np.linspace(100, 150, 60)
        seasonality = 10 * np.sin(2 * np.pi * np.arange(60) / 7)
        values = base + seasonality + np.random.normal(0, 5, 60)
        
        result = planner.adjust_for_seasonality(
            dates=dates,
            values=values,
            period='weekly'
        )
        
        assert 'trend' in result
        assert 'seasonal' in result
        assert 'residual' in result
        assert len(result['trend']) == 60


class TestAnomalyDetector:
    """Test the AnomalyDetector component"""
    
    def test_detector_initialization(self):
        """Test anomaly detector initialization"""
        detector = AnomalyDetector()
        assert detector is not None
        assert hasattr(detector, 'detect_anomalies')
    
    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection methods"""
        detector = AnomalyDetector()
        
        # Create data with anomalies
        normal_data = np.random.normal(100, 10, 1000)
        anomalies = np.array([200, 250, 50, 30])
        data = np.concatenate([normal_data, anomalies])
        np.random.shuffle(data)
        
        result = detector.detect_statistical_anomalies(
            data=data,
            method='zscore',
            threshold=3
        )
        
        assert 'anomaly_indices' in result
        assert 'anomaly_scores' in result
        assert len(result['anomaly_indices']) >= 4  # Should detect at least the injected anomalies
        assert 'threshold_used' in result
    
    def test_isolation_forest_detection(self):
        """Test Isolation Forest anomaly detection"""
        detector = AnomalyDetector()
        
        # Create 2D data with anomalies
        normal_data = np.random.multivariate_normal([0, 0], [[1, 0.5], [0.5, 1]], 100)
        anomalies = np.array([[5, 5], [-5, -5], [5, -5], [-5, 5]])
        data = np.vstack([normal_data, anomalies])
        
        result = detector.detect_isolation_forest(
            data=data,
            contamination=0.1
        )
        
        assert 'anomaly_labels' in result
        assert 'anomaly_scores' in result
        anomaly_labels = np.array(result['anomaly_labels'])
        assert sum(anomaly_labels == -1) > 0  # Should detect some anomalies
        assert 'model_params' in result
    
    def test_pyod_ensemble_detection(self):
        """Test PyOD ensemble anomaly detection"""
        detector = AnomalyDetector()
        
        # Create data with clear anomalies
        X = np.random.randn(200, 2)
        X = np.r_[X + 2, X - 2]  # Two clusters
        outliers = np.random.uniform(low=-6, high=6, size=(20, 2))
        X = np.r_[X, outliers]
        
        with patch('pyod.models.combination.SUOD') as mock_suod:
            # Mock PyOD SUOD ensemble
            mock_model = Mock()
            mock_suod.return_value = mock_model
            mock_model.fit.return_value = mock_model
            mock_model.decision_scores_ = np.random.rand(len(X))
            mock_model.labels_ = np.zeros(len(X))
            mock_model.labels_[-20:] = 1  # Last 20 are anomalies
            
            result = detector.detect_pyod_ensemble(
                data=X,
                algorithms=['knn', 'lof', 'iforest']
            )
            
            assert 'anomaly_labels' in result
            assert 'ensemble_scores' in result
            assert 'algorithm_scores' in result
            assert sum(result['anomaly_labels']) >= 10
    
    def test_pattern_deviation_detection(self):
        """Test pattern deviation detection"""
        detector = AnomalyDetector()
        
        # Create time series with pattern change
        t = np.arange(100)
        pattern1 = np.sin(0.1 * t[:50])
        pattern2 = np.sin(0.2 * t[50:]) + 2  # Different frequency and level
        data = np.concatenate([pattern1, pattern2])
        
        result = detector.detect_pattern_deviation(
            data=data,
            window_size=10
        )
        
        assert 'change_points' in result
        assert 'deviation_scores' in result
        assert 50 in result['change_points'] or 49 in result['change_points']  # Should detect the pattern change


class TestPredictionMagic:
    """Test the main PredictionMagic class"""
    
    def test_magic_initialization(self):
        """Test PredictionMagic initialization"""
        magic = PredictionMagic()
        
        assert magic.name == "Prediction Magic"
        assert magic.magic_type == "prediction"
        assert isinstance(magic.future_predictor, FuturePredictor)
        assert isinstance(magic.risk_assessor, RiskAssessor)
        assert isinstance(magic.capacity_planner, CapacityPlanner)
        assert isinstance(magic.anomaly_detector, AnomalyDetector)
    
    def test_identify_intent(self):
        """Test intent identification"""
        magic = PredictionMagic()
        
        assert magic._identify_intent("predict sales for next month") == PredictionIntent.FUTURE_FORECAST
        assert magic._identify_intent("assess project risk") == PredictionIntent.RISK_ASSESSMENT
        assert magic._identify_intent("plan server capacity") == PredictionIntent.CAPACITY_PLANNING
        assert magic._identify_intent("detect anomalies in logs") == PredictionIntent.ANOMALY_DETECTION
        assert magic._identify_intent("random query") == PredictionIntent.UNKNOWN
    
    def test_cast_magic_future_forecast(self):
        """Test casting magic for future forecasting"""
        magic = PredictionMagic()
        
        # Create sample time series data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        values = np.sin(np.arange(50) * 0.1) + np.random.normal(0, 0.1, 50)
        
        query = "predict next 7 days"
        context = {
            'data': pd.DataFrame({'date': dates, 'value': values}),
            'horizon': 7
        }
        
        result = magic.cast_magic(query, context)
        
        assert result.prediction_type == "future_forecast"
        assert 'values' in result.predictions
        assert len(result.predictions['values']) == 7
        assert 'model' in result.metadata
        # Metrics are only present when actual values are provided for validation
    
    def test_cast_magic_risk_assessment(self):
        """Test casting magic for risk assessment"""
        magic = PredictionMagic()
        
        query = "assess risk of system failure"
        context = {
            'historical_failures': [0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
            'current_metrics': {
                'cpu_usage': 85,
                'memory_usage': 92,
                'error_rate': 0.05
            }
        }
        
        result = magic.cast_magic(query, context)
        
        assert result.prediction_type == "risk_assessment"
        assert 'risk_score' in result.predictions
        assert 0 <= result.predictions['risk_score'] <= 1
        assert 'risk_level' in result.predictions
        assert 'factors' in result.metadata
    
    def test_cast_magic_capacity_planning(self):
        """Test casting magic for capacity planning"""
        magic = PredictionMagic()
        
        query = "plan capacity for next quarter"
        context = {
            'current_usage': {'cpu': 60, 'memory': 70, 'storage': 50},
            'growth_rate': 0.15,
            'time_horizon': 90
        }
        
        result = magic.cast_magic(query, context)
        
        assert result.prediction_type == "capacity_planning"
        assert 'projections' in result.predictions
        assert 'scaling_needs' in result.predictions
        assert 'recommendations' in result.metadata
    
    def test_cast_magic_anomaly_detection(self):
        """Test casting magic for anomaly detection"""
        magic = PredictionMagic()
        
        # Create data with anomalies
        normal_data = np.random.normal(100, 10, 100).tolist()
        anomalies = [200, 250, 50]
        data = normal_data + anomalies
        
        query = "detect anomalies in metrics"
        context = {
            'data': data,
            'method': 'statistical'
        }
        
        result = magic.cast_magic(query, context)
        
        assert result.prediction_type == "anomaly_detection"
        assert 'anomalies' in result.predictions
        assert 'anomaly_count' in result.predictions
        assert len(result.predictions['anomalies']) > 0
        assert 'detection_method' in result.metadata
    
    def test_cast_magic_with_error(self):
        """Test error handling in cast_magic"""
        magic = PredictionMagic()
        
        query = "predict without data"
        context = {}  # Empty context should cause error
        
        with pytest.raises(PredictionError):
            magic.cast_magic(query, context)
    
    def test_validate_predictions(self):
        """Test prediction validation"""
        magic = PredictionMagic()
        
        predictions = np.array([100, 105, 110, 115, 120])
        actuals = np.array([98, 107, 108, 118, 119])
        
        metrics = magic.validate_predictions(predictions, actuals)
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'mape' in metrics
        assert metrics['rmse'] < 5  # Should be reasonably accurate
    
    def test_get_capabilities(self):
        """Test getting magic capabilities"""
        magic = PredictionMagic()
        
        capabilities = magic.get_capabilities()
        
        assert 'name' in capabilities
        assert 'type' in capabilities
        assert 'intents' in capabilities
        assert len(capabilities['intents']) == 4
        assert 'methods' in capabilities
        assert 'description' in capabilities
    
    def test_explain_prediction(self):
        """Test prediction explanation"""
        magic = PredictionMagic()
        
        result = PredictionResult(
            prediction_type="future_forecast",
            predictions={"values": [100, 105, 110]},
            confidence_intervals={"lower": [95, 100, 105], "upper": [105, 110, 115]},
            metrics={"rmse": 2.5, "mae": 2.0},
            metadata={"model": "ARIMA", "parameters": {"p": 1, "d": 1, "q": 1}}
        )
        
        explanation = magic.explain_prediction(result)
        
        assert 'summary' in explanation
        assert 'method_used' in explanation
        assert 'confidence_explanation' in explanation
        assert 'limitations' in explanation
    
    def test_integration_with_ancient_magic(self):
        """Test integration with Ancient Magic system"""
        magic = PredictionMagic()
        
        # Test that it follows Ancient Magic interface
        assert hasattr(magic, 'name')
        assert hasattr(magic, 'magic_type')
        assert hasattr(magic, 'cast_magic')
        assert hasattr(magic, 'get_capabilities')
        
        # Test magic metadata
        assert magic.name == "Prediction Magic"
        assert magic.magic_type == "prediction"
        
        # Test that cast_magic returns PredictionResult
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        values = np.random.randn(30).cumsum() + 100
        
        result = magic.cast_magic(
            "forecast next week",
            {'data': pd.DataFrame({'date': dates, 'value': values}), 'horizon': 7}
        )
        
        assert isinstance(result, PredictionResult)
        assert hasattr(result, 'to_dict')


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        magic = PredictionMagic()
        
        with pytest.raises(PredictionError):
            magic.cast_magic("predict future", {'data': pd.DataFrame()})
    
    def test_invalid_intent_handling(self):
        """Test handling of invalid intent"""
        magic = PredictionMagic()
        
        result = magic.cast_magic("do something random", {'data': [1, 2, 3]})
        
        assert result.prediction_type == "unknown"
        assert 'error' in result.predictions
    
    def test_large_data_handling(self):
        """Test handling of large datasets"""
        magic = PredictionMagic()
        
        # Create large dataset
        large_data = np.random.randn(10000)
        
        query = "detect anomalies"
        context = {'data': large_data, 'method': 'statistical'}
        
        result = magic.cast_magic(query, context)
        
        assert result.prediction_type == "anomaly_detection"
        assert 'processing_time' in result.metadata
    
    def test_missing_dependencies_handling(self):
        """Test graceful handling of missing dependencies"""
        magic = PredictionMagic()
        
        with patch('prophet.Prophet', side_effect=ImportError("Prophet not installed")):
            # Should fall back to other methods
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            data = pd.DataFrame({'date': dates, 'value': np.random.randn(30)})
            
            result = magic.cast_magic(
                "predict future with prophet",
                {'data': data, 'horizon': 7, 'method': 'prophet'}
            )
            
            assert result.prediction_type == "future_forecast"
            assert result.metadata['model'] != 'prophet'  # Should use fallback


class TestPerformance:
    """Test performance requirements"""
    
    def test_prediction_speed(self):
        """Test that predictions complete within reasonable time"""
        import time
        
        magic = PredictionMagic()
        
        # Medium-sized dataset
        data = np.random.randn(1000)
        
        start_time = time.time()
        result = magic.cast_magic(
            "detect anomalies quickly",
            {'data': data, 'method': 'statistical'}
        )
        end_time = time.time()
        
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        assert result.prediction_type == "anomaly_detection"
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets"""
        import psutil
        import os
        
        magic = PredictionMagic()
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        large_data = np.random.randn(100000)
        result = magic.cast_magic(
            "analyze large dataset",
            {'data': large_data, 'method': 'statistical'}
        )
        
        # Check memory usage didn't explode
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 500  # Should not increase by more than 500MB
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
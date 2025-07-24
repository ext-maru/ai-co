#!/usr/bin/env python3
"""
Prediction Magic - The eighth Ancient Magic of the Elder system
Handles future prediction, risk assessment, capacity planning, and anomaly detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Import additional libraries with graceful fallback
try:
    import statsmodels.api as sm
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("statsmodels not available, some features will be limited")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available, robust forecasting will be limited")

try:
    from pyod.models.knn import KNN
    from pyod.models.lof import LOF
    from pyod.models.iforest import IForest
    from pyod.models.combination import SUOD
    PYOD_AVAILABLE = True
except ImportError:
    PYOD_AVAILABLE = False
    logging.warning("PyOD not available, advanced anomaly detection will be limited")

try:
    from pmdarima import auto_arima
    PMDARIMA_AVAILABLE = True
except ImportError:
    PMDARIMA_AVAILABLE = False
    logging.warning("pmdarima not available, auto ARIMA will be limited")


class PredictionIntent(Enum):
    pass

    """Types of prediction intents""" str) -> 'PredictionIntent':
        """Determine intent from query text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['predict', 'forecast', 'future']):
            return cls.FUTURE_FORECAST
        elif any(word in text_lower for word in ['risk', 'assess', 'probability']):
            return cls.RISK_ASSESSMENT
        elif any(word in text_lower for word in ['capacity', 'plan', 'scale']):
            return cls.CAPACITY_PLANNING
        elif any(word in text_lower for word in ['anomaly', 'outlier', 'detect']):
            return cls.ANOMALY_DETECTION
        else:
            return cls.UNKNOWN


@dataclass
class PredictionResult:
    pass

            """Result of a prediction magic operation""" str
    predictions: Dict[str, Any]
    confidence_intervals: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        pass

    
    """Convert to dictionary for serialization""" self.prediction_type,
            'predictions': self.predictions,
            'confidence_intervals': self.confidence_intervals,
            'metrics': self.metrics,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class PredictionError(Exception):
    pass

        """Custom exception for prediction errors"""
    """Component for future prediction and forecasting"""
    
    def __init__(self):
        self.models = {
            'linear': LinearRegression,
            'ridge': Ridge,
            'lasso': Lasso
        }
        self.scaler = StandardScaler()
    
    def predict_time_series(self, data: pd.DataFrame, horizon: int, method: str = 'auto') -> Dict[str, Any]:
        """Predict future values for time series data"""
        if method == 'auto':
            # Choose best method based on data characteristics
            if len(data) > 50 and STATSMODELS_AVAILABLE:
                method = 'arima'
            elif PROPHET_AVAILABLE and 'date' in data.columns:
                method = 'prophet'
            else:
                method = 'regression'
        
        if method == 'arima':
            return self.predict_arima(data['value'] if 'value' in data.columns else data.iloc[:, -1], horizon)
        elif method == 'prophet':
            return self.predict_prophet(data, horizon)
        else:
            # Fallback to regression
            X = np.arange(len(data)).reshape(-1, 1)
            y = data['value'].values if 'value' in data.columns else data.iloc[:, -1].values
            X_future = np.arange(len(data), len(data) + horizon).reshape(-1, 1)
            return self.predict_regression(X, y, X_future, 'linear')
    
    def predict_arima(self, data: pd.Series, horizon: int) -> Dict[str, Any]:
        """ARIMA-based prediction"""
        if not STATSMODELS_AVAILABLE:
            raise PredictionError("statsmodels not available for ARIMA prediction")
        
        try:
            # Auto-select ARIMA parameters if pmdarima available
            if PMDARIMA_AVAILABLE:
                model = auto_arima(data, seasonal=False, suppress_warnings=True)
                predictions = model.predict(n_periods=horizon)
                # Get confidence intervals
                predictions_df = model.predict(n_periods=horizon, return_conf_int=True)
                if isinstance(predictions_df, tuple):
                    predictions, conf_int = predictions_df
                    lower = conf_int[:, 0].tolist()
                    upper = conf_int[:, 1].tolist()
                else:
                    lower = (predictions - 1.96 * np.std(data)).tolist()
                    upper = (predictions + 1.96 * np.std(data)).tolist()
            else:
                # Simple ARIMA(1,1,1)
                model = ARIMA(data, order=(1, 1, 1))
                model_fit = model.fit()
                forecast = model_fit.forecast(steps=horizon)
                predictions = forecast
                # Simple confidence intervals
                std_error = np.std(model_fit.resid)
                lower = (predictions - 1.96 * std_error).tolist()
                upper = (predictions + 1.96 * std_error).tolist()
            
            return {
                'predictions': predictions.tolist() if hasattr(predictions, 'tolist') else predictions,
                'confidence_intervals': {
                    'lower': lower,
                    'upper': upper
                },
                'model_used': 'ARIMA'
            }
        except Exception as e:
            raise PredictionError(f"ARIMA prediction failed: {str(e)}")
    
    def predict_prophet(self, data: pd.DataFrame, horizon: int) -> Dict[str, Any]:
        """Prophet-based prediction"""
        if not PROPHET_AVAILABLE:
            raise PredictionError("Prophet not available for forecasting")
        
        try:
            # Prepare data for Prophet
            prophet_data = data.copy()
            if 'ds' not in prophet_data.columns:
                prophet_data['ds'] = data['date'] if 'date' in data.columns else pd.date_range(start='2024-01-01', periods=len(data), freq='D')
            if 'y' not in prophet_data.columns:
                prophet_data['y'] = data['value'] if 'value' in data.columns else data.iloc[:, -1]
            
            # Fit Prophet model
            model = Prophet(daily_seasonality=True, yearly_seasonality=True)
            model.fit(prophet_data[['ds', 'y']])
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)
            
            # Extract predictions
            predictions = forecast['yhat'].tail(horizon).tolist()
            lower = forecast['yhat_lower'].tail(horizon).tolist()
            upper = forecast['yhat_upper'].tail(horizon).tolist()
            
            return {
                'predictions': predictions,
                'confidence_intervals': {
                    'lower': lower,
                    'upper': upper
                },
                'model_used': 'Prophet'
            }
        except Exception as e:
            raise PredictionError(f"Prophet prediction failed: {str(e)}")
    
    def predict_regression(self, X_train: np.ndarray, y_train: np.ndarray, 
                          X_future: np.ndarray, method: str = 'linear') -> Dict[str, Any]:
        """Regression-based prediction"""
        try:
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_future_scaled = self.scaler.transform(X_future)
            
            # Select and fit model
            model_class = self.models.get(method, LinearRegression)
            model = model_class()
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            predictions = model.predict(X_future_scaled)
            
            # Calculate simple confidence intervals
            train_predictions = model.predict(X_train_scaled)
            residuals = y_train - train_predictions
            std_error = np.std(residuals)
            
            return {
                'predictions': predictions.tolist(),
                'confidence_intervals': {
                    'lower': (predictions - 1.96 * std_error).tolist(),
                    'upper': (predictions + 1.96 * std_error).tolist()
                },
                'model_used': f'{method}_regression'
            }
        except Exception as e:
            raise PredictionError(f"Regression prediction failed: {str(e)}")


class RiskAssessor:
    pass



"""Component for risk assessment and uncertainty quantification""" Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk based on various factors"""
        risk_factors = {}
        
        # Extract risk factors from data
        if 'historical_failures' in data:
            failure_rate = sum(data['historical_failures']) / len(data['historical_failures'])
            risk_factors['failure_rate'] = failure_rate
        
        if 'current_metrics' in data:
            metrics = data['current_metrics']
            if 'cpu_usage' in metrics:
                risk_factors['cpu_risk'] = metrics['cpu_usage'] / 100
            if 'memory_usage' in metrics:
                risk_factors['memory_risk'] = metrics['memory_usage'] / 100
            if 'error_rate' in metrics:
                risk_factors['error_risk'] = metrics['error_rate']
        
        # Calculate overall risk score
        risk_score = self.calculate_risk_score(risk_factors)
        
        return risk_score
    
    def calculate_probability(self, values: np.ndarray, threshold: float, 
                            distribution: str = 'normal') -> Dict[str, Any]:
        """Calculate probability of exceeding threshold"""
        if distribution == 'normal':
            mean = np.mean(values)
            std = np.std(values)
            z_score = (threshold - mean) / std
            probability = 1 - stats.norm.cdf(z_score)
            
            return {
                'probability': probability,
                'confidence': 0.95,  # 95% confidence
                'distribution_params': {
                    'mean': mean,
                    'std': std
                }
            }
        else:
            # Non-parametric approach
            probability = np.sum(values > threshold) / len(values)
            return {
                'probability': probability,
                'confidence': 0.9,
                'distribution_params': {
                    'method': 'empirical'
                }
            }
    
    def monte_carlo_simulation(self, scenario_func: callable, params: Dict[str, Any], 
                              iterations: int = 1000) -> Dict[str, Any]:
        """Run Monte Carlo simulation for risk assessment"""
        scenarios = []
        
        for _ in range(iterations):
            result = scenario_func(params)
            scenarios.append(result)
        
        scenarios = np.array(scenarios)
        
        return {
            'scenarios': scenarios.tolist(),
            'statistics': {
                'mean': float(np.mean(scenarios)),
                'std': float(np.std(scenarios)),
                'min': float(np.min(scenarios)),
                'max': float(np.max(scenarios))
            },
            'percentiles': {
                '5': float(np.percentile(scenarios, 5)),
                '25': float(np.percentile(scenarios, 25)),
                '50': float(np.percentile(scenarios, 50)),
                '75': float(np.percentile(scenarios, 75)),
                '95': float(np.percentile(scenarios, 95))
            }
        }
    
    def calculate_risk_score(self, factors: Dict[str, float]) -> Dict[str, Any]:
        """Calculate overall risk score from multiple factors"""
        # Weighted risk calculation
        weights = {
            'failure_rate': 0.3,
            'cpu_risk': 0.2,
            'memory_risk': 0.2,
            'error_risk': 0.2,
            'volatility': 0.1
        }
        
        risk_score = 0
        components = {}
        
        for factor, value in factors.items():
            weight = weights.get(factor, 0.1)
            component_score = value * weight
            risk_score += component_score
            components[factor] = component_score
        
        # Normalize to 0-1 range
        risk_score = min(max(risk_score, 0), 1)
        
        # Determine risk level
        if risk_score < 0.25:
            risk_level = 'low'
        elif risk_score < 0.5:
            risk_level = 'medium'
        elif risk_score < 0.75:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'components': components
        }
    
    def quantify_uncertainty(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict[str, Any]:
        """Quantify uncertainty in predictions"""
        errors = predictions - actuals
        
        return {
            'uncertainty_score': float(np.std(errors)),
            'confidence_level': float(1 - (np.std(errors) / np.mean(np.abs(actuals)))),
            'error_distribution': {
                'mean': float(np.mean(errors)),
                'std': float(np.std(errors)),
                'skew': float(stats.skew(errors)),
                'kurtosis': float(stats.kurtosis(errors))
            }
        }


class CapacityPlanner:
    pass

            """Component for capacity planning and resource prediction""" Dict[str, Any]) -> Dict[str, Any]:
        """Plan capacity based on current usage and growth"""
        current_usage = data.get('current_usage', {})
        growth_rate = data.get('growth_rate', 0.1)
        time_horizon = data.get('time_horizon', 90)
        
        projections = {}
        scaling_needs = {}
        
        for resource, usage in current_usage.items():
            # Project future usage
            days = np.arange(time_horizon)
            projected = usage * (1 + growth_rate) ** (days / 365)
            projections[resource] = projected.tolist()
            
            # Determine when scaling is needed (80% threshold)
            scaling_day = np.where(projected > 80)[0]
            if len(scaling_day) > 0:
                scaling_needs[resource] = int(scaling_day[0])
            else:
                scaling_needs[resource] = None
        
        return {
            'projections': projections,
            'scaling_needs': scaling_needs,
            'recommendations': self._generate_recommendations(scaling_needs)
        }
    
    def predict_resource_usage(self, historical_data: pd.DataFrame, horizon: int, 
                              resource_type: str) -> Dict[str, Any]:
        """Predict future resource usage"""
        # Use time series prediction
        predictor = FuturePredictor()
        
        try:
            result = predictor.predict_time_series(historical_data, horizon)
            predictions = result['predictions']
            
            # Determine capacity threshold
            max_historical = historical_data['usage'].max() if 'usage' in historical_data else historical_data.iloc[:, -1].max()
            capacity_threshold = max_historical * 1.2  # 20% buffer
            
            # Generate scaling recommendations
            scaling_recommendations = []
            for i, pred in enumerate(predictions):
                if pred > capacity_threshold * 0.8:  # 80% of capacity
                    scaling_recommendations.append({
                        'day': i + 1,
                        'predicted_usage': pred,
                        'action': 'scale_up'
                    })
            
            return {
                'predictions': predictions,
                'capacity_threshold': capacity_threshold,
                'scaling_recommendations': scaling_recommendations
            }
        except Exception as e:
            raise PredictionError(f"Resource prediction failed: {str(e)}")
    
    def fit_growth_curve(self, time_points: np.ndarray, values: np.ndarray, 
                        curve_type: str = 'logistic') -> Dict[str, Any]:
        """Fit growth curve to data"""
        if curve_type == 'logistic':
            # Logistic growth: y = L / (1 + exp(-k(x-x0)))
            from scipy.optimize import curve_fit
            
            def logistic(x, L, k, x0):
                return L / (1 + np.exp(-k * (x - x0)))
            
            # Initial guess
            L_init = np.max(values) * 1.1
            x0_init = time_points[len(time_points) // 2]
            k_init = 0.1
            
            try:
                popt, _ = curve_fit(logistic, time_points, values, p0=[L_init, k_init, x0_init])
                L, k, x0 = popt
                
                fitted_values = logistic(time_points, L, k, x0)
                
                return {
                    'parameters': {
                        'saturation': L,
                        'growth_rate': k,
                        'midpoint': x0
                    },
                    'fitted_values': fitted_values.tolist(),
                    'saturation_point': L,
                    'growth_rate': k
                }
            except Exception as e:
                raise PredictionError(f"Growth curve fitting failed: {str(e)}")
    
    def project_scaling_needs(self, current_metrics: Dict[str, float], 
                             growth_factors: Dict[str, float], 
                             time_horizon: int) -> Dict[str, Any]:
        """Project scaling needs based on growth factors"""
        projected_metrics = {}
        scaling_timeline = []
        
        # Calculate compound growth
        for metric, current_value in current_metrics.items():
            # Apply relevant growth factors
            total_growth = 1.0
            if metric == 'cpu_usage':
                total_growth *= growth_factors.get('user_growth', 1.0)
                total_growth *= growth_factors.get('complexity_growth', 1.0)
            elif metric == 'memory_usage':
                total_growth *= growth_factors.get('data_growth', 1.0)
                total_growth *= growth_factors.get('user_growth', 1.0)
            elif metric == 'storage_usage':
                total_growth *= growth_factors.get('data_growth', 1.0)
            
            # Project over time
            daily_growth = total_growth ** (1/365)
            projections = []
            for day in range(time_horizon):
                value = current_value * (daily_growth ** day)
                projections.append(value)
                
                # Check if scaling needed
                if value > 80 and len([s for s in scaling_timeline if s['metric'] == metric]) == 0:
                    scaling_timeline.append({
                        'day': day,
                        'metric': metric,
                        'projected_value': value
                    })
            
            projected_metrics[metric] = projections
        
        # Calculate resource requirements
        resource_requirements = {
            'cpu_cores': int(np.ceil(max(projected_metrics.get('cpu_usage', [0])) / 80 * 4)),
            'memory_gb': int(np.ceil(max(projected_metrics.get('memory_usage', [0])) / 80 * 16)),
            'storage_tb': int(np.ceil(max(projected_metrics.get('storage_usage', [0])) / 80 * 1))
        }
        
        # Simple cost projection
        cost_projection = {
            'daily_cost': resource_requirements['cpu_cores'] * 2 + 
                         resource_requirements['memory_gb'] * 0.5 + 
                         resource_requirements['storage_tb'] * 20,
            'monthly_cost': 0  # Will be calculated
        }
        cost_projection['monthly_cost'] = cost_projection['daily_cost'] * 30
        
        return {
            'projected_metrics': projected_metrics,
            'scaling_timeline': scaling_timeline,
            'resource_requirements': resource_requirements,
            'cost_projection': cost_projection
        }
    
    def adjust_for_seasonality(self, dates: pd.DatetimeIndex, values: np.ndarray, 
                              period: str = 'weekly') -> Dict[str, Any]:
        """Adjust predictions for seasonality"""
        if not STATSMODELS_AVAILABLE:
            # Simple moving average decomposition
            if period == 'weekly':
                window = 7
            elif period == 'monthly':
                window = 30
            else:
                window = 365
            
            # Calculate trend using moving average
            trend = pd.Series(values).rolling(window=window, center=True).mean()
            
            # Calculate seasonal component
            trend_filled = trend.bfill().ffill()
            detrended = values - trend_filled
            seasonal = detrended
            
            # Residual
            residual = values - trend_filled - seasonal
            
            return {
                'trend': trend_filled.tolist(),
                'seasonal': seasonal.tolist(),
                'residual': residual.tolist()
            }
        else:
            # Use statsmodels seasonal decomposition
            series = pd.Series(values, index=dates)
            
            if period == 'weekly':
                freq = 7
            elif period == 'monthly':
                freq = 30
            else:
                freq = 365
            
            decomposition = seasonal_decompose(series, model='additive', period=freq)
            
            return {
                'trend': decomposition.trend.fillna(method='bfill').fillna(method='ffill').tolist(),
                'seasonal': decomposition.seasonal.fillna(0).tolist(),
                'residual': decomposition.resid.fillna(0).tolist()
            }
    
    def _generate_recommendations(self, scaling_needs: Dict[str, Optional[int]]) -> List[str]:
        """Generate capacity planning recommendations"""
        recommendations = []
        
        for resource, days_until_scale in scaling_needs.items():
            if days_until_scale is not None:
                if days_until_scale < 7:
                    recommendations.append(f"URGENT: Scale {resource} within {days_until_scale} days")
                elif days_until_scale < 30:
                    recommendations.append(f"Plan to scale {resource} within {days_until_scale} days")
                else:
                    recommendations.append(f"Monitor {resource}, scaling needed in {days_until_scale} days")
        
        if not recommendations:
            recommendations.append("No immediate scaling required")
        
        return recommendations


class AnomalyDetector:
    pass

            """Component for anomaly and outlier detection""" Union[List, np.ndarray], method: str = 'auto') -> Dict[str, Any]:
        """Detect anomalies in data"""
        if isinstance(data, list):
            data = np.array(data)
        
        if method == 'auto':
            # Choose method based on data characteristics
            if len(data) < 50:
                method = 'statistical'
            elif len(data.shape) > 1 and PYOD_AVAILABLE:
                method = 'ensemble'
            else:
                method = 'isolation_forest'
        
        if method == 'statistical':
            return self.detect_statistical_anomalies(data)
        elif method == 'isolation_forest':
            return self.detect_isolation_forest(data.reshape(-1, 1) if len(data.shape) == 1 else data)
        elif method == 'ensemble' and PYOD_AVAILABLE:
            return self.detect_pyod_ensemble(data.reshape(-1, 1) if len(data.shape) == 1 else data)
        else:
            return self.detect_statistical_anomalies(data)
    
    def detect_statistical_anomalies(self, data: np.ndarray, method: str = 'zscore', 
                                   threshold: float = 3) -> Dict[str, Any]:
        """Detect anomalies using statistical methods"""
        if method == 'zscore':
            # Z-score method
            mean = np.mean(data)
            std = np.std(data)
            z_scores = np.abs((data - mean) / std)
            anomaly_mask = z_scores > threshold
            anomaly_indices = np.where(anomaly_mask)[0].tolist()
            anomaly_scores = z_scores.tolist()
        elif method == 'mad':
            # Median Absolute Deviation
            median = np.median(data)
            mad = np.median(np.abs(data - median))
            modified_z_scores = 0.6745 * (data - median) / mad
            anomaly_mask = np.abs(modified_z_scores) > threshold
            anomaly_indices = np.where(anomaly_mask)[0].tolist()
            anomaly_scores = np.abs(modified_z_scores).tolist()
        else:
            # IQR method
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            anomaly_mask = (data < lower_bound) | (data > upper_bound)
            anomaly_indices = np.where(anomaly_mask)[0].tolist()
            anomaly_scores = np.abs(data - np.median(data)).tolist()
        
        return {
            'anomaly_indices': anomaly_indices,
            'anomaly_scores': anomaly_scores,
            'threshold_used': threshold,
            'method': method
        }
    
    def detect_isolation_forest(self, data: np.ndarray, contamination: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest"""
        try:
            model = IsolationForest(contamination=contamination, random_state=42)
            anomaly_labels = model.fit_predict(data)
            anomaly_scores = model.score_samples(data)
            
            return {
                'anomaly_labels': anomaly_labels.tolist(),
                'anomaly_scores': (-anomaly_scores).tolist(),  # Convert to anomaly scores
                'model_params': {
                    'contamination': contamination,
                    'n_estimators': model.n_estimators
                }
            }
        except Exception as e:
            raise PredictionError(f"Isolation Forest detection failed: {str(e)}")
    
    def detect_pyod_ensemble(self, data: np.ndarray, algorithms: List[str] = None) -> Dict[str, Any]:
        """Detect anomalies using PyOD ensemble methods"""
        if not PYOD_AVAILABLE:
            raise PredictionError("PyOD not available for ensemble detection")
        
        if algorithms is None:
            algorithms = ['knn', 'lof', 'iforest']
        
        try:
            # Create base detectors
            detectors = []
            for algo in algorithms:
                if algo == 'knn':
                    detectors.append(KNN())
                elif algo == 'lof':
                    detectors.append(LOF())
                elif algo == 'iforest':
                    detectors.append(IForest())
            
            # Create ensemble
            model = SUOD(base_estimators=detectors, combination='average')
            model.fit(data)
            
            anomaly_labels = model.labels_
            anomaly_scores = model.decision_scores_
            
            # Get individual algorithm scores
            algorithm_scores = {}
            for i, algo in enumerate(algorithms):
                algorithm_scores[algo] = model.base_estimators[i].decision_scores_.tolist()
            
            return {
                'anomaly_labels': anomaly_labels.tolist(),
                'ensemble_scores': anomaly_scores.tolist(),
                'algorithm_scores': algorithm_scores
            }
        except Exception as e:
            raise PredictionError(f"PyOD ensemble detection failed: {str(e)}")
    
    def detect_pattern_deviation(self, data: np.ndarray, window_size: int = 10) -> Dict[str, Any]:
        """Detect deviations from expected patterns"""
        change_points = []
        deviation_scores = []
        
        for i in range(window_size, len(data) - window_size):
            # Compare windows before and after
            window_before = data[i-window_size:i]
            window_after = data[i:i+window_size]
            
            # Calculate statistical difference
            t_stat, p_value = stats.ttest_ind(window_before, window_after)
            deviation_score = abs(t_stat)
            
            deviation_scores.append(deviation_score)
            
            # Mark as change point if significant
            if p_value < 0.05 and deviation_score > 2:
                change_points.append(i)
        
        return {
            'change_points': change_points,
            'deviation_scores': deviation_scores,
            'window_size': window_size
        }


class PredictionMagic:
    pass

        """Main Prediction Magic class - the eighth Ancient Magic"""
        self.name = "Prediction Magic"
        self.magic_type = "prediction"
        self.future_predictor = FuturePredictor()
        self.risk_assessor = RiskAssessor()
        self.capacity_planner = CapacityPlanner()
        self.anomaly_detector = AnomalyDetector()
        self.logger = logging.getLogger(__name__)
    
    def cast_magic(self, query: str, context: Dict[str, Any]) -> PredictionResult:
        """Cast prediction magic based on query and context"""
        # Identify intent
        intent = self._identify_intent(query)
        
        try:
            if intent == PredictionIntent.FUTURE_FORECAST:
                return self._handle_future_forecast(query, context)
            elif intent == PredictionIntent.RISK_ASSESSMENT:
                return self._handle_risk_assessment(query, context)
            elif intent == PredictionIntent.CAPACITY_PLANNING:
                return self._handle_capacity_planning(query, context)
            elif intent == PredictionIntent.ANOMALY_DETECTION:
                return self._handle_anomaly_detection(query, context)
            else:
                return self._handle_unknown_intent(query, context)
        except Exception as e:
            self.logger.error(f"Prediction magic failed: {str(e)}")
            raise PredictionError(f"Failed to cast prediction magic: {str(e)}")
    
    def _identify_intent(self, query: str) -> PredictionIntentreturn PredictionIntent.from_string(query)
    """Identify the prediction intent from the query"""
    :
    def _handle_future_forecast(self, query: str, context: Dict[str, Any]) -> PredictionResult:
        """Handle future forecasting requests"""
        if 'data' not in context:
            raise PredictionError("No data provided for forecasting")
        
        data = context['data']
        if isinstance(data, pd.DataFrame) and data.empty:
            raise PredictionError("Empty dataframe provided")
        
        horizon = context.get('horizon', 7)
        method = context.get('method', 'auto')
        
        # Perform prediction
        import time
        start_time = time.time()
        
        result = self.future_predictor.predict_time_series(data, horizon, method)
        
        processing_time = time.time() - start_time
        
        # Calculate metrics if we have ground truth
        metrics = None
        if 'actual_values' in context:
            predictions = np.array(result['predictions'])
            actuals = np.array(context['actual_values'])
            metrics = self.validate_predictions(predictions, actuals)
        
        return PredictionResult(
            prediction_type="future_forecast",
            predictions={'values': result['predictions']},
            confidence_intervals=result.get('confidence_intervals'),
            metrics=metrics,
            metadata={
                'model': result.get('model_used', 'unknown'),
                'horizon': horizon,
                'processing_time': processing_time
            }
        )
    
    def _handle_risk_assessment(self, query: str, context: Dict[str, Any]) -> PredictionResult:
        """Handle risk assessment requests"""
        # Assess risk
        risk_result = self.risk_assessor.assess_risk(context)
        
        # Add probability calculations if threshold provided
        if 'threshold' in context and 'values' in context:
            prob_result = self.risk_assessor.calculate_probability(
                np.array(context['values']),
                context['threshold']
            )
            risk_result['probability'] = prob_result['probability']
        
        return PredictionResult(
            prediction_type="risk_assessment",
            predictions={
                'risk_score': risk_result['risk_score'],
                'risk_level': risk_result['risk_level']
            },
            confidence_intervals=None,
            metrics={'components': risk_result['components']},
            metadata={'factors': list(risk_result['components'].keys())}
        )
    
    def _handle_capacity_planning(self, query: str, context: Dict[str, Any]) -> PredictionResult:
        """Handle capacity planning requests"""
        # Plan capacity
        capacity_result = self.capacity_planner.plan_capacity(context)
        
        return PredictionResult(
            prediction_type="capacity_planning",
            predictions={
                'projections': capacity_result['projections'],
                'scaling_needs': capacity_result['scaling_needs']
            },
            confidence_intervals=None,
            metrics=None,
            metadata={'recommendations': capacity_result['recommendations']}
        )
    
    def _handle_anomaly_detection(self, query: str, context: Dict[str, Any]) -> PredictionResult:
        """Handle anomaly detection requests"""
        if 'data' not in context:
            raise PredictionError("No data provided for anomaly detection")
        
        data = context['data']
        method = context.get('method', 'auto')
        
        # Track processing time
        import time
        start_time = time.time()
        
        # Detect anomalies
        anomaly_result = self.anomaly_detector.detect_anomalies(data, method)
        
        processing_time = time.time() - start_time
        
        # Format results
        if 'anomaly_indices' in anomaly_result:
            anomalies = anomaly_result['anomaly_indices']
        else:
            # Convert labels to indices
            labels = np.array(anomaly_result.get('anomaly_labels', []))
            anomalies = np.where(labels == -1)[0].tolist()
        
        return PredictionResult(
            prediction_type="anomaly_detection",
            predictions={
                'anomalies': anomalies,
                'anomaly_count': len(anomalies),
                'anomaly_scores': anomaly_result.get('anomaly_scores', [])
            },
            confidence_intervals=None,
            metrics={'total_points': len(data)},
            metadata={'detection_method': method, 'processing_time': processing_time}
        )
    
    def _handle_unknown_intent(self, query: str, context: Dict[str, Any]) -> PredictionResult:
        """Handle unknown intents"""
        return PredictionResult(
            prediction_type="unknown",
            predictions={'error': 'Could not determine prediction intent'},
            confidence_intervals=None,
            metrics=None,
            metadata={'query': query}
        )
    
    def validate_predictions(self, predictions: np.ndarray, actuals: np.ndarray) -> Dict[str, float]rmse = float(np.sqrt(mean_squared_error(actuals, predictions)))
    """Validate predictions against actual values"""
        mae = float(mean_absolute_error(actuals, predictions))
        mape = float(np.mean(np.abs((actuals - predictions) / actuals)) * 100)
        
        return {:
            'rmse': rmse,
            'mae': mae,
            'mape': mape
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        pass

        """Get the capabilities of this magic""" self.name,
            'type': self.magic_type,
            'intents': [intent.value for intent in PredictionIntent if intent != PredictionIntent.UNKNOWN],
            'methods': {
                'future_forecast': ['arima', 'prophet', 'regression'],
                'risk_assessment': ['monte_carlo', 'probability', 'scoring'],
                'capacity_planning': ['growth_curves', 'projections', 'seasonality'],
                'anomaly_detection': ['statistical', 'isolation_forest', 'ensemble']
            },
            'description': 'Prediction Magic for forecasting, risk assessment, capacity planning, and anomaly detection'
        }
    
    def explain_prediction(self, result: PredictionResult) -> Dict[str, str]:
        """Explain a prediction result"""
        explanations = {
            'future_forecast': "Used time series analysis to predict future values based on historical patterns.",
            'risk_assessment': "Analyzed multiple risk factors to calculate overall risk score and probability.",
            'capacity_planning': "Projected resource usage based on growth factors and historical trends.",
            'anomaly_detection': "Identified data points that deviate significantly from expected patterns."
        }
        
        base_explanation = explanations.get(result.prediction_type, "Performed prediction analysis.")
        
        # Add method-specific details
        method_details = ""
        if result.metadata and 'model' in result.metadata:
            method_details = f" Model used: {result.metadata['model']}."
        
        # Add confidence explanation
        confidence_explanation = ""
        if result.confidence_intervals:
            confidence_explanation = " Confidence intervals provided for uncertainty quantification."
        
        # Add limitations
        limitations = {
            'future_forecast': "Predictions assume historical patterns will continue.",
            'risk_assessment': "Risk scores are based on available data and may not capture all factors.",
            'capacity_planning': "Projections assume linear or exponential growth patterns.",
            'anomaly_detection': "Detection sensitivity depends on threshold settings."
        }
        
        limitation = limitations.get(result.prediction_type, "Results should be validated with domain expertise.")
        
        return {
            'summary': base_explanation + method_details,
            'method_used': result.metadata.get('model', 'Statistical analysis') if result.metadata else 'Unknown',
            'confidence_explanation': confidence_explanation or "Point estimates provided without confidence intervals.",
            'limitations': limitation
        }


# Create a singleton instance for easy import
prediction_magic = PredictionMagic()
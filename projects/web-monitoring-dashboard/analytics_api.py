#!/usr/bin/env python3
"""
高度分析エンジン API
4賢者システムのデータを統合的に分析
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, Blueprint, jsonify, request
from libs.metrics_aggregator import MetricsAggregator
from libs.data_pipeline import DataProcessingPipeline

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
analytics_api = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')

class AdvancedAnalyticsEngine:
    """高度分析エンジン"""
    
    def __init__(self):
        self.metrics_aggregator = MetricsAggregator()
        self.data_pipeline = DataProcessingPipeline()
        self.cache = {}
        self.cache_ttl = 300  # 5分
    
    def time_series_analysis(self, metric_name: str, 
                           start_date: datetime, 
                           end_date: datetime,
                           granularity: str = "hour") -> Dict[str, Any]:
        """時系列分析"""
        try:
            # データ取得
            data = self.metrics_aggregator.get_metric_data(
                metric_name, start_date, end_date, granularity
            )
            
            if not data:
                return {"error": "No data available for analysis"}
            
            # DataFrameに変換
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 基本統計
            basic_stats = {
                "mean": float(df['value'].mean()),
                "std": float(df['value'].std()),
                "min": float(df['value'].min()),
                "max": float(df['value'].max()),
                "count": len(df)
            }
            
            # トレンド分析
            trend = self._calculate_trend(df['value'])
            
            # 季節性分析
            seasonality = self._detect_seasonality(df['value'])
            
            # 異常値検出
            anomalies = self._detect_anomalies(df['value'])
            
            return {
                "metric": metric_name,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "granularity": granularity
                },
                "statistics": basic_stats,
                "trend": trend,
                "seasonality": seasonality,
                "anomalies": anomalies,
                "data_points": len(df)
            }
            
        except Exception as e:
            logger.error(f"時系列分析エラー: {e}")
            return {"error": str(e)}
    
    def correlation_analysis(self, metrics: List[str], 
                           start_date: datetime,
                           end_date: datetime) -> Dict[str, Any]:
        """相関分析"""
        try:
            # 複数メトリクスのデータ取得
            data_frames = []
            for metric in metrics:
                data = self.metrics_aggregator.get_metric_data(
                    metric, start_date, end_date, "hour"
                )
                if data:
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')  # 数値変換
                    df.set_index('timestamp', inplace=True)
                    df.rename(columns={'value': metric}, inplace=True)
                    # NaN値を除去
                    df = df.dropna()
                    if not df.empty:
                        data_frames.append(df)
            
            if len(data_frames) < 2:
                return {"error": "Insufficient data for correlation analysis"}
            
            # データ結合
            combined_df = pd.concat(data_frames, axis=1, join='inner')
            
            # 相関行列計算
            correlation_matrix = combined_df.corr()
            
            # 統計的有意性テスト
            p_values = self._calculate_correlation_pvalues(combined_df)
            
            # 強い相関の検出
            strong_correlations = self._find_strong_correlations(
                correlation_matrix, p_values
            )
            
            return {
                "metrics": metrics,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "correlation_matrix": correlation_matrix.to_dict(),
                "p_values": p_values,
                "strong_correlations": strong_correlations,
                "data_points": len(combined_df)
            }
            
        except Exception as e:
            logger.error(f"相関分析エラー: {e}")
            return {"error": str(e)}
    
    def anomaly_detection(self, metric_name: str,
                         start_date: datetime,
                         end_date: datetime,
                         sensitivity: float = 2.0) -> Dict[str, Any]:
        """異常検知"""
        try:
            # データ取得
            data = self.metrics_aggregator.get_metric_data(
                metric_name, start_date, end_date, "minute"
            )
            
            if not data:
                return {"error": "No data available for anomaly detection"}
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 複数の異常検知手法を適用
            anomalies = {
                "statistical": self._statistical_anomaly_detection(
                    df['value'], sensitivity
                ),
                "isolation_forest": self._isolation_forest_detection(
                    df['value']
                ),
                "rolling_std": self._rolling_std_detection(
                    df['value'], sensitivity
                )
            }
            
            # 統合スコア計算
            combined_anomalies = self._combine_anomaly_scores(anomalies, df.index)
            
            return {
                "metric": metric_name,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "sensitivity": sensitivity,
                "anomalies": combined_anomalies,
                "summary": {
                    "total_points": len(df),
                    "anomaly_count": len(combined_anomalies),
                    "anomaly_rate": len(combined_anomalies) / len(df)
                }
            }
            
        except Exception as e:
            logger.error(f"異常検知エラー: {e}")
            return {"error": str(e)}
    
    def trend_prediction(self, metric_name: str,
                        historical_days: int = 30,
                        forecast_days: int = 7) -> Dict[str, Any]:
        """トレンド予測"""
        try:
            # 履歴データ取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=historical_days)
            
            data = self.metrics_aggregator.get_metric_data(
                metric_name, start_date, end_date, "hour"
            )
            
            if not data or len(data) < 24:  # 最低1日分のデータが必要
                return {"error": "Insufficient historical data for prediction"}
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # トレンド分解
            trend_components = self._decompose_time_series(df['value'])
            
            # 予測モデル適用
            predictions = self._apply_prediction_models(
                df['value'], forecast_days
            )
            
            # 信頼区間計算
            confidence_intervals = self._calculate_confidence_intervals(
                predictions, df['value']
            )
            
            return {
                "metric": metric_name,
                "historical_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": historical_days
                },
                "forecast_period": {
                    "start": end_date.isoformat(),
                    "end": (end_date + timedelta(days=forecast_days)).isoformat(),
                    "days": forecast_days
                },
                "trend_components": trend_components,
                "predictions": predictions,
                "confidence_intervals": confidence_intervals,
                "model_accuracy": self._evaluate_model_accuracy(df['value'])
            }
            
        except Exception as e:
            logger.error(f"トレンド予測エラー: {e}")
            return {"error": str(e)}
    
    def performance_insights(self) -> Dict[str, Any]:
        """パフォーマンスインサイト生成"""
        try:
            # 各賢者のパフォーマンスデータ収集
            sage_metrics = {
                "knowledge_sage": self._get_sage_performance("knowledge"),
                "task_sage": self._get_sage_performance("task"),
                "incident_sage": self._get_sage_performance("incident"),
                "rag_sage": self._get_sage_performance("rag")
            }
            
            # システム全体のパフォーマンス
            system_metrics = self._get_system_performance()
            
            # インサイト生成
            insights = self._generate_insights(sage_metrics, system_metrics)
            
            # 推奨アクション
            recommendations = self._generate_recommendations(
                sage_metrics, system_metrics, insights
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "sage_performance": sage_metrics,
                "system_performance": system_metrics,
                "insights": insights,
                "recommendations": recommendations,
                "health_score": self._calculate_health_score(
                    sage_metrics, system_metrics
                )
            }
            
        except Exception as e:
            logger.error(f"パフォーマンスインサイト生成エラー: {e}")
            return {"error": str(e)}
    
    # プライベートメソッド
    def _calculate_trend(self, series: pd.Series) -> Dict[str, Any]:
        """トレンド計算"""
        x = np.arange(len(series))
        y = series.values
        
        # 線形回帰
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            "direction": "increasing" if slope > 0 else "decreasing",
            "slope": float(slope),
            "strength": float(abs(r_value)),
            "p_value": float(p_value)
        }
    
    def _detect_seasonality(self, series: pd.Series) -> Dict[str, Any]:
        """季節性検出"""
        # 簡略版: 自己相関を使用
        if len(series) < 48:  # 2日分未満
            return {"detected": False, "period": None}
        
        # 自己相関計算
        acf_values = [series.autocorr(lag) for lag in range(1, min(25, len(series)//2))]
        
        # ピーク検出
        peaks = []
        for i in range(1, len(acf_values)-1):
            if acf_values[i] > acf_values[i-1] and acf_values[i] > acf_values[i+1]:
                if acf_values[i] > 0.5:  # 閾値
                    peaks.append(i+1)
        
        if peaks:
            return {
                "detected": True,
                "period": peaks[0],
                "strength": float(max(acf_values))
            }
        else:
            return {"detected": False, "period": None}
    
    def _detect_anomalies(self, series: pd.Series) -> List[Dict[str, Any]]:
        """異常値検出"""
        anomalies = []
        
        # Z-score法
        z_scores = np.abs(stats.zscore(series))
        threshold = 3
        
        for i, (timestamp, value) in enumerate(series.items()):
            if z_scores[i] > threshold:
                anomalies.append({
                    "timestamp": timestamp.isoformat(),
                    "value": float(value),
                    "z_score": float(z_scores[i]),
                    "severity": "high" if z_scores[i] > 4 else "medium"
                })
        
        return anomalies
    
    def _calculate_correlation_pvalues(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """相関係数のp値計算"""
        p_values = {}
        columns = df.columns
        
        for i, col1 in enumerate(columns):
            p_values[col1] = {}
            for j, col2 in enumerate(columns):
                if i != j:
                    _, p_value = stats.pearsonr(df[col1], df[col2])
                    p_values[col1][col2] = float(p_value)
                else:
                    p_values[col1][col2] = 0.0
        
        return p_values
    
    def _find_strong_correlations(self, corr_matrix: pd.DataFrame, 
                                 p_values: Dict) -> List[Dict[str, Any]]:
        """強い相関の検出"""
        strong_correlations = []
        threshold = 0.7
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if abs(corr_value) > threshold:
                    strong_correlations.append({
                        "metric1": col1,
                        "metric2": col2,
                        "correlation": float(corr_value),
                        "p_value": p_values[col1][col2],
                        "strength": "very_strong" if abs(corr_value) > 0.9 else "strong"
                    })
        
        return strong_correlations
    
    def _statistical_anomaly_detection(self, series: pd.Series, 
                                     sensitivity: float) -> List[int]:
        """統計的異常検知"""
        mean = series.mean()
        std = series.std()
        threshold = sensitivity * std
        
        anomalies = []
        for i, value in enumerate(series):
            if abs(value - mean) > threshold:
                anomalies.append(i)
        
        return anomalies
    
    def _isolation_forest_detection(self, series: pd.Series) -> List[int]:
        """Isolation Forest（簡略版）"""
        # 実際の実装では scikit-learn の IsolationForest を使用
        # ここでは四分位範囲を使った簡略版
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        anomalies = []
        for i, value in enumerate(series):
            if value < Q1 - 1.5 * IQR or value > Q3 + 1.5 * IQR:
                anomalies.append(i)
        
        return anomalies
    
    def _rolling_std_detection(self, series: pd.Series, 
                              sensitivity: float) -> List[int]:
        """ローリング標準偏差による検知"""
        window = min(24, len(series) // 10)  # 24時間または10%
        rolling_mean = series.rolling(window=window, center=True).mean()
        rolling_std = series.rolling(window=window, center=True).std()
        
        anomalies = []
        for i in range(len(series)):
            if pd.notna(rolling_mean.iloc[i]) and pd.notna(rolling_std.iloc[i]):
                if abs(series.iloc[i] - rolling_mean.iloc[i]) > sensitivity * rolling_std.iloc[i]:
                    anomalies.append(i)
        
        return anomalies
    
    def _combine_anomaly_scores(self, anomaly_methods: Dict[str, List[int]], 
                               timestamps: pd.DatetimeIndex) -> List[Dict[str, Any]]:
        """異常スコア統合"""
        # 各手法で検出された異常をカウント
        anomaly_counts = {}
        for method, indices in anomaly_methods.items():
            for idx in indices:
                if idx not in anomaly_counts:
                    anomaly_counts[idx] = 0
                anomaly_counts[idx] += 1
        
        # 複数の手法で検出されたものを異常とする
        combined_anomalies = []
        for idx, count in anomaly_counts.items():
            if count >= 2:  # 2つ以上の手法で検出
                combined_anomalies.append({
                    "timestamp": timestamps[idx].isoformat(),
                    "detection_count": count,
                    "confidence": count / len(anomaly_methods)
                })
        
        return combined_anomalies
    
    def _decompose_time_series(self, series: pd.Series) -> Dict[str, Any]:
        """時系列分解（簡略版）"""
        # 実際の実装では statsmodels.tsa.seasonal を使用
        # ここでは移動平均によるトレンド抽出
        window = min(24, len(series) // 10)
        trend = series.rolling(window=window, center=True).mean()
        
        # 季節性成分（簡略版）
        detrended = series - trend
        seasonal = detrended.groupby(detrended.index.hour).mean()
        
        # 残差
        residual = series - trend
        
        return {
            "trend": {
                "values": trend.dropna().tolist()[-10:],  # 最新10点
                "direction": "increasing" if trend.iloc[-1] > trend.iloc[0] else "decreasing"
            },
            "seasonal": {
                "pattern": seasonal.to_dict(),
                "strength": float(seasonal.std() / series.std())
            },
            "residual": {
                "std": float(residual.dropna().std()),
                "mean": float(residual.dropna().mean())
            }
        }
    
    def _apply_prediction_models(self, series: pd.Series, 
                                forecast_days: int) -> Dict[str, List[float]]:
        """予測モデル適用（簡略版）"""
        forecast_points = forecast_days * 24  # 時間単位
        
        # 線形トレンド予測
        x = np.arange(len(series))
        y = series.values
        slope, intercept = np.polyfit(x, y, 1)
        
        future_x = np.arange(len(series), len(series) + forecast_points)
        linear_forecast = slope * future_x + intercept
        
        # 移動平均予測
        ma_window = min(24, len(series) // 10)
        ma_forecast = [series.rolling(window=ma_window).mean().iloc[-1]] * forecast_points
        
        # 最終値継続予測（ベースライン）
        naive_forecast = [series.iloc[-1]] * forecast_points
        
        return {
            "linear": linear_forecast.tolist(),
            "moving_average": ma_forecast,
            "naive": naive_forecast
        }
    
    def _calculate_confidence_intervals(self, predictions: Dict[str, List[float]], 
                                      historical: pd.Series) -> Dict[str, Dict[str, List[float]]]:
        """信頼区間計算"""
        # 履歴データの標準偏差を使用
        std = historical.std()
        
        confidence_intervals = {}
        for model, forecast in predictions.items():
            confidence_intervals[model] = {
                "upper_95": [v + 1.96 * std for v in forecast],
                "lower_95": [v - 1.96 * std for v in forecast],
                "upper_68": [v + std for v in forecast],
                "lower_68": [v - std for v in forecast]
            }
        
        return confidence_intervals
    
    def _evaluate_model_accuracy(self, series: pd.Series) -> Dict[str, float]:
        """モデル精度評価（バックテスト）"""
        if len(series) < 48:
            return {"error": "Insufficient data for evaluation"}
        
        # 訓練・テスト分割
        split_point = int(len(series) * 0.8)
        train = series[:split_point]
        test = series[split_point:]
        
        # 簡易予測
        naive_pred = [train.iloc[-1]] * len(test)
        ma_pred = [train.rolling(window=24).mean().iloc[-1]] * len(test)
        
        # RMSE計算
        naive_rmse = np.sqrt(np.mean((test.values - naive_pred) ** 2))
        ma_rmse = np.sqrt(np.mean((test.values - ma_pred) ** 2))
        
        return {
            "naive_rmse": float(naive_rmse),
            "moving_average_rmse": float(ma_rmse),
            "baseline_mae": float(np.mean(np.abs(test.values - naive_pred)))
        }
    
    def _get_sage_performance(self, sage_type: str) -> Dict[str, Any]:
        """賢者パフォーマンス取得"""
        # モックデータ（実際は各賢者のAPIから取得）
        base_performance = {
            "knowledge": {"speed": 95, "accuracy": 98, "availability": 99.5},
            "task": {"speed": 92, "accuracy": 96, "availability": 99.0},
            "incident": {"speed": 98, "accuracy": 99, "availability": 99.9},
            "rag": {"speed": 90, "accuracy": 95, "availability": 98.5}
        }
        
        performance = base_performance.get(sage_type, {})
        
        # ランダムな変動を追加
        import random
        for key in performance:
            performance[key] += random.uniform(-2, 2)
        
        return performance
    
    def _get_system_performance(self) -> Dict[str, Any]:
        """システム全体のパフォーマンス"""
        return {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_io": 78.5,
            "network_throughput": 125.6,
            "response_time": 85.3,
            "error_rate": 0.02,
            "throughput": 1250
        }
    
    def _generate_insights(self, sage_metrics: Dict, 
                          system_metrics: Dict) -> List[Dict[str, Any]]:
        """インサイト生成"""
        insights = []
        
        # 賢者パフォーマンス分析
        for sage, metrics in sage_metrics.items():
            if metrics.get("speed", 100) < 85:
                insights.append({
                    "type": "performance",
                    "severity": "warning",
                    "component": sage,
                    "message": f"{sage}の処理速度が低下しています",
                    "metric": "speed",
                    "value": metrics["speed"]
                })
        
        # システムリソース分析
        if system_metrics["cpu_usage"] > 80:
            insights.append({
                "type": "resource",
                "severity": "warning",
                "component": "system",
                "message": "CPU使用率が高くなっています",
                "metric": "cpu_usage",
                "value": system_metrics["cpu_usage"]
            })
        
        # エラー率分析
        if system_metrics["error_rate"] > 0.05:
            insights.append({
                "type": "reliability",
                "severity": "critical",
                "component": "system",
                "message": "エラー率が閾値を超えています",
                "metric": "error_rate",
                "value": system_metrics["error_rate"]
            })
        
        return insights
    
    def _generate_recommendations(self, sage_metrics: Dict, 
                                 system_metrics: Dict,
                                 insights: List) -> List[Dict[str, Any]]:
        """推奨アクション生成"""
        recommendations = []
        
        # インサイトに基づく推奨
        for insight in insights:
            if insight["type"] == "performance" and insight["severity"] == "warning":
                recommendations.append({
                    "priority": "high",
                    "action": "scale_up",
                    "target": insight["component"],
                    "reason": insight["message"],
                    "expected_improvement": "20-30%"
                })
            
            elif insight["type"] == "resource" and insight["component"] == "system":
                recommendations.append({
                    "priority": "medium",
                    "action": "optimize_queries",
                    "target": "database",
                    "reason": "リソース使用量削減",
                    "expected_improvement": "15-25%"
                })
        
        return recommendations
    
    def _calculate_health_score(self, sage_metrics: Dict, 
                               system_metrics: Dict) -> float:
        """ヘルススコア計算"""
        scores = []
        
        # 賢者スコア
        for sage, metrics in sage_metrics.items():
            sage_score = (
                metrics.get("speed", 0) * 0.3 +
                metrics.get("accuracy", 0) * 0.5 +
                metrics.get("availability", 0) * 0.2
            )
            scores.append(sage_score)
        
        # システムスコア
        system_score = 100 - (
            max(0, system_metrics["cpu_usage"] - 50) * 0.5 +
            max(0, system_metrics["memory_usage"] - 50) * 0.3 +
            system_metrics["error_rate"] * 200
        )
        scores.append(system_score)
        
        # 総合スコア
        return float(np.mean(scores))

# エンジンインスタンス
analytics_engine = AdvancedAnalyticsEngine()

# API エンドポイント

@analytics_api.route('/time-series/<metric_name>')
def analyze_time_series(metric_name):
    """時系列分析エンドポイント"""
    try:
        # パラメータ取得
        days = int(request.args.get('days', 7))
        granularity = request.args.get('granularity', 'hour')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        result = analytics_engine.time_series_analysis(
            metric_name, start_date, end_date, granularity
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_api.route('/correlation', methods=['POST'])
def analyze_correlation():
    """相関分析エンドポイント"""
    try:
        data = request.json
        metrics = data.get('metrics', [])
        days = data.get('days', 7)
        
        if len(metrics) < 2:
            return jsonify({"error": "At least 2 metrics required"}), 400
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        result = analytics_engine.correlation_analysis(
            metrics, start_date, end_date
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_api.route('/anomalies/<metric_name>')
def detect_anomalies(metric_name):
    """異常検知エンドポイント"""
    try:
        days = int(request.args.get('days', 1))
        sensitivity = float(request.args.get('sensitivity', 2.0))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        result = analytics_engine.anomaly_detection(
            metric_name, start_date, end_date, sensitivity
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_api.route('/predict/<metric_name>')
def predict_trend(metric_name):
    """トレンド予測エンドポイント"""
    try:
        historical_days = int(request.args.get('historical_days', 30))
        forecast_days = int(request.args.get('forecast_days', 7))
        
        result = analytics_engine.trend_prediction(
            metric_name, historical_days, forecast_days
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_api.route('/insights')
def get_performance_insights():
    """パフォーマンスインサイトエンドポイント"""
    try:
        result = analytics_engine.performance_insights()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analytics_api.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({
        "status": "healthy",
        "service": "analytics_engine",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    # テスト用実行
    app = Flask(__name__)
    app.register_blueprint(analytics_api)
    
    print("=== 高度分析エンジン API ===")
    print("エンドポイント:")
    print("- GET  /api/analytics/time-series/<metric>")
    print("- POST /api/analytics/correlation")
    print("- GET  /api/analytics/anomalies/<metric>")
    print("- GET  /api/analytics/predict/<metric>")
    print("- GET  /api/analytics/insights")
    
    app.run(debug=True, port=5005)
#!/usr/bin/env python3
"""
Predictive Incident Management System
エルダーズギルド 予測的インシデント管理システム

Created by Claude Elder
Version: 1.0.0
"""

import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """インシデント重要度"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class PredictionConfidence(Enum):
    """予測信頼度"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class IncidentPattern:
    """インシデントパターン"""
    pattern_id: str
    name: str
    features: Dict[str, float]
    severity: IncidentSeverity
    frequency: float
    last_occurrence: Optional[datetime] = None
    prevention_actions: List[str] = field(default_factory=list)

@dataclass
class PredictionResult:
    """予測結果"""
    incident_type: str
    probability: float
    confidence: PredictionConfidence
    time_window: str
    severity: IncidentSeverity
    recommended_actions: List[str]
    reasoning: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class IncidentMetrics:
    """インシデントメトリクス"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_latency: float = 0.0
    error_rate: float = 0.0
    response_time: float = 0.0
    active_connections: int = 0
    queue_length: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

class IncidentPredictor:
    """インシデント予測エンジン"""

    def __init__(self, model_path: str = "incident_prediction_model.pkl"):
        self.model_path = Path(model_path)
        self.patterns: Dict[str, IncidentPattern] = {}
        self.historical_data: List[IncidentMetrics] = []
        self.predictions: List[PredictionResult] = []
        self.load_patterns()

    def add_pattern(self, pattern: IncidentPattern):
        """パターンを追加"""
        self.patterns[pattern.pattern_id] = pattern
        logger.info(f"Added incident pattern: {pattern.name}")

    def collect_metrics(self) -> IncidentMetrics:
        """現在のシステムメトリクス収集"""
        try:
            import psutil

            # システムメトリクス取得
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # ネットワークメトリクス（簡易版）
            network_latency = self._measure_network_latency()

            # プロセスメトリクス
            active_connections = len(psutil.net_connections())

            metrics = IncidentMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_latency=network_latency,
                active_connections=active_connections
            )

            # 履歴に追加（最大1000件保持）
            self.historical_data.append(metrics)
            if len(self.historical_data) > 1000:
                self.historical_data.pop(0)

            return metrics

        except ImportError:
            logger.warning("psutil not installed, using mock metrics")
            return IncidentMetrics(
                cpu_usage=np.random.uniform(10, 30),
                memory_usage=np.random.uniform(40, 60),
                disk_usage=np.random.uniform(20, 40),
                network_latency=np.random.uniform(10, 50),
                active_connections=np.random.randint(50, 200)
            )

    def _measure_network_latency(self) -> float:
        """ネットワーク遅延測定"""
        try:
            import subprocess
            result = subprocess.run(['ping', '-c', '1', 'localhost'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # ping結果から遅延を抽出
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'time=' in line:
                        time_str = line.split('time=')[1].split(' ')[0]
                        return float(time_str)
            return 0.0
        except:
            return np.random.uniform(1, 10)

    def analyze_trends(self, window_hours: int = 24) -> Dict[str, Any]:
        """トレンド分析"""
        if len(self.historical_data) < 10:
            return {"status": "insufficient_data"}

        # 指定時間窓内のデータを取得
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        recent_data = [m for m in self.historical_data if m.timestamp >= cutoff_time]

        if not recent_data:
            return {"status": "no_recent_data"}

        # トレンド計算
        cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_data])
        memory_trend = self._calculate_trend([m.memory_usage for m in recent_data])
        disk_trend = self._calculate_trend([m.disk_usage for m in recent_data])
        latency_trend = self._calculate_trend([m.network_latency for m in recent_data])

        return {
            "status": "analyzed",
            "window_hours": window_hours,
            "data_points": len(recent_data),
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend,
                "disk": disk_trend,
                "network_latency": latency_trend
            },
            "analysis_time": datetime.now().isoformat()
        }

    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """トレンド計算"""
        if len(values) < 2:
            return {"direction": 0.0, "rate": 0.0, "volatility": 0.0}

        # 線形回帰でトレンド方向を計算
        x = np.arange(len(values))
        z = np.polyfit(x, values, 1)
        direction = z[0]  # 傾き

        # 変動率計算
        volatility = np.std(values)

        return {
            "direction": float(direction),
            "rate": abs(float(direction)),
            "volatility": float(volatility),
            "current": float(values[-1]),
            "average": float(np.mean(values))
        }

    def predict_incidents(self, forecast_hours: int = 6) -> List[PredictionResult]:
        """インシデント予測実行"""
        predictions = []
        current_metrics = self.collect_metrics()
        trends = self.analyze_trends()

        # 各パターンについて予測
        for pattern in self.patterns.values():
            prediction = self._evaluate_pattern(pattern, current_metrics, trends, forecast_hours)
            if prediction:
                predictions.append(prediction)

        # 緊急度でソート
        predictions.sort(key=lambda p: (p.severity.value, p.probability), reverse=True)

        # 予測履歴に追加
        self.predictions.extend(predictions)

        return predictions

    def _evaluate_pattern(self, pattern: IncidentPattern, metrics: IncidentMetrics,
                         trends: Dict[str, Any], forecast_hours: int) -> Optional[PredictionResult]:
        """パターン評価"""
        # 特徴量マッチング
        match_score = 0.0
        feature_count = 0

        for feature_name, threshold in pattern.features.items():
            current_value = getattr(metrics, feature_name, 0.0)

            # 閾値との比較
            if current_value >= threshold:
                match_score += 1.0
            else:
                match_score += max(0.0, current_value / threshold)

            feature_count += 1

        if feature_count == 0:
            return None

        # マッチスコア正規化
        match_score = match_score / feature_count

        # トレンド影響を考慮
        trend_impact = self._calculate_trend_impact(trends, pattern)

        # 最終確率計算
        probability = min(0.99, match_score * 0.7 + trend_impact * 0.3)

        # 予測閾値チェック
        if probability < 0.3:
            return None

        # 信頼度決定
        confidence = self._determine_confidence(probability, len(self.historical_data))

        # 推奨アクション生成
        actions = self._generate_recommendations(pattern, probability, trends)

        # 理由説明生成
        reasoning = self._generate_reasoning(pattern, match_score, trend_impact, metrics)

        return PredictionResult(
            incident_type=pattern.name,
            probability=probability,
            confidence=confidence,
            time_window=f"next {forecast_hours} hours",
            severity=pattern.severity,
            recommended_actions=actions,
            reasoning=reasoning
        )

    def _calculate_trend_impact(self, trends: Dict[str, Any], pattern: IncidentPattern) -> float:
        """トレンド影響計算"""
        if trends.get("status") != "analyzed":
            return 0.0

        trend_data = trends.get("trends", {})
        impact = 0.0

        # CPU使用率が高まっている場合
        cpu_trend = trend_data.get("cpu", {})
        if cpu_trend.get("direction", 0) > 0 and "cpu_usage" in pattern.features:
            impact += min(0.3, cpu_trend.get("rate", 0) / 10)

        # メモリ使用率が高まっている場合
        memory_trend = trend_data.get("memory", {})
        if memory_trend.get("direction", 0) > 0 and "memory_usage" in pattern.features:
            impact += min(0.3, memory_trend.get("rate", 0) / 10)

        # ネットワーク遅延が増加している場合
        latency_trend = trend_data.get("network_latency", {})
        if latency_trend.get("direction", 0) > 0 and "network_latency" in pattern.features:
            impact += min(0.2, latency_trend.get("rate", 0) / 5)

        return min(1.0, impact)

    def _determine_confidence(self, probability: float, data_points: int) -> PredictionConfidence:
        """信頼度決定"""
        # データ量による信頼度調整
        data_factor = min(1.0, data_points / 100)
        adjusted_confidence = probability * data_factor

        if adjusted_confidence >= 0.9:
            return PredictionConfidence.VERY_HIGH
        elif adjusted_confidence >= 0.7:
            return PredictionConfidence.HIGH
        elif adjusted_confidence >= 0.5:
            return PredictionConfidence.MEDIUM
        elif adjusted_confidence >= 0.3:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW

    def _generate_recommendations(self, pattern: IncidentPattern, probability: float,
                                trends: Dict[str, Any]) -> List[str]:
        """推奨アクション生成"""
        actions = pattern.prevention_actions.copy()

        # 確率に基づく追加アクション
        if probability > 0.8:
            actions.append("Immediate monitoring increase required")
            actions.append("Prepare incident response team")
        elif probability > 0.6:
            actions.append("Enhanced system monitoring recommended")
            actions.append("Review resource allocation")

        # トレンドに基づく追加アクション
        if trends.get("status") == "analyzed":
            trend_data = trends.get("trends", {})

            cpu_trend = trend_data.get("cpu", {})
            if cpu_trend.get("direction", 0) > 5:
                actions.append("Scale CPU resources or optimize processes")

            memory_trend = trend_data.get("memory", {})
            if memory_trend.get("direction", 0) > 5:
                actions.append("Investigate memory leaks or scale memory")

            disk_trend = trend_data.get("disk", {})
            if disk_trend.get("direction", 0) > 2:
                actions.append("Clean up disk space or expand storage")

        return list(set(actions))  # 重複削除

    def _generate_reasoning(self, pattern: IncidentPattern, match_score: float,
                          trend_impact: float, metrics: IncidentMetrics) -> str:
        """理由説明生成"""
        reasons = []

        # パターンマッチング理由
        reasons.append(f"Pattern '{pattern.name}' matched with {match_score:.1%} similarity")

        # 現在のメトリクス状況
        critical_metrics = []
        if metrics.cpu_usage > 80:
            critical_metrics.append(f"CPU usage at {metrics.cpu_usage:.1f}%")
        if metrics.memory_usage > 85:
            critical_metrics.append(f"Memory usage at {metrics.memory_usage:.1f}%")
        if metrics.disk_usage > 90:
            critical_metrics.append(f"Disk usage at {metrics.disk_usage:.1f}%")
        if metrics.network_latency > 100:
            critical_metrics.append(f"Network latency at {metrics.network_latency:.1f}ms")

        if critical_metrics:
            reasons.append("Critical metrics: " + ", ".join(critical_metrics))

        # トレンド影響
        if trend_impact > 0.1:
            reasons.append(f"Negative trend impact: {trend_impact:.1%}")

        return ". ".join(reasons)

    def load_patterns(self):
        """パターンをロード"""
        # デフォルトパターンを定義
        default_patterns = [
            IncidentPattern(
                pattern_id="high_cpu_usage",
                name="High CPU Usage Incident",
                features={"cpu_usage": 85.0, "response_time": 500.0},
                severity=IncidentSeverity.HIGH,
                frequency=0.3,
                prevention_actions=[
                    "Scale CPU resources",
                    "Optimize high-CPU processes",
                    "Implement CPU throttling"
                ]
            ),
            IncidentPattern(
                pattern_id="memory_leak",
                name="Memory Leak Detection",
                features={"memory_usage": 90.0},
                severity=IncidentSeverity.CRITICAL,
                frequency=0.2,
                prevention_actions=[
                    "Restart affected services",
                    "Investigate memory leaks",
                    "Implement memory monitoring"
                ]
            ),
            IncidentPattern(
                pattern_id="disk_space_exhaustion",
                name="Disk Space Exhaustion",
                features={"disk_usage": 95.0},
                severity=IncidentSeverity.EMERGENCY,
                frequency=0.15,
                prevention_actions=[
                    "Clean temporary files",
                    "Expand disk capacity",
                    "Implement log rotation"
                ]
            ),
            IncidentPattern(
                pattern_id="network_degradation",
                name="Network Performance Degradation",
                features={"network_latency": 200.0, "error_rate": 5.0},
                severity=IncidentSeverity.MEDIUM,
                frequency=0.4,
                prevention_actions=[
                    "Check network configuration",
                    "Restart network services",
                    "Investigate bandwidth usage"
                ]
            )
        ]

        # パターンを追加
        for pattern in default_patterns:
            self.add_pattern(pattern)

        # 保存されたパターンがあれば読み込み
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    saved_patterns = pickle.load(f)
                    self.patterns.update(saved_patterns)
                logger.info(f"Loaded {len(saved_patterns)} saved patterns")
            except Exception as e:
                logger.error(f"Failed to load saved patterns: {e}")

    def save_patterns(self):
        """パターンを保存"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.patterns, f)
            logger.info("Patterns saved successfully")
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")

class PredictiveIncidentManager:
    """予測的インシデント管理システム"""

    def __init__(self):
        self.predictor = IncidentPredictor()
        self.logger = logging.getLogger(__name__)
        self.active_predictions: List[PredictionResult] = []
        self.monitoring_active = False

    async def start_monitoring(self, interval_minutes: int = 10):
        """監視開始"""
        self.monitoring_active = True
        self.logger.info("Predictive incident monitoring started")

        while self.monitoring_active:
            try:
                # 予測実行
                predictions = self.predictor.predict_incidents()

                # 高リスク予測の処理
                for prediction in predictions:
                    if prediction.probability > 0.7:
                        await self._handle_high_risk_prediction(prediction)

                # アクティブ予測を更新
                self.active_predictions = [p for p in predictions if p.probability > 0.5]

                # 指定間隔で待機
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        self.logger.info("Predictive incident monitoring stopped")

    async def _handle_high_risk_prediction(self, prediction: PredictionResult):
        """高リスク予測の処理"""
        self.logger.warning(f"High risk prediction: {prediction.incident_type} "
                          f"({prediction.probability:.1%} probability)")

        # アラート送信（実装例）
        alert_data = {
            "type": "predictive_incident_alert",
            "incident_type": prediction.incident_type,
            "probability": prediction.probability,
            "severity": prediction.severity.name,
            "actions": prediction.recommended_actions,
            "reasoning": prediction.reasoning,
            "timestamp": prediction.created_at.isoformat()
        }

        # ここで実際のアラートシステムに送信
        await self._send_alert(alert_data)

    async def _send_alert(self, alert_data: Dict[str, Any]):
        """アラート送信"""
        # 実装例：ログ出力、外部システム通知等
        self.logger.critical(f"PREDICTIVE ALERT: {json.dumps(alert_data, indent=2)}")

        # 将来的にはSlack、メール、PagerDuty等への通知実装

    def get_current_status(self) -> Dict[str, Any]:
        """現在の状態取得"""
        return {
            "monitoring_active": self.monitoring_active,
            "active_predictions": len(self.active_predictions),
            "high_risk_predictions": len([p for p in self.active_predictions if p.probability > 0.7]),
            "total_patterns": len(self.predictor.patterns),
            "data_points": len(self.predictor.historical_data),
            "last_prediction": self.active_predictions[0].created_at.isoformat() if self.active_predictions else None
        }

    def get_predictions_summary(self) -> List[Dict[str, Any]]:
        """予測サマリー取得"""
        return [
            {
                "incident_type": p.incident_type,
                "probability": f"{p.probability:.1%}",
                "confidence": p.confidence.name,
                "severity": p.severity.name,
                "time_window": p.time_window,
                "actions_count": len(p.recommended_actions),
                "created_at": p.created_at.isoformat()
            }
            for p in self.active_predictions
        ]

# グローバルインスタンス
predictive_manager = PredictiveIncidentManager()

# 便利な関数
def start_predictive_monitoring(interval_minutes: int = 10):
    """予測監視開始"""
    return asyncio.create_task(predictive_manager.start_monitoring(interval_minutes))

def stop_predictive_monitoring():
    """予測監視停止"""
    predictive_manager.stop_monitoring()

def get_current_predictions() -> List[PredictionResult]:
    """現在の予測取得"""
    return predictive_manager.predictor.predict_incidents()

def get_system_status() -> Dict[str, Any]:
    """システム状態取得"""
    return predictive_manager.get_current_status()

if __name__ == "__main__":
    async def main():
        print("🚨 Predictive Incident Management System")
        print("=" * 50)

        # 現在のメトリクス収集
        metrics = predictive_manager.predictor.collect_metrics()
        print(f"Current Metrics:")
        print(f"  CPU: {metrics.cpu_usage:.1f}%")
        print(f"  Memory: {metrics.memory_usage:.1f}%")
        print(f"  Disk: {metrics.disk_usage:.1f}%")
        print(f"  Network Latency: {metrics.network_latency:.1f}ms")
        print()

        # 予測実行
        print("🔮 Running incident predictions...")
        predictions = get_current_predictions()

        if predictions:
            print(f"Found {len(predictions)} potential incidents:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"  {i}. {pred.incident_type}")
                print(f"     Probability: {pred.probability:.1%}")
                print(f"     Severity: {pred.severity.name}")
                print(f"     Confidence: {pred.confidence.name}")
                print(f"     Actions: {len(pred.recommended_actions)}")
                print()
        else:
            print("✅ No incidents predicted")

        # システム状態
        status = get_system_status()
        print(f"📊 System Status:")
        print(f"  Active Predictions: {status['active_predictions']}")
        print(f"  High Risk: {status['high_risk_predictions']}")
        print(f"  Patterns Loaded: {status['total_patterns']}")
        print(f"  Historical Data: {status['data_points']}")

    asyncio.run(main())

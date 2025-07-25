#!/usr/bin/env python3
"""
🔮 Incident Predictor - インシデント予測システム
Phase 26: Incident Sage統合実装
Created: 2025-07-17
Author: Claude Elder
Version: 1.0.0
"""

import asyncio
import json
import logging
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Elders Legacy Integration
from core.elders_legacy import EldersAILegacy
from libs.four_sages.incident.failure_pattern_detector import (
    FailurePattern,
    FailurePatternDetector,
)
from libs.four_sages.incident.incident_sage import IncidentCategory, IncidentSeverity

logger = logging.getLogger("incident_predictor")


@dataclass
class FeatureVector:
    """特徴量ベクトル"""

    timestamp: datetime
    error_rate: float
    response_time: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_connections: int
    queue_depth: int
    failure_count_1h: int
    failure_count_24h: int
    pattern_match_count: int
    time_of_day: int  # 0-23
    day_of_week: int  # 0-6
    is_business_hours: bool
    recent_deployment: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_array(self) -> np.ndarray:
        """NumPy配列に変換"""
        return np.array(
            [
                self.error_rate,
                self.response_time,
                self.cpu_usage,
                self.memory_usage,
                self.disk_usage,
                self.network_latency,
                self.active_connections,
                self.queue_depth,
                self.failure_count_1h,
                self.failure_count_24h,
                self.pattern_match_count,
                self.time_of_day,
                self.day_of_week,
                int(self.is_business_hours),
                int(self.recent_deployment),
            ]
        )


@dataclass
class PredictionResult:
    """予測結果"""

    risk_score: float  # 0.0-1.0
    risk_level: str  # "low", "medium", "high", "critical"
    incident_probability: Dict[str, float]  # カテゴリ別確率
    severity_probability: Dict[str, float]  # 重要度別確率
    contributing_factors: List[Tuple[str, float]]  # 寄与要因
    recommended_actions: List[str]
    confidence: float
    prediction_timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "incident_probability": self.incident_probability,
            "severity_probability": self.severity_probability,
            "contributing_factors": self.contributing_factors,
            "recommended_actions": self.recommended_actions,
            "confidence": self.confidence,
            "prediction_timestamp": self.prediction_timestamp.isoformat(),
        }


class FeatureExtractor:
    """特徴量抽出器"""

    def __init__(self):
        """初期化メソッド"""
        self.feature_names = [
            "error_rate",
            "response_time",
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "network_latency",
            "active_connections",
            "queue_depth",
            "failure_count_1h",
            "failure_count_24h",
            "pattern_match_count",
            "time_of_day",
            "day_of_week",
            "is_business_hours",
            "recent_deployment",
        ]
        self.scaler = StandardScaler()
        self.is_fitted = False

    def extract(self, state: Dict[str, Any]) -> FeatureVector:
        """状態から特徴量抽出"""
        now = datetime.now()

        # メトリクスから特徴量を抽出
        metrics = state.get("metrics", {})
        history = state.get("history", {})
        patterns = state.get("patterns", [])

        feature = FeatureVector(
            timestamp=now,
            error_rate=metrics.get("error_rate", 0.0),
            response_time=metrics.get("response_time", 0.0),
            cpu_usage=metrics.get("cpu_usage", 0.0),
            memory_usage=metrics.get("memory_usage", 0.0),
            disk_usage=metrics.get("disk_usage", 0.0),
            network_latency=metrics.get("network_latency", 0.0),
            active_connections=metrics.get("active_connections", 0),
            queue_depth=metrics.get("queue_depth", 0),
            failure_count_1h=history.get("failures_1h", 0),
            failure_count_24h=history.get("failures_24h", 0),
            pattern_match_count=len(patterns),
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            is_business_hours=9 <= now.hour <= 17 and now.weekday() < 5,
            recent_deployment=state.get("recent_deployment", False),
        )

        return feature

    def fit_transform(self, features: List[FeatureVector]) -> np.ndarray:
        """特徴量の正規化（訓練時）"""
        X = np.array([f.to_array() for f in features])
        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True
        return X_scaled

    def transform(self, features: List[FeatureVector]) -> np.ndarray:
        """特徴量の正規化（予測時）"""
        if not self.is_fitted:
            raise ValueError("Scaler not fitted yet")
        X = np.array([f.to_array() for f in features])
        return self.scaler.transform(X)

    def get_feature_importance(
        self, importances: np.ndarray
    ) -> List[Tuple[str, float]]:
        """特徴量の重要度を取得"""
        feature_importance = list(zip(self.feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        return feature_importance


class IncidentPredictor(EldersAILegacy):
    """インシデント予測システム"""

    def __init__(self, pattern_detector: FailurePatternDetector):
        """初期化メソッド"""
        super().__init__(name="IncidentPredictor", model_type="prediction-v1")
        self.pattern_detector = pattern_detector
        self.prediction_model = None
        self.severity_model = None
        self.feature_extractor = FeatureExtractor()
        self.model_path = "models/incident_predictor.pkl"
        self.training_history: List[Dict[str, Any]] = []
        self.prediction_cache: Dict[str, PredictionResult] = {}
        self.cache_ttl = 300  # 5分間キャッシュ

        # モデルパラメータ
        self.model_params = {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "random_state": 42,
        }

        # リスクレベル閾値
        self.risk_thresholds = {"low": 0.3, "medium": 0.5, "high": 0.7, "critical": 0.9}

        logger.info("🔮 Incident Predictor initialized")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        request_type = request.get("type", "predict")

        if request_type == "predict":
            return await self._predict_request(request)
        elif request_type == "train":
            return await self._train_request(request)
        elif request_type == "evaluate":
            return await self._evaluate_request(request)
        elif request_type == "get_model_info":
            return await self._get_model_info_request(request)
        else:
            return {"success": False, "error": f"Unknown request type: {request_type}"}

    async def train_model(
        self, historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """予測モデル訓練"""
        try:
            logger.info(f"🎯 Training model with {len(historical_data)} samples")

            # 特徴量とラベルの準備
            features = []
            labels_category = []
            labels_severity = []

            for data in historical_data:
                # 特徴量抽出
                feature = self.feature_extractor.extract(data["state"])
                features.append(feature)

                # ラベル（実際に発生したインシデント）
                incident = data.get("incident", {})
                if incident:
                    labels_category.append(incident.get("category", "system_failure"))
                    labels_severity.append(incident.get("severity", "medium"))
                else:
                    labels_category.append("none")
                    labels_severity.append("none")

            # 特徴量の正規化
            X = self.feature_extractor.fit_transform(features)

            # カテゴリ予測モデル
            X_train_cat, X_test_cat, y_train_cat, y_test_cat = train_test_split(
                X, labels_category, test_size=0.2, random_state=42
            )

            self.prediction_model = RandomForestClassifier(**self.model_params)
            self.prediction_model.fit(X_train_cat, y_train_cat)

            # カテゴリモデル評価
            y_pred_cat = self.prediction_model.predict(X_test_cat)
            cat_accuracy = accuracy_score(y_test_cat, y_pred_cat)

            # 重要度予測モデル
            X_train_sev, X_test_sev, y_train_sev, y_test_sev = train_test_split(
                X, labels_severity, test_size=0.2, random_state=42
            )

            self.severity_model = RandomForestClassifier(**self.model_params)
            self.severity_model.fit(X_train_sev, y_train_sev)

            # 重要度モデル評価
            y_pred_sev = self.severity_model.predict(X_test_sev)
            sev_accuracy = accuracy_score(y_test_sev, y_pred_sev)

            # モデル保存
            await self._save_model()

            # 訓練履歴記録
            training_result = {
                "timestamp": datetime.now().isoformat(),
                "samples": len(historical_data),
                "category_accuracy": float(cat_accuracy),
                "severity_accuracy": float(sev_accuracy),
                "feature_importance": self._get_feature_importance(),
            }
            self.training_history.append(training_result)

            logger.info(
                f"✅ Model training completed - Category: {cat_accuracy:0.2%}, Severity: " \
                    "{sev_accuracy:0.2%}"
            )

            return {"success": True, "training_result": training_result}

        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return {"success": False, "error": str(e)}

    async def predict_incident_risk(
        self, current_state: Dict[str, Any]
    ) -> PredictionResult:
        """インシデントリスク予測"""
        try:
            # キャッシュチェック
            cache_key = self._generate_cache_key(current_state)
            if cache_key in self.prediction_cache:
                cached = self.prediction_cache[cache_key]
                if (
                    datetime.now() - cached.prediction_timestamp
                ).seconds < self.cache_ttl:
                    return cached

            # モデルが訓練されているか確認
            if not self.prediction_model or not self.severity_model:
                # モデルをロード
                loaded = await self._load_model()
                if not loaded:
                    return self._default_prediction()

            # 特徴量抽出
            feature = self.feature_extractor.extract(current_state)
            X = self.feature_extractor.transform([feature])

            # カテゴリ予測
            category_proba = self.prediction_model.predict_proba(X)[0]
            category_classes = self.prediction_model.classes_
            incident_probability = dict(zip(category_classes, category_proba))

            # 重要度予測
            severity_proba = self.severity_model.predict_proba(X)[0]
            severity_classes = self.severity_model.classes_
            severity_probability = dict(zip(severity_classes, severity_proba))

            # リスクスコア計算
            risk_score = self._calculate_risk_score(
                incident_probability, severity_probability
            )

            # リスクレベル判定
            risk_level = self._categorize_risk(risk_score)

            # 寄与要因分析
            contributing_factors = self._analyze_contributing_factors(feature, X)

            # 推奨アクション生成
            recommended_actions = await self._generate_recommendations(
                risk_level, incident_probability, contributing_factors
            )

            # 信頼度計算
            confidence = self._calculate_confidence(category_proba, severity_proba)

            prediction = PredictionResult(
                risk_score=risk_score,
                risk_level=risk_level,
                incident_probability=incident_probability,
                severity_probability=severity_probability,
                contributing_factors=contributing_factors,
                recommended_actions=recommended_actions,
                confidence=confidence,
            )

            # キャッシュに保存
            self.prediction_cache[cache_key] = prediction

            return prediction

        except Exception as e:
            logger.error(f"❌ Incident prediction failed: {e}")
            return self._default_prediction()

    def _calculate_risk_score(
        self, incident_prob: Dict[str, float], severity_prob: Dict[str, float]
    ) -> float:
        """リスクスコア計算"""
        # インシデント発生確率（"none"以外の確率の合計）
        incident_likelihood = 1.0 - incident_prob.get("none", 0.0)

        # 重要度の重み付け
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.3,
            "info": 0.1,
            "none": 0.0,
        }

        weighted_severity = sum(
            severity_prob.get(sev, 0.0) * severity_weights.get(sev, 0.0)
            for sev in severity_weights
        )

        # リスクスコア = 発生確率 × 影響度
        risk_score = incident_likelihood * weighted_severity

        return min(1.0, max(0.0, risk_score))

    def _categorize_risk(self, risk_score: float) -> str:
        """リスクレベル分類"""
        if risk_score >= self.risk_thresholds["critical"]:
            return "critical"
        elif risk_score >= self.risk_thresholds["high"]:
            return "high"
        elif risk_score >= self.risk_thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def _analyze_contributing_factors(
        self, feature: FeatureVector, X: np.ndarray
    ) -> List[Tuple[str, float]]:
        """寄与要因分析"""
        if not self.prediction_model:
            return []

        # 特徴量の重要度を取得
        feature_importance = self.prediction_model.feature_importances_
        factors = self.feature_extractor.get_feature_importance(feature_importance)

        # 現在の値が異常な特徴量を特定
        feature_array = feature.to_array()
        contributing = []

        for i, (name, importance) in enumerate(factors[:10]):  # 上位10個
            value = feature_array[i]

            # 閾値を超えている特徴量を寄与要因として記録
            if name == "error_rate" and value > 0.05:
                contributing.append((f"High error rate: {value:0.2%}", importance))
            elif name == "response_time" and value > 5.0:
                contributing.append((f"Slow response time: {value:0.1f}s", importance))
            elif name == "cpu_usage" and value > 80:
                contributing.append((f"High CPU usage: {value:0.1f}%", importance))
            elif name == "memory_usage" and value > 80:
                contributing.append((f"High memory usage: {value:0.1f}%", importance))
            elif name == "failure_count_1h" and value > 10:
                contributing.append(
                    (f"Recent failures: {int(value)} in 1h", importance)
                )

        return contributing[:5]  # 上位5つの要因

    async def _generate_recommendations(
        self,
        risk_level: str,
        incident_prob: Dict[str, float],
        factors: List[Tuple[str, float]],
    ) -> List[str]:
        """推奨アクション生成"""
        recommendations = []

        # リスクレベルに基づく基本推奨
        if risk_level in ["critical", "high"]:
            recommendations.append("Immediate investigation required")
            recommendations.append("Consider scaling up resources")
            recommendations.append("Enable enhanced monitoring")
        elif risk_level == "medium":
            recommendations.append("Monitor system closely")
            recommendations.append("Review recent changes")

        # 最も可能性の高いインシデントカテゴリに基づく推奨
        likely_category = max(incident_prob.items(), key=lambda x: x[1])[0]
        if likely_category != "none":
            category_recommendations = {
                "system_failure": [
                    "Check system logs for errors",
                    "Verify service health status",
                ],
                "performance_issue": [
                    "Analyze resource utilization",
                    "Check for bottlenecks",
                ],
                "network_issue": ["Test network connectivity", "Check firewall rules"],
                "security_breach": [
                    "Review security logs",
                    "Check for unauthorized access",
                ],
            }
            recommendations.extend(category_recommendations.get(likely_category, []))

        # 寄与要因に基づく推奨
        for factor, _ in factors[:3]:
            if "error rate" in factor:
                recommendations.append("Investigate error sources")
            elif "CPU" in factor:
                recommendations.append("Consider CPU optimization")
            elif "memory" in factor:
                recommendations.append("Check for memory leaks")

        # 重複を削除して返す
        return list(dict.fromkeys(recommendations))[:5]

    def _calculate_confidence(
        self, category_proba: np.ndarray, severity_proba: np.ndarray
    ) -> float:
        """予測信頼度計算"""
        # エントロピーベースの信頼度
        # 確率分布が偏っているほど信頼度が高い

        def entropy(proba):
            """entropyメソッド"""
            # 小さな値を追加してlog(0)を回避
            proba = proba + 1e-10
            return -np.sum(proba * np.log(proba))

        # 最大エントロピーで正規化
        max_entropy_cat = np.log(len(category_proba))
        max_entropy_sev = np.log(len(severity_proba))

        cat_confidence = 1.0 - (entropy(category_proba) / max_entropy_cat)
        sev_confidence = 1.0 - (entropy(severity_proba) / max_entropy_sev)

        # 平均信頼度
        return (cat_confidence + sev_confidence) / 2

    def _get_feature_importance(self) -> List[Tuple[str, float]]:
        """特徴量重要度取得"""
        if not self.prediction_model:
            return []

        importance = self.prediction_model.feature_importances_
        return self.feature_extractor.get_feature_importance(importance)

    def _generate_cache_key(self, state: Dict[str, Any]) -> str:
        """キャッシュキー生成"""
        # 主要なメトリクスからキーを生成
        metrics = state.get("metrics", {})
        key_parts = [
            f"err_{metrics.get('error_rate', 0):0.2f}",
            f"cpu_{metrics.get('cpu_usage', 0):0.0f}",
            f"mem_{metrics.get('memory_usage', 0):0.0f}",
            f"resp_{metrics.get('response_time', 0):0.1f}",
        ]
        return "_".join(key_parts)

    def _default_prediction(self) -> PredictionResult:
        """デフォルト予測（モデルが利用できない場合）"""
        return PredictionResult(
            risk_score=0.0,
            risk_level="low",
            incident_probability={"none": 1.0},
            severity_probability={"none": 1.0},
            contributing_factors=[],
            recommended_actions=["Model not available - manual monitoring required"],
            confidence=0.0,
        )

    async def _save_model(self):
        """モデル保存"""
        try:
            model_data = {
                "prediction_model": self.prediction_model,
                "severity_model": self.severity_model,
                "feature_scaler": self.feature_extractor.scaler,
                "model_params": self.model_params,
                "training_timestamp": datetime.now().isoformat(),
            }

            # ディレクトリ作成
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)

            # pickle形式で保存
            with open(self.model_path, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"✅ Model saved to {self.model_path}")

        except Exception as e:
            logger.error(f"❌ Model save failed: {e}")

    async def _load_model(self) -> bool:
        """モデル読み込み"""
        try:
            if not Path(self.model_path).exists():
                logger.warning(f"⚠️ Model file not found: {self.model_path}")
                return False

            with open(self.model_path, "rb") as f:
                model_data = pickle.load(f)

            self.prediction_model = model_data["prediction_model"]
            self.severity_model = model_data["severity_model"]
            self.feature_extractor.scaler = model_data["feature_scaler"]
            self.feature_extractor.is_fitted = True
            self.model_params = model_data.get("model_params", self.model_params)

            logger.info(f"✅ Model loaded from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Model load failed: {e}")
            return False

    # リクエスト処理メソッド
    async def _predict_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """予測リクエスト処理"""
        current_state = request.get("state", {})

        # パターン検出結果を含める
        patterns = await self.pattern_detector.process_request({"type": "get_patterns"})
        current_state["patterns"] = patterns.get("patterns", [])

        prediction = await self.predict_incident_risk(current_state)

        return {"success": True, "prediction": prediction.to_dict()}

    async def _train_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """訓練リクエスト処理"""
        historical_data = request.get("historical_data", [])

        if not historical_data:
            return {"success": False, "error": "No historical data provided"}

        return await self.train_model(historical_data)

    async def _evaluate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """評価リクエスト処理"""
        test_data = request.get("test_data", [])

        if not test_data or not self.prediction_model:
            return {"success": False, "error": "No test data or model not trained"}

        # 予測実行
        predictions = []
        actuals = []

        for data in test_data:
            prediction = await self.predict_incident_risk(data["state"])
            predictions.append(prediction.risk_level)

            # 実際のインシデント
            incident = data.get("incident", {})
            if incident:
                severity = incident.get("severity", "medium")
                if severity in ["critical", "high"]:
                    actuals.append("high")
                else:
                    actuals.append("low")
            else:
                actuals.append("low")

        # 精度計算
        correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
        accuracy = correct / len(predictions) if predictions else 0

        return {
            "success": True,
            "evaluation": {
                "test_samples": len(test_data),
                "accuracy": accuracy,
                "predictions": predictions[:10],  # 最初の10件
                "actuals": actuals[:10],
            },
        }

    async def _get_model_info_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """モデル情報取得リクエスト処理"""
        if not self.prediction_model:
            return {"success": False, "error": "Model not trained"}

        return {
            "success": True,
            "model_info": {
                "is_trained": self.prediction_model is not None,
                "model_params": self.model_params,
                "feature_importance": self._get_feature_importance(),
                "training_history": self.training_history[-5:],  # 最新5件
                "cache_size": len(self.prediction_cache),
                "risk_thresholds": self.risk_thresholds,
            },
        }

    def get_capabilities(self) -> List[str]:
        """能力一覧"""
        return [
            "incident_risk_prediction",
            "ml_based_forecasting",
            "feature_extraction",
            "pattern_correlation",
            "risk_scoring",
            "confidence_estimation",
            "recommendation_generation",
            "model_training",
            "model_evaluation",
        ]


# エクスポート
__all__ = ["IncidentPredictor", "PredictionResult", "FeatureVector", "FeatureExtractor"]

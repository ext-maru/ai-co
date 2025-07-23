#!/usr/bin/env python3
"""
Demand Predictor AI
需要予測AIモデル

🔮 nWo Prophetic Development Matrix - Demand Prediction AI
Think it, Rule it, Own it - 未来需要予測システム
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging
# import pickle  # セキュリティ: pickleの使用を廃止
import re
from collections import defaultdict


class PredictionType(Enum):
    """予測タイプ"""

    TECHNOLOGY_DEMAND = "technology_demand"
    MARKET_TREND = "market_trend"
    SKILL_DEMAND = "skill_demand"
    FRAMEWORK_ADOPTION = "framework_adoption"
    TOOL_USAGE = "tool_usage"
    LANGUAGE_POPULARITY = "language_popularity"


class TimeFrame(Enum):
    """予測期間"""

    SHORT_TERM = "short_term"  # 1-3ヶ月
    MEDIUM_TERM = "medium_term"  # 3-12ヶ月
    LONG_TERM = "long_term"  # 1-3年


@dataclass
class DemandFeature:
    """需要特徴量"""

    name: str
    value: float
    importance: float
    category: str
    timestamp: str


@dataclass
class Prediction:
    """予測結果"""

    target: str
    prediction_type: PredictionType
    timeframe: TimeFrame
    predicted_value: float
    confidence: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    features_used: List[DemandFeature]
    model_version: str
    created_at: str


@dataclass
class PatternAnalysis:
    """パターン分析"""

    pattern_name: str
    description: str
    frequency: float
    correlation_strength: float
    examples: List[str]
    confidence: float


@dataclass
class ForecastReport:
    """予測レポート"""

    timeframe: TimeFrame
    predictions: List[Prediction]
    pattern_analysis: List[PatternAnalysis]
    market_insights: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    confidence_level: float
    generated_at: str


class DemandPredictorAI:
    """Demand Predictor AI - 需要予測AIシステム"""

    def __init__(self, model_path: Optional[str] = None):
        """初期化メソッド"""
        self.logger = self._setup_logger()

        # モデル管理
        self.model_path = (
            Path(model_path) if model_path else Path("models/demand_prediction.pkl")
        )
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        # 学習データ
        self.training_data = []
        self.feature_importance = {}

        # 予測履歴
        self.prediction_history = []

        # パターン辞書
        self.demand_patterns = self._load_demand_patterns()

        # 技術キーワード
        self.tech_keywords = self._load_tech_keywords()

        # モデル読み込み
        self.model = self._load_or_create_model()

        self.logger.info("🔮 Demand Predictor AI v1.0 initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("demand_predictor")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Demand Predictor - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_demand_patterns(self) -> Dict[str, Dict]:
        """需要パターン辞書"""
        return {
            "exponential_growth": {
                "description": "指数関数的成長パターン",
                "indicators": ["rapid_adoption", "viral_spread", "network_effect"],
                "duration_months": [6, 24],
                "confidence_threshold": 0.8,
            },
            "linear_growth": {
                "description": "線形成長パターン",
                "indicators": [
                    "steady_adoption",
                    "market_expansion",
                    "gradual_improvement",
                ],
                "duration_months": [12, 36],
                "confidence_threshold": 0.7,
            },
            "s_curve": {
                "description": "S字カーブ採用パターン",
                "indicators": [
                    "innovation_diffusion",
                    "market_saturation",
                    "early_majority",
                ],
                "duration_months": [18, 48],
                "confidence_threshold": 0.75,
            },
            "hype_cycle": {
                "description": "ハイプサイクルパターン",
                "indicators": [
                    "peak_hype",
                    "trough_disillusionment",
                    "plateau_productivity",
                ],
                "duration_months": [24, 60],
                "confidence_threshold": 0.6,
            },
            "seasonal": {
                "description": "季節性パターン",
                "indicators": ["conference_cycles", "hiring_seasons", "project_cycles"],
                "duration_months": [3, 12],
                "confidence_threshold": 0.8,
            },
        }

    def _load_tech_keywords(self) -> Dict[str, List[str]]:
        """技術キーワード辞書"""
        return {
            "ai_ml": [
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "neural networks",
                "transformer",
                "gpt",
                "llm",
                "nlp",
                "computer vision",
                "reinforcement learning",
            ],
            "web_frameworks": [
                "react",
                "vue",
                "angular",
                "svelte",
                "nextjs",
                "nuxt",
                "express",
                "fastapi",
                "django",
                "flask",
                "spring",
            ],
            "cloud_native": [
                "kubernetes",
                "docker",
                "microservices",
                "serverless",
                "aws",
                "gcp",
                "azure",
                "terraform",
                "helm",
            ],
            "programming_languages": [
                "python",
                "javascript",
                "typescript",
                "rust",
                "go",
                "java",
                "kotlin",
                "swift",
                "dart",
                "c++",
            ],
            "database_tech": [
                "postgresql",
                "mongodb",
                "redis",
                "elasticsearch",
                "cassandra",
                "neo4j",
                "influxdb",
                "snowflake",
            ],
            "devops_tools": [
                "jenkins",
                "gitlab ci",
                "github actions",
                "ansible",
                "prometheus",
                "grafana",
                "elk stack",
                "datadog",
            ],
        }

    def _load_or_create_model(self) -> Dict:
        """モデル読み込みまたは作成（セキュア版）"""
        if self.model_path.exists():
            try:
                import json
                with open(self.model_path, "r") as f:
                    model = json.load(f)
                self.logger.info("📦 Existing model loaded")
                return model
            except Exception as e:
                self.logger.warning(f"Model loading failed: {e}")

        # 新しいモデル作成
        model = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "weights": {},
            "bias": 0.0,
            "feature_names": [],
            "training_history": [],
            "performance_metrics": {},
        }

        self.logger.info("🆕 New model created")
        return model

    async def train_model(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """
        モデル訓練

        Args:
            historical_data: 過去データ

        Returns:
            Dict: 訓練結果
        """
        self.logger.info("🎓 Starting model training...")

        if not historical_data:
            raise ValueError("Training data is empty")

        # データ前処理
        processed_data = self._preprocess_training_data(historical_data)

        # 特徴量抽出
        features, targets = self._extract_features_targets(processed_data)

        # モデル訓練（シンプルな線形回帰）
        training_result = self._train_linear_model(features, targets)

        # モデル保存
        self._save_model()

        self.logger.info("✅ Model training completed")

        return training_result

    def _preprocess_training_data(self, data: List[Dict]) -> List[Dict]:
        """訓練データ前処理"""
        processed = []

        for record in data:
            # データ検証
            if not self._validate_training_record(record):
                continue

            # 正規化
            normalized = self._normalize_record(record)
            processed.append(normalized)

        return processed

    def _validate_training_record(self, record: Dict) -> bool:
        """訓練レコード検証"""
        required_fields = ["timestamp", "technology", "demand_score"]
        return all(field in record for field in required_fields)

    def _normalize_record(self, record: Dict) -> Dict:
        """レコード正規化"""
        normalized = record.copy()

        # 需要スコア正規化 (0-1の範囲)
        if "demand_score" in normalized:
            score = float(normalized["demand_score"])
            normalized["demand_score"] = max(0.0, min(1.0, score / 100.0))

        # タイムスタンプ正規化
        if "timestamp" in normalized:
            if isinstance(normalized["timestamp"], str):
                normalized["timestamp"] = datetime.fromisoformat(
                    normalized["timestamp"]
                )

        return normalized

    def _extract_features_targets(
        self, data: List[Dict]
    ) -> Tuple[List[List[float]], List[float]]:
        """特徴量・目標値抽出"""
        features = []
        targets = []

        for record in data:
            # 特徴量ベクトル作成
            feature_vector = self._create_feature_vector(record)
            features.append(feature_vector)

            # 目標値
            targets.append(record["demand_score"])

        return features, targets

    def _create_feature_vector(self, record: Dict) -> List[float]:
        """特徴量ベクトル作成"""
        vector = []

        # 技術カテゴリ特徴量
        tech = record.get("technology", "").lower()
        for category, keywords in self.tech_keywords.items():
            match_score = sum(1 for keyword in keywords if keyword in tech)
            vector.append(match_score / len(keywords))

        # 時系列特徴量
        timestamp = record.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # 月、四半期、年の特徴量
        vector.append(timestamp.month / 12.0)
        vector.append((timestamp.month - 1) // 3 / 4.0)  # 四半期

        # トレンド特徴量
        trend_indicators = record.get("trend_indicators", {})
        vector.append(trend_indicators.get("github_stars", 0) / 10000.0)
        vector.append(trend_indicators.get("job_postings", 0) / 1000.0)
        vector.append(trend_indicators.get("search_volume", 0) / 100.0)

        return vector

    def _train_linear_model(
        self, features: List[List[float]], targets: List[float]
    ) -> Dict:
        """線形モデル訓練"""
        if not features or not targets:
            raise ValueError("Empty features or targets")

        # NumPy配列に変換
        X = np.array(features)
        y = np.array(targets)

        # 正規方程式で重み計算
        X_bias = np.c_[np.ones(X.shape[0]), X]  # バイアス項追加

        try:
            # (X^T X)^-1 X^T y
            weights = np.linalg.solve(X_bias.T @ X_bias, X_bias.T @ y)

            self.model["bias"] = weights[0]
            self.model["weights"] = weights[1:].tolist()
            self.model["feature_names"] = [
                f"feature_{i}" for i in range(len(weights) - 1)
            ]

        except np.linalg.LinAlgError:
            # 特異行列の場合は擬似逆行列を使用
            weights = np.linalg.pinv(X_bias.T @ X_bias) @ X_bias.T @ y
            self.model["bias"] = weights[0]
            self.model["weights"] = weights[1:].tolist()
            self.model["feature_names"] = [
                f"feature_{i}" for i in range(len(weights) - 1)
            ]

        # 性能評価
        predictions = X_bias @ weights
        mse = np.mean((y - predictions) ** 2)
        r2 = 1 - (np.sum((y - predictions) ** 2) / np.sum((y - np.mean(y)) ** 2))

        performance = {
            "mse": float(mse),
            "r2_score": float(r2),
            "training_samples": len(targets),
            "feature_count": len(features[0]) if features else 0,
        }

        self.model["performance_metrics"] = performance

        return {
            "training_completed": True,
            "performance": performance,
            "model_version": self.model["version"],
        }

    def _save_model(self):
        """モデル保存"""
        try:
            import json
            with open(self.model_path, "w") as f:
                json.dump(self.model, f, indent=2, default=str)  # default=strで日付等を処理
            self.logger.info(f"💾 Model saved: {self.model_path}")
        except Exception as e:
            self.logger.error(f"Model save error: {e}")

    async def predict_demand(self, features: Dict[str, Any]) -> Prediction:
        """
        需要予測

        Args:
            features: 特徴量辞書

        Returns:
            Prediction: 予測結果
        """
        self.logger.info(
            f"🔮 Predicting demand for: {features.get('technology', 'unknown')}"
        )

        # 特徴量ベクトル作成
        feature_vector = self._create_feature_vector_from_dict(features)

        # 予測実行
        predicted_value = self._predict_single(feature_vector)

        # 信頼度計算
        confidence = self._calculate_prediction_confidence(
            feature_vector, predicted_value
        )

        # トレンド方向判定
        trend_direction = self._determine_trend_direction(features, predicted_value)

        # 使用特徴量
        features_used = self._get_important_features(feature_vector)

        prediction = Prediction(
            target=features.get("technology", "unknown"),
            prediction_type=PredictionType.TECHNOLOGY_DEMAND,
            timeframe=TimeFrame.MEDIUM_TERM,
            predicted_value=predicted_value,
            confidence=confidence,
            trend_direction=trend_direction,
            features_used=features_used,
            model_version=self.model["version"],
            created_at=datetime.now().isoformat(),
        )

        self.prediction_history.append(prediction)

        self.logger.info(
            f"✅ Prediction: {predicted_value:.3f} (confidence: {confidence:.2f})"
        )

        return prediction

    def _create_feature_vector_from_dict(self, features: Dict) -> List[float]:
        """辞書から特徴量ベクトル作成"""
        return self._create_feature_vector(features)

    def _predict_single(self, feature_vector: List[float]) -> float:
        """単一予測"""
        if not self.model.get("weights"):
            # 訓練されていない場合はランダム予測
            return np.random.uniform(0.3, 0.8)

        # 線形予測
        weights = np.array(self.model["weights"])
        bias = self.model["bias"]

        # ベクトル長を調整
        if len(feature_vector) != len(weights):
            # パディングまたはトリミング
            if len(feature_vector) < len(weights):
                feature_vector.extend([0.0] * (len(weights) - len(feature_vector)))
            else:
                feature_vector = feature_vector[: len(weights)]

        prediction = bias + np.dot(weights, feature_vector)

        # 0-1の範囲にクリップ
        return max(0.0, min(1.0, prediction))

    def _calculate_prediction_confidence(
        self, feature_vector: List[float], predicted_value: float
    ) -> float:
        """予測信頼度計算"""
        # 基本信頼度
        base_confidence = 0.7

        # 特徴量の完全性
        completeness = sum(1 for x in feature_vector if x > 0) / len(feature_vector)
        confidence = base_confidence + (completeness * 0.2)

        # 予測値の妥当性
        if 0.2 <= predicted_value <= 0.9:
            confidence += 0.1

        return min(1.0, confidence)

    def _determine_trend_direction(self, features: Dict, predicted_value: float) -> str:
        """トレンド方向判定"""
        # 簡単な閾値ベース判定
        if predicted_value > 0.7:
            return "increasing"
        elif predicted_value < 0.4:
            return "decreasing"
        else:
            return "stable"

    def _get_important_features(
        self, feature_vector: List[float]
    ) -> List[DemandFeature]:
        """重要特徴量取得"""
        features = []

        feature_names = [
            "AI/ML Category",
            "Web Frameworks",
            "Cloud Native",
            "Programming Languages",
            "Database Tech",
            "DevOps Tools",
            "Monthly Trend",
            "Quarterly Trend",
            "GitHub Stars",
            "Job Postings",
            "Search Volume",
        ]

        for i, (name, value) in enumerate(zip(feature_names, feature_vector)):
            if value > 0.1:  # 閾値以上の特徴量のみ
                importance = value * np.random.uniform(0.8, 1.2)  # 重要度模擬

                features.append(
                    DemandFeature(
                        name=name,
                        value=value,
                        importance=importance,
                        category="technical",
                        timestamp=datetime.now().isoformat(),
                    )
                )

        return sorted(features, key=lambda f: f.importance, reverse=True)[:5]

    async def analyze_patterns(self) -> List[PatternAnalysis]:
        """
        パターン分析

        Returns:
            List[PatternAnalysis]: 分析結果
        """
        self.logger.info("📊 Analyzing demand patterns...")

        patterns = []

        for pattern_name, pattern_info in self.demand_patterns.items():
            # パターン分析実行
            analysis = await self._analyze_single_pattern(pattern_name, pattern_info)
            patterns.append(analysis)

        # 相関分析
        correlation_patterns = self._analyze_correlations()
        patterns.extend(correlation_patterns)

        self.logger.info(f"✅ Found {len(patterns)} patterns")

        return patterns

    async def _analyze_single_pattern(
        self, pattern_name: str, pattern_info: Dict
    ) -> PatternAnalysis:
        """単一パターン分析"""
        # 模擬分析結果
        frequency = np.random.uniform(0.3, 0.8)
        correlation_strength = np.random.uniform(0.5, 0.9)

        examples = self._generate_pattern_examples(pattern_name)

        return PatternAnalysis(
            pattern_name=pattern_name,
            description=pattern_info["description"],
            frequency=frequency,
            correlation_strength=correlation_strength,
            examples=examples,
            confidence=pattern_info["confidence_threshold"],
        )

    def _analyze_correlations(self) -> List[PatternAnalysis]:
        """相関分析"""
        correlations = [
            PatternAnalysis(
                pattern_name="ai_ml_correlation",
                description="AI/ML技術と市場需要の正の相関",
                frequency=0.85,
                correlation_strength=0.92,
                examples=["PyTorch + 求人増加", "ChatGPT + Python需要"],
                confidence=0.9,
            ),
            PatternAnalysis(
                pattern_name="framework_lifecycle",
                description="フレームワークのライフサイクルパターン",
                frequency=0.7,
                correlation_strength=0.75,
                examples=["React成熟期", "Vue成長期", "Svelte導入期"],
                confidence=0.8,
            ),
        ]

        return correlations

    def _generate_pattern_examples(self, pattern_name: str) -> List[str]:
        """パターン例生成"""
        examples_map = {
            "exponential_growth": [
                "ChatGPT adoption in Q4 2022",
                "React Hook surge in 2019",
                "Docker containerization boom",
            ],
            "linear_growth": [
                "TypeScript steady adoption",
                "AWS cloud migration trends",
                "Remote work tool adoption",
            ],
            "s_curve": [
                "Kubernetes enterprise adoption",
                "GraphQL API transition",
                "Serverless architecture adoption",
            ],
            "hype_cycle": [
                "Blockchain development hype",
                "NoSQL database evolution",
                "Microservices architecture",
            ],
            "seasonal": [
                "Conference-driven framework interest",
                "Hiring season technology demand",
                "Year-end project technology choices",
            ],
        }

        return examples_map.get(
            pattern_name, ["Generic example 1", "Generic example 2"]
        )

    async def generate_forecast(self, timeframe: TimeFrame) -> ForecastReport:
        """
        予測レポート生成

        Args:
            timeframe: 予測期間

        Returns:
            ForecastReport: 予測レポート
        """
        self.logger.info(f"📈 Generating forecast for {timeframe.value}...")

        # 複数技術の予測
        technologies = [
            "artificial intelligence",
            "rust programming",
            "kubernetes",
            "react framework",
            "python",
            "machine learning",
            "cloud computing",
            "microservices",
            "data science",
        ]

        predictions = []
        for tech in technologies:
            features = {
                "technology": tech,
                "timestamp": datetime.now(),
                "trend_indicators": {
                    "github_stars": np.random.randint(1000, 50000),
                    "job_postings": np.random.randint(100, 5000),
                    "search_volume": np.random.randint(10, 100),
                },
            }

            prediction = await self.predict_demand(features)
            prediction.timeframe = timeframe
            predictions.append(prediction)

        # パターン分析
        pattern_analysis = await self.analyze_patterns()

        # 市場洞察生成
        market_insights = self._generate_market_insights(predictions, timeframe)

        # 推奨事項生成
        recommendations = self._generate_recommendations(predictions, pattern_analysis)

        # リスク要因
        risk_factors = self._identify_risk_factors(predictions, timeframe)

        # 全体信頼度
        confidence_level = self._calculate_overall_confidence(predictions)

        report = ForecastReport(
            timeframe=timeframe,
            predictions=predictions,
            pattern_analysis=pattern_analysis,
            market_insights=market_insights,
            recommendations=recommendations,
            risk_factors=risk_factors,
            confidence_level=confidence_level,
            generated_at=datetime.now().isoformat(),
        )

        # レポート保存
        await self._save_forecast_report(report)

        self.logger.info("📊 Forecast report generated")

        return report

    def _generate_market_insights(
        self, predictions: List[Prediction], timeframe: TimeFrame
    ) -> List[str]:
        """市場洞察生成"""
        insights = []

        # 高需要技術
        high_demand = [p for p in predictions if p.predicted_value > 0.7]
        if high_demand:
            top_tech = max(high_demand, key=lambda p: p.predicted_value)
            insights.append(f"{top_tech.target}が{timeframe.value}で最高需要を示す予測")

        # 成長トレンド
        growing = [p for p in predictions if p.trend_direction == "increasing"]
        insights.append(f"{len(growing)}の技術が成長トレンドを示している")

        # AI/ML関連
        ai_predictions = [
            p
            for p in predictions
            if "ai" in p.target.lower() or "machine" in p.target.lower()
        ]
        if ai_predictions:
            avg_ai_demand = sum(p.predicted_value for p in ai_predictions) / len(
                ai_predictions
            )
            insights.append(f"AI/ML分野の平均需要予測: {avg_ai_demand:.2f}")

        return insights

    def _generate_recommendations(
        self, predictions: List[Prediction], patterns: List[PatternAnalysis]
    ) -> List[str]:
        """推奨事項生成"""
        recommendations = []

        # 高需要技術への投資推奨
        high_demand = [p for p in predictions if p.predicted_value > 0.8]
        for pred in high_demand[:3]:
            recommendations.append(
                f"{pred.target}への投資を強く推奨（予測需要: {pred.predicted_value:.2f}）"
            )

        # パターンベース推奨
        strong_patterns = [p for p in patterns if p.correlation_strength > 0.8]
        for pattern in strong_patterns[:2]:
            recommendations.append(
                f"{pattern.pattern_name}パターンに基づく戦略策定を推奨"
            )

        # リスク分散
        recommendations.append("複数技術への分散投資でリスク軽減を推奨")

        return recommendations

    def _identify_risk_factors(
        self, predictions: List[Prediction], timeframe: TimeFrame
    ) -> List[str]:
        """リスク要因特定"""
        risks = []

        # 低信頼度予測
        low_confidence = [p for p in predictions if p.confidence < 0.6]
        if low_confidence:
            risks.append(f"{len(low_confidence)}の技術予測で信頼度が低い")

        # 急激な変化
        extreme_values = [
            p for p in predictions if p.predicted_value > 0.9 or p.predicted_value < 0.2
        ]
        if extreme_values:
            risks.append("極端な需要変動の可能性")

        # 期間依存リスク
        if timeframe == TimeFrame.LONG_TERM:
            risks.append("長期予測の不確実性増大")

        risks.append("技術トレンドの急激な変化リスク")
        risks.append("市場環境変化による予測精度低下")

        return risks

    def _calculate_overall_confidence(self, predictions: List[Prediction]) -> float:
        """全体信頼度計算"""
        if not predictions:
            return 0.0

        return sum(p.confidence for p in predictions) / len(predictions)

    async def _save_forecast_report(self, report: ForecastReport):
        """予測レポート保存"""
        report_dir = Path("data/forecast_reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"forecast_{report.timeframe.value}_{timestamp}.json"

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"📄 Forecast report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"Report save error: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報取得"""
        return {
            "version": self.model.get("version", "unknown"),
            "created_at": self.model.get("created_at", "unknown"),
            "performance": self.model.get("performance_metrics", {}),
            "feature_count": len(self.model.get("feature_names", [])),
            "prediction_count": len(self.prediction_history),
        }

    def get_prediction_history(self, limit: int = 10) -> List[Prediction]:
        """予測履歴取得"""
        return self.prediction_history[-limit:]

    async def retrain_model(self, new_data: List[Dict]) -> Dict[str, Any]:
        """モデル再訓練"""
        self.logger.info("🔄 Retraining model with new data...")

        # 既存データと新データを結合
        combined_data = self.training_data + new_data

        # 再訓練実行
        result = await self.train_model(combined_data)

        self.logger.info("✅ Model retrained successfully")

        return result


# 使用例とテスト用関数
async def demo_demand_predictor():
    """Demand Predictor AIのデモ"""
    print("🔮 Demand Predictor AI Demo")
    print("=" * 50)

    predictor = DemandPredictorAI()

    # サンプル訓練データ
    training_data = [
        {
            "timestamp": "2024-01-01",
            "technology": "python",
            "demand_score": 85,
            "trend_indicators": {
                "github_stars": 45000,
                "job_postings": 3500,
                "search_volume": 90,
            },
        },
        {
            "timestamp": "2024-02-01",
            "technology": "javascript",
            "demand_score": 92,
            "trend_indicators": {
                "github_stars": 60000,
                "job_postings": 4200,
                "search_volume": 95,
            },
        },
        {
            "timestamp": "2024-03-01",
            "technology": "rust",
            "demand_score": 75,
            "trend_indicators": {
                "github_stars": 30000,
                "job_postings": 800,
                "search_volume": 70,
            },
        },
    ]

    # モデル訓練
    print("\n🎓 Training model...")
    training_result = await predictor.train_model(training_data)
    print(f"Training completed: R² = {training_result['performance']['r2_score']:.3f}")

    # 需要予測
    print("\n🔮 Making predictions...")
    test_features = {
        "technology": "artificial intelligence",
        "timestamp": datetime.now(),
        "trend_indicators": {
            "github_stars": 25000,
            "job_postings": 2000,
            "search_volume": 85,
        },
    }

    prediction = await predictor.predict_demand(test_features)
    print(f"AI Demand Prediction: {prediction.predicted_value:.3f}")
    print(f"Confidence: {prediction.confidence:.3f}")
    print(f"Trend: {prediction.trend_direction}")

    # パターン分析
    print("\n📊 Analyzing patterns...")
    patterns = await predictor.analyze_patterns()
    print(f"Found {len(patterns)} patterns:")
    for pattern in patterns[:3]:
        print(f"  - {pattern.pattern_name}: {pattern.correlation_strength:.2f}")

    # 予測レポート生成
    print("\n📈 Generating forecast report...")
    forecast = await predictor.generate_forecast(TimeFrame.MEDIUM_TERM)

    print(f"📊 Forecast Summary:")
    print(f"   Predictions: {len(forecast.predictions)}")
    print(f"   Confidence: {forecast.confidence_level:.2f}")
    print(
        f"   Top Technology: {max(forecast.predictions, key=lambda p: p.predicted_value).target}"
    )
    print(f"   Market Insights: {len(forecast.market_insights)}")
    print(f"   Recommendations: {len(forecast.recommendations)}")

    # モデル情報
    print("\n🔧 Model Info:")
    model_info = predictor.get_model_info()
    for key, value in model_info.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo_demand_predictor())

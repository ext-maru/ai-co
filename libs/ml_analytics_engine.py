#!/usr/bin/env python3
"""
機械学習分析エンジン
エルダーズギルドの高度な予測・分析・最適化システム

設計: RAGエルダー × クロードエルダー
承認: エルダーズ評議会
実装日: 2025年7月10日
"""

import asyncio
import json
import logging
import pickle
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, mean_squared_error, silhouette_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(Enum):
    """モデルタイプ"""

    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class MLModel:
    """機械学習モデル管理"""

    model_id: str
    model_type: ModelType
    algorithm: str
    features: List[str]
    target: Optional[str]
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    trained_at: datetime
    model_object: Any = None


class FeatureEngineer:
    """特徴量エンジニアリング"""

    def __init__(self):
        self.scalers = {}
        self.encoders = {}

    async def engineer_features(
        self, df: pd.DataFrame, feature_config: Dict
    ) -> pd.DataFrame:
        """特徴量エンジニアリング実行"""
        result = df.copy()

        # 時系列特徴量
        if feature_config.get("time_features", False):
            result = await self._add_time_features(result)

        # 統計特徴量
        if feature_config.get("statistical_features", False):
            result = await self._add_statistical_features(result)

        # カテゴリカル特徴量
        if feature_config.get("encode_categorical", False):
            result = await self._encode_categorical(result)

        # 相互作用特徴量
        if feature_config.get("interaction_features", False):
            result = await self._add_interaction_features(result)

        # 欠損値処理
        if feature_config.get("handle_missing", True):
            result = await self._handle_missing_values(result)

        return result

    async def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """時系列特徴量追加"""
        time_columns = df.select_dtypes(include=["datetime64"]).columns

        for col in time_columns:
            df[f"{col}_hour"] = df[col].dt.hour
            df[f"{col}_dayofweek"] = df[col].dt.dayofweek
            df[f"{col}_month"] = df[col].dt.month
            df[f"{col}_quarter"] = df[col].dt.quarter
            df[f"{col}_is_weekend"] = df[col].dt.dayofweek.isin([5, 6]).astype(int)

        return df

    async def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """統計的特徴量追加"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # ローリング統計
        for col in numeric_cols:
            if len(df) > 10:
                df[f"{col}_rolling_mean_7"] = (
                    df[col].rolling(window=7, min_periods=1).mean()
                )
                df[f"{col}_rolling_std_7"] = (
                    df[col].rolling(window=7, min_periods=1).std()
                )

        return df

    async def _encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """カテゴリカル変数エンコーディング"""
        categorical_cols = df.select_dtypes(include=["object"]).columns

        for col in categorical_cols:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                df[f"{col}_encoded"] = self.encoders[col].fit_transform(
                    df[col].fillna("unknown")
                )
            else:
                df[f"{col}_encoded"] = self.encoders[col].transform(
                    df[col].fillna("unknown")
                )

        return df

    async def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """相互作用特徴量追加"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns[:5]  # 最大5列

        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1 :]:
                df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
                df[f"{col1}_div_{col2}"] = df[col1] / (df[col2] + 1e-8)

        return df

    async def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """欠損値処理"""
        # 数値型: 中央値で補完
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col].fillna(df[col].median(), inplace=True)

        # カテゴリ型: 最頻値で補完
        categorical_cols = df.select_dtypes(include=["object"]).columns
        for col in categorical_cols:
            df[col].fillna(
                df[col].mode()[0] if not df[col].mode().empty else "unknown",
                inplace=True,
            )

        return df


class ModelTrainer:
    """モデル訓練エンジン"""

    def __init__(self):
        self.models = {
            ModelType.REGRESSION: {
                "random_forest": RandomForestRegressor,
                "linear_regression": LinearRegression,
            },
            ModelType.CLASSIFICATION: {
                "random_forest": RandomForestClassifier,
                "logistic_regression": LogisticRegression,
            },
            ModelType.CLUSTERING: {"kmeans": KMeans, "dbscan": DBSCAN},
        }

    async def train_model(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series],
        model_type: ModelType,
        algorithm: str,
        params: Dict = None,
    ) -> MLModel:
        """モデル訓練"""

        logger.info(f"🧠 モデル訓練開始: {model_type.value} - {algorithm}")

        # モデル作成
        model_class = self.models[model_type][algorithm]
        model = model_class(**(params or {}))

        # 訓練
        if model_type in [ModelType.REGRESSION, ModelType.CLASSIFICATION]:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            model.fit(X_train, y_train)

            # 評価
            y_pred = model.predict(X_test)

            if model_type == ModelType.REGRESSION:
                metrics = {
                    "mse": mean_squared_error(y_test, y_pred),
                    "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                    "r2": model.score(X_test, y_test),
                }
            else:
                metrics = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "cross_val_score": np.mean(cross_val_score(model, X, y, cv=5)),
                }

        elif model_type == ModelType.CLUSTERING:
            model.fit(X)

            if algorithm == "kmeans":
                metrics = {
                    "inertia": model.inertia_,
                    "silhouette_score": silhouette_score(X, model.labels_)
                    if len(set(model.labels_)) > 1
                    else 0,
                }
            else:
                metrics = {
                    "n_clusters": len(set(model.labels_))
                    - (1 if -1 in model.labels_ else 0)
                }

        # モデル情報作成
        ml_model = MLModel(
            model_id=f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_type=model_type,
            algorithm=algorithm,
            features=list(X.columns),
            target=y.name if y is not None else None,
            parameters=params or {},
            metrics=metrics,
            trained_at=datetime.now(),
            model_object=model,
        )

        logger.info(f"✅ モデル訓練完了: {ml_model.model_id}")
        logger.info(f"📊 メトリクス: {metrics}")

        return ml_model


class PredictionEngine:
    """予測エンジン"""

    def __init__(self):
        self.active_models: Dict[str, MLModel] = {}

    async def predict(
        self, model: MLModel, X: pd.DataFrame
    ) -> Union[np.ndarray, pd.DataFrame]:
        """予測実行"""
        if model.model_object is None:
            raise ValueError("モデルオブジェクトが存在しません")

        predictions = model.model_object.predict(X)

        # 予測結果をDataFrameで返す
        if model.model_type == ModelType.CLUSTERING:
            result = pd.DataFrame(
                {"cluster": predictions, "confidence": 1.0}  # クラスタリングの場合は信頼度1.0
            )
        else:
            # 確率予測が可能な場合
            if hasattr(model.model_object, "predict_proba"):
                probabilities = model.model_object.predict_proba(X)
                confidence = np.max(probabilities, axis=1)
            else:
                confidence = np.ones(len(predictions))

            result = pd.DataFrame({"prediction": predictions, "confidence": confidence})

        return result

    async def batch_predict(self, model: MLModel, data_generator) -> List[pd.DataFrame]:
        """バッチ予測"""
        results = []

        async for batch in data_generator:
            predictions = await self.predict(model, batch)
            results.append(predictions)

        return results


class AnomalyDetector:
    """異常検知エンジン"""

    def __init__(self):
        self.threshold_multiplier = 3  # 標準偏差の倍数

    async def detect_anomalies(
        self, df: pd.DataFrame, method: str = "statistical"
    ) -> pd.DataFrame:
        """異常検知実行"""
        result = df.copy()

        if method == "statistical":
            anomalies = await self._statistical_anomaly_detection(df)
        elif method == "isolation_forest":
            anomalies = await self._isolation_forest_detection(df)
        elif method == "clustering":
            anomalies = await self._clustering_based_detection(df)
        else:
            raise ValueError(f"未対応の異常検知手法: {method}")

        result["is_anomaly"] = anomalies
        result["anomaly_score"] = await self._calculate_anomaly_scores(df, anomalies)

        return result

    async def _statistical_anomaly_detection(self, df: pd.DataFrame) -> np.ndarray:
        """統計的異常検知"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        anomaly_mask = np.zeros(len(df), dtype=bool)

        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()

            # 3σルール
            lower_bound = mean - self.threshold_multiplier * std
            upper_bound = mean + self.threshold_multiplier * std

            col_anomalies = (df[col] < lower_bound) | (df[col] > upper_bound)
            anomaly_mask = anomaly_mask | col_anomalies

        return anomaly_mask

    async def _isolation_forest_detection(self, df: pd.DataFrame) -> np.ndarray:
        """Isolation Forestによる異常検知"""
        from sklearn.ensemble import IsolationForest

        numeric_df = df.select_dtypes(include=[np.number])

        model = IsolationForest(contamination=0.1, random_state=42)
        predictions = model.fit_predict(numeric_df)

        return predictions == -1

    async def _clustering_based_detection(self, df: pd.DataFrame) -> np.ndarray:
        """クラスタリングベース異常検知"""
        numeric_df = df.select_dtypes(include=[np.number])

        # DBSCAN使用
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        clusters = dbscan.fit_predict(StandardScaler().fit_transform(numeric_df))

        # ノイズポイント（-1）を異常とする
        return clusters == -1

    async def _calculate_anomaly_scores(
        self, df: pd.DataFrame, anomalies: np.ndarray
    ) -> np.ndarray:
        """異常スコア計算"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        scores = np.zeros(len(df))

        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()

            # 標準化された距離をスコアとする
            col_scores = np.abs(df[col] - mean) / (std + 1e-8)
            scores = np.maximum(scores, col_scores)

        return scores


class MLAnalyticsEngine:
    """機械学習分析エンジン統合"""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.models_dir = self.project_root / "ml_models"
        self.models_dir.mkdir(exist_ok=True)

        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()
        self.prediction_engine = PredictionEngine()
        self.anomaly_detector = AnomalyDetector()

        self.trained_models: Dict[str, MLModel] = {}

    async def train_and_save_model(
        self,
        data: pd.DataFrame,
        target_col: Optional[str],
        model_type: ModelType,
        algorithm: str,
        feature_config: Dict = None,
        model_params: Dict = None,
    ) -> MLModel:
        """モデル訓練と保存"""

        # 特徴量エンジニアリング
        engineered_data = await self.feature_engineer.engineer_features(
            data, feature_config or {}
        )

        # 訓練データ準備
        if target_col:
            X = engineered_data.drop(columns=[target_col])
            y = engineered_data[target_col]
        else:
            X = engineered_data
            y = None

        # モデル訓練
        model = await self.model_trainer.train_model(
            X, y, model_type, algorithm, model_params
        )

        # モデル保存
        await self._save_model(model)
        self.trained_models[model.model_id] = model

        return model

    async def predict_with_model(
        self, model_id: str, data: pd.DataFrame
    ) -> pd.DataFrame:
        """保存済みモデルで予測"""
        if model_id not in self.trained_models:
            model = await self._load_model(model_id)
            self.trained_models[model_id] = model
        else:
            model = self.trained_models[model_id]

        # 特徴量エンジニアリング（訓練時と同じ処理）
        engineered_data = await self.feature_engineer.engineer_features(
            data, {"handle_missing": True}  # 最低限の処理
        )

        # 訓練時の特徴量に合わせる
        missing_features = set(model.features) - set(engineered_data.columns)
        for feature in missing_features:
            engineered_data[feature] = 0

        X = engineered_data[model.features]

        # 予測実行
        predictions = await self.prediction_engine.predict(model, X)

        return predictions

    async def detect_anomalies_in_data(
        self, data: pd.DataFrame, method: str = "statistical"
    ) -> pd.DataFrame:
        """データの異常検知"""
        return await self.anomaly_detector.detect_anomalies(data, method)

    async def _save_model(self, model: MLModel):
        """モデル保存"""
        model_path = self.models_dir / f"{model.model_id}.pkl"

        # モデルオブジェクトを別途保存
        model_obj_path = self.models_dir / f"{model.model_id}_object.pkl"

        with open(model_obj_path, "wb") as f:
            pickle.dump(model.model_object, f)

        # メタデータ保存（モデルオブジェクト以外）
        metadata = {
            "model_id": model.model_id,
            "model_type": model.model_type.value,
            "algorithm": model.algorithm,
            "features": model.features,
            "target": model.target,
            "parameters": model.parameters,
            "metrics": model.metrics,
            "trained_at": model.trained_at.isoformat(),
        }

        with open(model_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"💾 モデル保存: {model_path}")

    async def _load_model(self, model_id: str) -> MLModel:
        """モデル読み込み"""
        model_path = self.models_dir / f"{model_id}.pkl"
        model_obj_path = self.models_dir / f"{model_id}_object.pkl"

        # メタデータ読み込み
        with open(model_path, "r") as f:
            metadata = json.load(f)

        # モデルオブジェクト読み込み
        with open(model_obj_path, "rb") as f:
            model_object = pickle.load(f)

        # MLModelオブジェクト再構築
        model = MLModel(
            model_id=metadata["model_id"],
            model_type=ModelType(metadata["model_type"]),
            algorithm=metadata["algorithm"],
            features=metadata["features"],
            target=metadata["target"],
            parameters=metadata["parameters"],
            metrics=metadata["metrics"],
            trained_at=datetime.fromisoformat(metadata["trained_at"]),
            model_object=model_object,
        )

        return model

    async def get_model_performance_report(self) -> Dict[str, Any]:
        """モデルパフォーマンスレポート生成"""
        report = {"total_models": len(self.trained_models), "models": []}

        for model_id, model in self.trained_models.items():
            model_info = {
                "model_id": model_id,
                "type": model.model_type.value,
                "algorithm": model.algorithm,
                "metrics": model.metrics,
                "feature_count": len(model.features),
                "trained_at": model.trained_at.isoformat(),
            }
            report["models"].append(model_info)

        return report


# 使用例
async def main():
    """MLエンジンサンプル実行"""
    engine = MLAnalyticsEngine(Path("/home/aicompany/ai_co"))

    # サンプルデータ作成
    sample_data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-07-01", periods=100, freq="H"),
            "value": np.random.normal(100, 15, 100),
            "category": np.random.choice(["A", "B", "C"], 100),
        }
    )
    sample_data["target"] = sample_data["value"] + np.random.normal(0, 5, 100)

    # モデル訓練
    model = await engine.train_and_save_model(
        data=sample_data,
        target_col="target",
        model_type=ModelType.REGRESSION,
        algorithm="random_forest",
        feature_config={
            "time_features": True,
            "statistical_features": True,
            "encode_categorical": True,
        },
        model_params={"n_estimators": 100, "random_state": 42},
    )

    print(f"訓練済みモデル: {model.model_id}")
    print(f"メトリクス: {model.metrics}")

    # 異常検知
    anomaly_result = await engine.detect_anomalies_in_data(sample_data)
    print(f"異常検知結果: {anomaly_result['is_anomaly'].sum()}件の異常を検出")


if __name__ == "__main__":
    asyncio.run(main())

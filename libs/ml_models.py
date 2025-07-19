#!/usr/bin/env python3
"""
機械学習モデル定義
予測分析用の各種モデル実装
"""

import json
import logging
import pickle
import sys
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRegistry:
    """モデルレジストリ"""

    def __init__(self):
        self.models = {}
        self.model_metadata = {}
        self.model_dir = Path(__file__).parent.parent / "models"
        self.model_dir.mkdir(exist_ok=True)

    def register_model(
        self, model_id: str, model: Any, metadata: Dict[str, Any] = None
    ):
        """モデル登録"""
        self.models[model_id] = model
        self.model_metadata[model_id] = {
            "registered_at": datetime.now().isoformat(),
            "model_type": type(model).__name__,
            "metadata": metadata or {},
        }
        logger.info(f"モデル登録: {model_id}")

    def get_model(self, model_id: str) -> Any:
        """モデル取得"""
        return self.models.get(model_id)

    def list_models(self) -> List[str]:
        """モデル一覧"""
        return list(self.models.keys())

    def save_model(self, model_id: str, file_path: Optional[Path] = None):
        """モデル保存"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        if file_path is None:
            file_path = self.model_dir / f"{model_id}.pkl"

        with open(file_path, "wb") as f:
            pickle.dump(
                {
                    "model": self.models[model_id],
                    "metadata": self.model_metadata[model_id],
                },
                f,
            )

        logger.info(f"モデル保存: {model_id} -> {file_path}")

    def load_model(self, model_id: str, file_path: Optional[Path] = None):
        """モデル読み込み"""
        if file_path is None:
            file_path = self.model_dir / f"{model_id}.pkl"

        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")

        with open(file_path, "rb") as f:
            data = pickle.load(f)

        self.models[model_id] = data["model"]
        self.model_metadata[model_id] = data["metadata"]

        logger.info(f"モデル読み込み: {model_id} <- {file_path}")


class BasePredictor:
    """予測モデル基底クラス"""

    def __init__(self, name: str):
        self.name = name
        self.prediction_count = 0
        self.last_used = None
        self.last_update = datetime.now()
        self.performance_history = deque(maxlen=100)

    def predict(self, *args, **kwargs):
        """予測実行（サブクラスで実装）"""
        raise NotImplementedError

    def get_accuracy_metrics(self) -> Dict[str, float]:
        """精度メトリクス取得"""
        if not self.performance_history:
            return {"rmse": 0, "mae": 0, "mape": 0}

        # 最新のパフォーマンスメトリクス
        recent_metrics = list(self.performance_history)[-10:]
        return {
            "rmse": np.mean([m.get("rmse", 0) for m in recent_metrics]),
            "mae": np.mean([m.get("mae", 0) for m in recent_metrics]),
            "mape": np.mean([m.get("mape", 0) for m in recent_metrics]),
        }

    def get_prediction_count(self) -> int:
        """予測回数取得"""
        return self.prediction_count

    def get_last_used_time(self) -> Optional[str]:
        """最終使用時刻取得"""
        return self.last_used.isoformat() if self.last_used else None

    def get_last_update_time(self) -> str:
        """最終更新時刻取得"""
        return self.last_update.isoformat()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        return {
            "accuracy": self.get_accuracy_metrics(),
            "prediction_count": self.prediction_count,
            "last_used": self.get_last_used_time(),
            "last_update": self.get_last_update_time(),
        }

    def update_performance(self, actual: List[float], predicted: List[float]):
        """パフォーマンス更新"""
        if len(actual) != len(predicted):
            return

        # RMSE (Root Mean Squared Error)
        rmse = np.sqrt(np.mean((np.array(actual) - np.array(predicted)) ** 2))

        # MAE (Mean Absolute Error)
        mae = np.mean(np.abs(np.array(actual) - np.array(predicted)))

        # MAPE (Mean Absolute Percentage Error)
        non_zero_actual = np.array(actual)[np.array(actual) != 0]
        non_zero_predicted = np.array(predicted)[np.array(actual) != 0]
        if len(non_zero_actual) > 0:
            mape = (
                np.mean(
                    np.abs((non_zero_actual - non_zero_predicted) / non_zero_actual)
                )
                * 100
            )
        else:
            mape = 0

        self.performance_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "rmse": float(rmse),
                "mae": float(mae),
                "mape": float(mape),
            }
        )


class TimeSeriesPredictor(BasePredictor):
    """時系列予測モデル"""

    def __init__(self, metric_name: str):
        super().__init__(f"time_series_{metric_name}")
        self.metric_name = metric_name
        self.history_window = 168  # 1週間（時間単位）
        self.historical_data = deque(maxlen=self.history_window * 12)  # 5分間隔

    def predict(self, horizon_hours: int = 24) -> List[float]:
        """時系列予測"""
        self.prediction_count += 1
        self.last_used = datetime.now()

        # 履歴データが不足している場合はランダムデータ生成
        if len(self.historical_data) < 24:
            base_value = 50 + np.random.randn() * 10
            trend = np.random.randn() * 0.1

            predictions = []
            for i in range(horizon_hours * 12):  # 5分間隔
                # 時間による周期性
                hour_of_day = (i // 12) % 24
                daily_pattern = 1 + 0.3 * np.sin(2 * np.pi * hour_of_day / 24)

                # 週次パターン
                day_of_week = (i // (12 * 24)) % 7
                weekly_pattern = 1 + 0.1 * np.sin(2 * np.pi * day_of_week / 7)

                # ノイズ
                noise = np.random.randn() * 5

                value = base_value * daily_pattern * weekly_pattern + i * trend + noise
                predictions.append(max(0, value))

            return predictions

        # 簡易的な移動平均予測
        recent_data = list(self.historical_data)[-144:]  # 最新12時間

        # トレンド抽出
        if len(recent_data) >= 2:
            trend = (recent_data[-1] - recent_data[0]) / len(recent_data)
        else:
            trend = 0

        # 季節性パターン抽出（24時間周期）
        seasonal_pattern = []
        for hour in range(24):
            hour_values = [
                recent_data[i]
                for i in range(hour * 12, min(len(recent_data), (hour + 1) * 12))
            ]
            if hour_values:
                seasonal_pattern.append(np.mean(hour_values))
            else:
                seasonal_pattern.append(50)

        # 予測生成
        predictions = []
        last_value = recent_data[-1] if recent_data else 50

        for i in range(horizon_hours * 12):
            hour_of_day = (i // 12) % 24
            seasonal_component = seasonal_pattern[hour_of_day] - np.mean(
                seasonal_pattern
            )

            # 予測値 = 最終値 + トレンド + 季節性 + ノイズ
            prediction = (
                last_value + trend * i + seasonal_component + np.random.randn() * 3
            )
            predictions.append(max(0, prediction))

            # ARモデル的な要素
            last_value = prediction * 0.7 + last_value * 0.3

        return predictions

    def add_historical_data(self, timestamp: datetime, value: float):
        """履歴データ追加"""
        self.historical_data.append(value)
        self.last_update = datetime.now()

    def get_historical_summary(self) -> Dict[str, Any]:
        """履歴データサマリー"""
        if not self.historical_data:
            return {"count": 0}

        data = list(self.historical_data)
        return {
            "count": len(data),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "last_value": float(data[-1]),
        }


class AnomalyDetector(BasePredictor):
    """異常検知モデル"""

    def __init__(self):
        super().__init__("anomaly_detector")
        self.threshold_multiplier = 3.0  # 標準偏差の倍数
        self.min_samples = 100
        self.baseline_stats = {}

    def detect_anomalies(
        self, data: List[float], sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """異常検知"""
        self.prediction_count += 1
        self.last_used = datetime.now()

        if len(data) < self.min_samples:
            return []

        # 統計量計算
        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)

        # 異常検出
        anomalies = []
        threshold = sensitivity * std

        for i, value in enumerate(data):
            z_score = abs(value - mean) / std if std > 0 else 0

            if z_score > sensitivity:
                anomaly_score = min(z_score / sensitivity, 2.0)  # 0-2の範囲

                anomalies.append(
                    {
                        "index": i,
                        "value": float(value),
                        "z_score": float(z_score),
                        "anomaly_score": float(anomaly_score),
                        "type": "spike" if value > mean else "drop",
                    }
                )

        # ベースライン更新
        self.baseline_stats = {
            "mean": float(mean),
            "std": float(std),
            "count": len(data),
        }

        return anomalies

    def detect_contextual_anomalies(
        self, data: List[Dict[str, Any]], context_window: int = 12
    ) -> List[Dict[str, Any]]:
        """文脈的異常検知"""
        if len(data) < context_window * 2:
            return []

        anomalies = []

        for i in range(context_window, len(data) - context_window):
            # 前後のコンテキストウィンドウ
            before = data[i - context_window : i]
            after = data[i : i + context_window]
            current = data[i]

            # コンテキスト統計
            context_values = [d.get("value", 0) for d in before + after]
            context_mean = np.mean(context_values)
            context_std = np.std(context_values)

            # 異常判定
            if context_std > 0:
                z_score = abs(current.get("value", 0) - context_mean) / context_std

                if z_score > 2.5:
                    anomalies.append(
                        {
                            "index": i,
                            "timestamp": current.get("timestamp"),
                            "value": current.get("value", 0),
                            "context_z_score": float(z_score),
                            "context_mean": float(context_mean),
                            "type": "contextual",
                        }
                    )

        return anomalies

    def get_baseline_stats(self) -> Dict[str, float]:
        """ベースライン統計取得"""
        return self.baseline_stats


class LoadPredictor(BasePredictor):
    """負荷予測モデル"""

    def __init__(self, resource_type: str):
        super().__init__(f"load_predictor_{resource_type}")
        self.resource_type = resource_type
        self.patterns = self._initialize_patterns()
        self.current_load = 50 + np.random.randn() * 10

    def predict(self, horizon_minutes: int = 60) -> List[float]:
        """負荷予測"""
        self.prediction_count += 1
        self.last_used = datetime.now()

        predictions = []
        current_time = datetime.now()

        for minute in range(0, horizon_minutes, 5):  # 5分間隔
            future_time = current_time + timedelta(minutes=minute)

            # 時間帯パターン
            hour = future_time.hour
            minute_of_hour = future_time.minute

            # ベース負荷（リソースタイプ別）
            base_load = self.patterns[self.resource_type]["base"]

            # 日中パターン
            daily_pattern = self.patterns[self.resource_type]["daily"][hour]

            # 分単位の変動
            minute_variation = np.sin(2 * np.pi * minute_of_hour / 60) * 5

            # ランダム変動
            random_variation = np.random.randn() * 3

            # 予測値計算
            predicted_load = (
                base_load + daily_pattern + minute_variation + random_variation
            )

            # スパイク発生（5%の確率）
            if np.random.random() < 0.05:
                predicted_load *= 1.5

            predictions.append(max(0, min(100, predicted_load)))

        return predictions

    def get_current_load(self) -> float:
        """現在の負荷取得"""
        # 実際の実装ではシステムから取得
        self.current_load += np.random.randn() * 2
        self.current_load = max(10, min(90, self.current_load))
        return float(self.current_load)

    def get_confidence_intervals(
        self, predictions: List[float], confidence_level: float = 0.95
    ) -> Dict[str, List[float]]:
        """信頼区間計算"""
        # 簡易的な信頼区間（正規分布仮定）
        z_score = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%

        # 予測の標準偏差（リソースタイプ別）
        std_dev = {"cpu": 8, "memory": 6, "disk": 4, "network": 10}.get(
            self.resource_type, 5
        )

        return {
            "upper": [min(100, p + z_score * std_dev) for p in predictions],
            "lower": [max(0, p - z_score * std_dev) for p in predictions],
        }

    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """パターン初期化"""
        patterns = {
            "cpu": {
                "base": 45,
                "daily": [
                    30,
                    25,
                    20,
                    20,
                    25,
                    30,
                    40,
                    50,
                    60,
                    65,
                    70,
                    75,
                    70,
                    65,
                    60,
                    65,
                    70,
                    65,
                    60,
                    55,
                    50,
                    45,
                    40,
                    35,
                ],
            },
            "memory": {
                "base": 60,
                "daily": [
                    50,
                    48,
                    45,
                    45,
                    48,
                    50,
                    55,
                    60,
                    65,
                    68,
                    70,
                    72,
                    70,
                    68,
                    65,
                    68,
                    70,
                    68,
                    65,
                    62,
                    60,
                    58,
                    55,
                    52,
                ],
            },
            "disk": {
                "base": 40,
                "daily": [
                    35,
                    35,
                    35,
                    35,
                    35,
                    36,
                    38,
                    40,
                    42,
                    43,
                    44,
                    45,
                    44,
                    43,
                    42,
                    43,
                    44,
                    43,
                    42,
                    41,
                    40,
                    39,
                    38,
                    37,
                ],
            },
            "network": {
                "base": 30,
                "daily": [
                    20,
                    18,
                    15,
                    15,
                    18,
                    22,
                    28,
                    35,
                    40,
                    45,
                    48,
                    50,
                    48,
                    45,
                    40,
                    45,
                    48,
                    45,
                    40,
                    35,
                    30,
                    28,
                    25,
                    22,
                ],
            },
        }

        return patterns


class IncidentPredictor(BasePredictor):
    """インシデント予測モデル"""

    def __init__(self):
        super().__init__("incident_predictor")
        self.incident_history = deque(maxlen=1000)
        self.risk_factors = {
            "cpu_high": 0.3,
            "memory_high": 0.25,
            "error_rate_high": 0.4,
            "response_time_high": 0.2,
            "connection_spike": 0.15,
        }

    def predict_incidents(
        self, system_state: Dict[str, Any], hours_ahead: int = 24
    ) -> List[float]:
        """インシデント確率予測"""
        self.prediction_count += 1
        self.last_used = datetime.now()

        # ベースリスク計算
        base_risk = self._calculate_base_risk(system_state)

        # 時間別予測
        predictions = []
        current_hour = datetime.now().hour

        for hour in range(hours_ahead):
            future_hour = (current_hour + hour) % 24

            # 時間帯による調整
            time_factor = self._get_time_factor(future_hour)

            # 履歴パターンによる調整
            history_factor = self._get_history_factor(future_hour)

            # 最終的な確率計算
            incident_probability = base_risk * time_factor * history_factor

            # 累積効果（時間が経つほどリスク増加）
            accumulation_factor = 1 + (hour / hours_ahead) * 0.2
            incident_probability *= accumulation_factor

            predictions.append(min(incident_probability, 1.0))

        return predictions

    def _calculate_base_risk(self, state: Dict[str, Any]) -> float:
        """ベースリスク計算"""
        risk_score = 0

        # CPU使用率
        if state.get("cpu_usage", 0) > 80:
            risk_score += self.risk_factors["cpu_high"]

        # メモリ使用率
        if state.get("memory_usage", 0) > 85:
            risk_score += self.risk_factors["memory_high"]

        # エラー率
        if state.get("error_rate", 0) > 0.05:
            risk_score += self.risk_factors["error_rate_high"]

        # レスポンスタイム
        if state.get("response_time", 0) > 500:
            risk_score += self.risk_factors["response_time_high"]

        # 接続数スパイク
        if state.get("active_connections", 0) > 1000:
            risk_score += self.risk_factors["connection_spike"]

        return min(risk_score, 0.9)

    def _get_time_factor(self, hour: int) -> float:
        """時間帯リスクファクター"""
        # ピーク時間帯（9-11, 14-16）はリスク高
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            return 1.3
        # 深夜（2-5）は低リスク
        elif 2 <= hour <= 5:
            return 0.7
        else:
            return 1.0

    def _get_history_factor(self, hour: int) -> float:
        """履歴パターンファクター"""
        # 簡易実装: ランダム要素
        return 0.8 + np.random.random() * 0.4

    def get_confidence_score(self) -> float:
        """信頼度スコア"""
        # 履歴データ量に基づく信頼度
        if len(self.incident_history) > 500:
            return 0.9
        elif len(self.incident_history) > 100:
            return 0.7
        else:
            return 0.5


if __name__ == "__main__":
    # テスト実行
    print("=== ML モデル テスト ===")

    # モデルレジストリ
    registry = ModelRegistry()

    # 時系列予測モデル
    print("\n1. 時系列予測モデル")
    ts_model = TimeSeriesPredictor("cpu")
    predictions = ts_model.predict(24)
    print(f"   予測数: {len(predictions)}")
    print(f"   最初の5予測: {predictions[:5]}")

    # 異常検知モデル
    print("\n2. 異常検知モデル")
    anomaly_model = AnomalyDetector()
    test_data = [50 + np.random.randn() * 5 for _ in range(200)]
    test_data[50] = 100  # 異常値
    test_data[100] = 10  # 異常値

    anomalies = anomaly_model.detect_anomalies(test_data)
    print(f"   検出異常数: {len(anomalies)}")
    if anomalies:
        print(f"   最初の異常: {anomalies[0]}")

    # 負荷予測モデル
    print("\n3. 負荷予測モデル")
    load_model = LoadPredictor("cpu")
    load_predictions = load_model.predict(60)
    intervals = load_model.get_confidence_intervals(load_predictions)

    print(f"   現在の負荷: {load_model.get_current_load():.1f}%")
    print(f"   予測最大値: {max(load_predictions):.1f}%")
    print(f"   予測最小値: {min(load_predictions):.1f}%")

    # モデル登録
    registry.register_model("ts_cpu", ts_model)
    registry.register_model("anomaly", anomaly_model)
    registry.register_model("load_cpu", load_model)

    print(f"\n登録済みモデル: {registry.list_models()}")

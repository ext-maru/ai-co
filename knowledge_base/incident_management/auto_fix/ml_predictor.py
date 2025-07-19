#!/usr/bin/env python3
"""
ML Predictor - 機械学習による障害予測システム
インシデント賢者の予知能力
"""

import json
import logging
import pickle
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class IncidentPredictor:
    """機械学習による障害予測システム"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")
        self.model_dir = (
            self.ai_co_path / "knowledge_base" / "incident_management" / "ml_models"
        )
        self.model_dir.mkdir(exist_ok=True)

        # 特徴量定義
        self.feature_columns = [
            "hour_of_day",
            "day_of_week",
            "day_of_month",
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "load_average",
            "active_workers",
            "queue_length",
            "error_rate",
            "response_time_avg",
            "network_throughput",
            "recent_incident_count",
            "time_since_last_incident",
        ]

        # 予測モデル（簡易実装 - 実際には scikit-learn などを使用）
        self.models = {}
        self.feature_history = deque(maxlen=1000)  # 最新1000サンプル
        self.prediction_history = []

        # 予測精度追跡
        self.accuracy_tracker = {
            "total_predictions": 0,
            "correct_predictions": 0,
            "false_positives": 0,
            "false_negatives": 0,
        }

        self.logger.info("🔮 IncidentPredictor initialized - 障害予測システム起動")

    def collect_current_features(self) -> Dict:
        """現在のシステム特徴量収集"""
        try:
            import psutil

            # 時間特徴量
            now = datetime.now()
            features = {
                "timestamp": now.isoformat(),
                "hour_of_day": now.hour,
                "day_of_week": now.weekday(),
                "day_of_month": now.day,
            }

            # システム特徴量
            features.update(
                {
                    "cpu_usage": psutil.cpu_percent(interval=1),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                    "load_average": psutil.getloadavg()[0],  # 1分平均
                }
            )

            # Elders Guild 特有の特徴量
            features.update(self._collect_ai_company_features())

            # 履歴ベース特徴量
            features.update(self._calculate_historical_features())

            return features

        except Exception as e:
            self.logger.error(f"Feature collection failed: {str(e)}")
            return self._get_default_features()

    def _collect_ai_company_features(self) -> Dict:
        """Elders Guild固有の特徴量収集"""
        features = {}

        try:
            # ワーカープロセス数
            import psutil

            active_workers = 0
            for proc in psutil.process_iter(["cmdline"]):
                try:
                    cmdline = " ".join(proc.info.get("cmdline", []))
                    if "worker" in cmdline and "ai_co" in cmdline:
                        active_workers += 1
                except:
                    continue

            features["active_workers"] = active_workers

            # キュー長（簡易推定）
            features["queue_length"] = self._estimate_queue_length()

            # エラー率（ログベース）
            features["error_rate"] = self._calculate_recent_error_rate()

            # 応答時間（推定）
            features["response_time_avg"] = self._estimate_response_time()

            # ネットワークスループット（簡易）
            net_io = psutil.net_io_counters()
            features["network_throughput"] = (
                (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024
            )  # MB

        except Exception as e:
            self.logger.warning(f"Elders Guild features collection failed: {str(e)}")
            features.update(
                {
                    "active_workers": 0,
                    "queue_length": 0,
                    "error_rate": 0,
                    "response_time_avg": 0,
                    "network_throughput": 0,
                }
            )

        return features

    def _calculate_historical_features(self) -> Dict:
        """履歴ベース特徴量計算"""
        features = {}

        try:
            # 最近のインシデント数
            recent_incidents = self._count_recent_incidents(hours=24)
            features["recent_incident_count"] = recent_incidents

            # 最後のインシデントからの経過時間
            last_incident_time = self._get_last_incident_time()
            if last_incident_time:
                time_diff = (
                    datetime.now() - last_incident_time
                ).total_seconds() / 3600  # hours
                features["time_since_last_incident"] = min(time_diff, 168)  # 最大1週間
            else:
                features["time_since_last_incident"] = 168  # デフォルト1週間

        except Exception as e:
            self.logger.warning(f"Historical features calculation failed: {str(e)}")
            features.update(
                {"recent_incident_count": 0, "time_since_last_incident": 168}
            )

        return features

    def _estimate_queue_length(self) -> int:
        """キュー長推定"""
        try:
            # RabbitMQ キュー確認（簡易版）
            import subprocess

            result = subprocess.run(
                ["sudo", "rabbitmqctl", "list_queues", "name", "messages"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                total_messages = 0
                for line in result.stdout.strip().split("\n")[1:]:  # ヘッダースキップ
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            total_messages += int(parts[1])
                        except ValueError:
                            continue
                return total_messages
        except:
            pass

        return 0

    def _calculate_recent_error_rate(self) -> float:
        """最近のエラー率計算"""
        try:
            logs_dir = self.ai_co_path / "logs"
            if not logs_dir.exists():
                return 0.0

            error_count = 0
            total_lines = 0
            cutoff_time = datetime.now() - timedelta(hours=1)

            for log_file in logs_dir.glob("*.log"):
                try:
                    with open(log_file, "r") as f:
                        for line in f:
                            if "ERROR" in line or "Exception" in line:
                                error_count += 1
                            total_lines += 1

                            # 最新1000行のみ処理（パフォーマンス考慮）
                            if total_lines > 1000:
                                break
                except:
                    continue

            return (error_count / total_lines * 100) if total_lines > 0 else 0.0

        except Exception as e:
            self.logger.warning(f"Error rate calculation failed: {str(e)}")
            return 0.0

    def _estimate_response_time(self) -> float:
        """応答時間推定"""
        # 簡易実装 - システム負荷から推定
        try:
            import psutil

            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            # 負荷が高いほど応答時間が長い（経験的式）
            base_time = 100  # ms
            cpu_factor = max(0, (cpu_percent - 50) / 50)
            memory_factor = max(0, (memory_percent - 70) / 30)

            estimated_time = base_time * (1 + cpu_factor + memory_factor)
            return min(estimated_time, 5000)  # 最大5秒

        except:
            return 100.0

    def _count_recent_incidents(self, hours: int = 24) -> int:
        """最近のインシデント数カウント"""
        try:
            incident_file = (
                self.ai_co_path
                / "knowledge_base"
                / "incident_management"
                / "incident_history.json"
            )
            if not incident_file.exists():
                return 0

            with open(incident_file, "r") as f:
                data = json.load(f)

            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_count = 0

            for incident in data.get("incidents", []):
                try:
                    incident_time = datetime.fromisoformat(incident["timestamp"])
                    if incident_time > cutoff_time:
                        recent_count += 1
                except:
                    continue

            return recent_count

        except:
            return 0

    def _get_last_incident_time(self) -> Optional[datetime]:
        """最後のインシデント時刻取得"""
        try:
            incident_file = (
                self.ai_co_path
                / "knowledge_base"
                / "incident_management"
                / "incident_history.json"
            )
            if not incident_file.exists():
                return None

            with open(incident_file, "r") as f:
                data = json.load(f)

            latest_time = None
            for incident in data.get("incidents", []):
                try:
                    incident_time = datetime.fromisoformat(incident["timestamp"])
                    if latest_time is None or incident_time > latest_time:
                        latest_time = incident_time
                except:
                    continue

            return latest_time

        except:
            return None

    def _get_default_features(self) -> Dict:
        """デフォルト特徴量"""
        now = datetime.now()
        return {
            "timestamp": now.isoformat(),
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "day_of_month": now.day,
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "load_average": 0,
            "active_workers": 0,
            "queue_length": 0,
            "error_rate": 0,
            "response_time_avg": 100,
            "network_throughput": 0,
            "recent_incident_count": 0,
            "time_since_last_incident": 168,
        }

    def predict_incident_probability(self, features: Optional[Dict] = None) -> Dict:
        """インシデント発生確率予測"""
        if features is None:
            features = self.collect_current_features()

        prediction = {
            "timestamp": datetime.now().isoformat(),
            "features_used": features,
            "predictions": {},
            "overall_risk": "low",
            "confidence": 0.0,
            "recommendations": [],
        }

        try:
            # 複数の予測手法を組み合わせ

            # 1. ルールベース予測
            rule_based = self._rule_based_prediction(features)
            prediction["predictions"]["rule_based"] = rule_based

            # 2. 統計ベース予測
            statistical = self._statistical_prediction(features)
            prediction["predictions"]["statistical"] = statistical

            # 3. パターン認識予測
            pattern_based = self._pattern_based_prediction(features)
            prediction["predictions"]["pattern_based"] = pattern_based

            # アンサンブル予測
            ensemble_prob = self._ensemble_prediction(
                [rule_based, statistical, pattern_based]
            )
            prediction["predictions"]["ensemble"] = ensemble_prob

            # 総合リスク評価
            prediction["overall_risk"] = self._categorize_risk(
                ensemble_prob["probability"]
            )
            prediction["confidence"] = ensemble_prob["confidence"]

            # 推奨事項生成
            prediction["recommendations"] = self._generate_recommendations(
                features, ensemble_prob
            )

        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            prediction["error"] = str(e)
            prediction["predictions"]["ensemble"] = {
                "probability": 0.1,
                "confidence": 0.1,
            }

        # 履歴に追加
        self.feature_history.append(features)
        self.prediction_history.append(prediction)

        return prediction

    def _rule_based_prediction(self, features: Dict) -> Dict:
        """ルールベース予測"""
        probability = 0.0
        triggered_rules = []

        # Rule 1: 高CPU使用率
        if features.get("cpu_usage", 0) > 90:
            probability += 0.4
            triggered_rules.append("high_cpu")
        elif features.get("cpu_usage", 0) > 80:
            probability += 0.2
            triggered_rules.append("elevated_cpu")

        # Rule 2: 高メモリ使用率
        if features.get("memory_usage", 0) > 95:
            probability += 0.5
            triggered_rules.append("critical_memory")
        elif features.get("memory_usage", 0) > 85:
            probability += 0.3
            triggered_rules.append("high_memory")

        # Rule 3: ディスク容量不足
        if features.get("disk_usage", 0) > 95:
            probability += 0.3
            triggered_rules.append("disk_full")

        # Rule 4: ワーカー異常
        active_workers = features.get("active_workers", 0)
        if active_workers == 0:
            probability += 0.6
            triggered_rules.append("no_workers")
        elif active_workers < 2:
            probability += 0.3
            triggered_rules.append("few_workers")

        # Rule 5: 高エラー率
        if features.get("error_rate", 0) > 10:
            probability += 0.4
            triggered_rules.append("high_error_rate")

        # Rule 6: 最近のインシデント多発
        recent_incidents = features.get("recent_incident_count", 0)
        if recent_incidents > 5:
            probability += 0.3
            triggered_rules.append("frequent_incidents")

        # Rule 7: 応答時間悪化
        if features.get("response_time_avg", 0) > 2000:
            probability += 0.3
            triggered_rules.append("slow_response")

        return {
            "probability": min(probability, 1.0),
            "confidence": 0.8 if triggered_rules else 0.3,
            "triggered_rules": triggered_rules,
        }

    def _statistical_prediction(self, features: Dict) -> Dict:
        """統計ベース予測"""
        try:
            if len(self.feature_history) < 10:
                return {
                    "probability": 0.1,
                    "confidence": 0.2,
                    "method": "insufficient_data",
                }

            # 過去データから統計的異常検出
            recent_features = list(self.feature_history)[-50:]  # 最新50サンプル

            anomaly_score = 0.0
            anomaly_count = 0

            for feature_name in [
                "cpu_usage",
                "memory_usage",
                "error_rate",
                "response_time_avg",
            ]:
                if feature_name not in features:
                    continue

                # 過去データの統計
                values = [f.get(feature_name, 0) for f in recent_features]
                if not values:
                    continue

                mean_val = np.mean(values)
                std_val = np.std(values)
                current_val = features[feature_name]

                # Z-score による異常検出
                if std_val > 0:
                    z_score = abs((current_val - mean_val) / std_val)
                    if z_score > 2:  # 2σ を超える場合
                        anomaly_score += min(z_score / 10, 0.3)
                        anomaly_count += 1

            probability = min(anomaly_score, 0.8)
            confidence = min(anomaly_count / 4, 0.7)

            return {
                "probability": probability,
                "confidence": confidence,
                "anomaly_count": anomaly_count,
                "method": "zscore_analysis",
            }

        except Exception as e:
            return {"probability": 0.1, "confidence": 0.1, "error": str(e)}

    def _pattern_based_prediction(self, features: Dict) -> Dict:
        """パターン認識予測"""
        try:
            # 時間パターン分析
            hour = features.get("hour_of_day", 0)
            day_of_week = features.get("day_of_week", 0)

            # 過去のインシデント時間パターン分析
            incident_patterns = self._analyze_incident_time_patterns()

            time_risk = 0.0

            # 高リスク時間帯
            if hour in incident_patterns.get("high_risk_hours", []):
                time_risk += 0.2

            # 高リスク曜日
            if day_of_week in incident_patterns.get("high_risk_days", []):
                time_risk += 0.1

            # システム状態パターン
            state_risk = self._analyze_system_state_pattern(features)

            total_probability = min(time_risk + state_risk, 0.7)

            return {
                "probability": total_probability,
                "confidence": 0.6,
                "time_risk": time_risk,
                "state_risk": state_risk,
                "method": "pattern_analysis",
            }

        except Exception as e:
            return {"probability": 0.1, "confidence": 0.1, "error": str(e)}

    def _ensemble_prediction(self, predictions: List[Dict]) -> Dict:
        """アンサンブル予測"""
        if not predictions:
            return {"probability": 0.1, "confidence": 0.1}

        # 信頼度で重み付け平均
        total_weight = sum(p.get("confidence", 0.1) for p in predictions)
        if total_weight == 0:
            return {"probability": 0.1, "confidence": 0.1}

        weighted_prob = (
            sum(p.get("probability", 0) * p.get("confidence", 0.1) for p in predictions)
            / total_weight
        )

        avg_confidence = sum(p.get("confidence", 0.1) for p in predictions) / len(
            predictions
        )

        return {
            "probability": weighted_prob,
            "confidence": avg_confidence,
            "method": "weighted_ensemble",
        }

    def _categorize_risk(self, probability: float) -> str:
        """リスクカテゴリ化"""
        if probability >= 0.7:
            return "critical"
        elif probability >= 0.5:
            return "high"
        elif probability >= 0.3:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(self, features: Dict, prediction: Dict) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        probability = prediction.get("probability", 0)

        if probability > 0.5:
            recommendations.append("高リスク状態: 即座の対応を推奨")

            # 具体的な推奨事項
            if features.get("cpu_usage", 0) > 80:
                recommendations.append("CPU使用率が高い: プロセス確認とスケールアウト検討")

            if features.get("memory_usage", 0) > 85:
                recommendations.append("メモリ使用率が高い: メモリリーク確認とキャッシュクリア")

            if features.get("active_workers", 0) < 2:
                recommendations.append("ワーカー数が少ない: ワーカーの再起動と追加")

            if features.get("error_rate", 0) > 5:
                recommendations.append("エラー率が高い: ログ確認と根本原因調査")

        elif probability > 0.3:
            recommendations.append("注意レベル: 監視強化を推奨")
            recommendations.append("定期的なシステムチェックを実施")

        else:
            recommendations.append("正常レベル: 継続監視")

        return recommendations

    def _analyze_incident_time_patterns(self) -> Dict:
        """インシデント時間パターン分析"""
        try:
            incident_file = (
                self.ai_co_path
                / "knowledge_base"
                / "incident_management"
                / "incident_history.json"
            )
            if not incident_file.exists():
                return {"high_risk_hours": [], "high_risk_days": []}

            with open(incident_file, "r") as f:
                data = json.load(f)

            hour_counts = defaultdict(int)
            day_counts = defaultdict(int)

            for incident in data.get("incidents", []):
                try:
                    incident_time = datetime.fromisoformat(incident["timestamp"])
                    hour_counts[incident_time.hour] += 1
                    day_counts[incident_time.weekday()] += 1
                except:
                    continue

            # 平均以上の時間帯を高リスクとする
            avg_hour_count = sum(hour_counts.values()) / max(len(hour_counts), 1)
            avg_day_count = sum(day_counts.values()) / max(len(day_counts), 1)

            high_risk_hours = [
                hour for hour, count in hour_counts.items() if count > avg_hour_count
            ]
            high_risk_days = [
                day for day, count in day_counts.items() if count > avg_day_count
            ]

            return {
                "high_risk_hours": high_risk_hours,
                "high_risk_days": high_risk_days,
            }

        except:
            return {"high_risk_hours": [], "high_risk_days": []}

    def _analyze_system_state_pattern(self, features: Dict) -> float:
        """システム状態パターン分析"""
        risk = 0.0

        # 複合的な状態パターン
        cpu = features.get("cpu_usage", 0)
        memory = features.get("memory_usage", 0)

        # パターン1: CPU と メモリが同時に高い
        if cpu > 70 and memory > 70:
            risk += 0.3

        # パターン2: エラー率とレスポンス時間の悪化
        error_rate = features.get("error_rate", 0)
        response_time = features.get("response_time_avg", 0)
        if error_rate > 5 and response_time > 1000:
            risk += 0.2

        # パターン3: ワーカー数とキュー長の不均衡
        workers = features.get("active_workers", 0)
        queue_length = features.get("queue_length", 0)
        if workers > 0 and queue_length / max(workers, 1) > 10:
            risk += 0.2

        return min(risk, 0.5)

    def update_prediction_accuracy(self, prediction_id: str, actual_incident: bool):
        """予測精度更新"""
        try:
            # 予測履歴から該当予測を検索
            for prediction in self.prediction_history:
                if prediction.get("id") == prediction_id:
                    predicted_prob = prediction["predictions"]["ensemble"][
                        "probability"
                    ]
                    predicted_incident = predicted_prob > 0.5

                    self.accuracy_tracker["total_predictions"] += 1

                    if predicted_incident == actual_incident:
                        self.accuracy_tracker["correct_predictions"] += 1
                    elif predicted_incident and not actual_incident:
                        self.accuracy_tracker["false_positives"] += 1
                    elif not predicted_incident and actual_incident:
                        self.accuracy_tracker["false_negatives"] += 1

                    break

        except Exception as e:
            self.logger.error(f"Accuracy update failed: {str(e)}")

    def get_prediction_statistics(self) -> Dict:
        """予測統計取得"""
        total = self.accuracy_tracker["total_predictions"]
        if total == 0:
            return {"total_predictions": 0, "accuracy": 0}

        accuracy = self.accuracy_tracker["correct_predictions"] / total
        precision = self.accuracy_tracker["correct_predictions"] / max(
            self.accuracy_tracker["correct_predictions"]
            + self.accuracy_tracker["false_positives"],
            1,
        )
        recall = self.accuracy_tracker["correct_predictions"] / max(
            self.accuracy_tracker["correct_predictions"]
            + self.accuracy_tracker["false_negatives"],
            1,
        )

        return {
            "total_predictions": total,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "false_positive_rate": self.accuracy_tracker["false_positives"] / total,
            "false_negative_rate": self.accuracy_tracker["false_negatives"] / total,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ML-based Incident Predictor")
    parser.add_argument(
        "action", choices=["predict", "collect", "stats"], help="Action to perform"
    )
    parser.add_argument(
        "--output", choices=["json", "summary"], default="summary", help="Output format"
    )

    args = parser.parse_args()

    predictor = IncidentPredictor()

    if args.action == "predict":
        prediction = predictor.predict_incident_probability()

        if args.output == "json":
            print(json.dumps(prediction, indent=2))
        else:
            risk = prediction["overall_risk"]
            prob = prediction["predictions"]["ensemble"]["probability"]
            confidence = prediction["confidence"]

            print(f"🔮 Incident Prediction Summary")
            print(f"Overall Risk: {risk.upper()} ({prob:.2%})")
            print(f"Confidence: {confidence:.2%}")
            print(f"Recommendations:")
            for rec in prediction["recommendations"]:
                print(f"  - {rec}")

    elif args.action == "collect":
        features = predictor.collect_current_features()
        print(json.dumps(features, indent=2))

    elif args.action == "stats":
        stats = predictor.get_prediction_statistics()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
高度データアナリティクスプラットフォーム
エルダーズギルドの全データを統合分析・予測する包括的システム

設計: RAGエルダー × クロードエルダー
承認: エルダーズ評議会（予定）
実装日: 2025年7月9日
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsType(Enum):
    """分析タイプ"""

    COMMIT_PATTERN = "commit_pattern"  # コミットパターン分析
    SAGE_PERFORMANCE = "sage_performance"  # 4賢者パフォーマンス分析
    SYSTEM_HEALTH = "system_health"  # システムヘルス予測
    PROTOCOL_EFFICIENCY = "protocol_efficiency"  # プロトコル効率分析
    ERROR_PREDICTION = "error_prediction"  # エラー予測
    BOTTLENECK_DETECTION = "bottleneck_detection"  # ボトルネック検出


@dataclass
class AnalyticsResult:
    """分析結果"""

    type: AnalyticsType
    timestamp: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    predictions: Dict[str, Any]
    recommendations: List[str]
    confidence: float


class DataCollector:
    """データ収集エンジン"""

    def __init__(self, project_root: Path):
        """初期化メソッド"""
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        self.db_path = self.project_root / "elder_dashboard.db"

    async def collect_commit_data(self) -> pd.DataFrame:
        """コミットデータ収集"""
        try:
            conn = sqlite3connect(str(self.db_path))

            # プロトコル履歴を取得
            query = """
                SELECT
                    timestamp,
                    protocol,
                    message,
                    approved,
                    execution_time,
                    sage_count,
                    risk_score,
                    files_changed,
                    complexity
                FROM protocol_history
                ORDER BY timestamp
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            # 日時型に変換
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            logger.info(f"📊 {len(df)}件のコミットデータを収集")
            return df

        except Exception as e:
            logger.error(f"❌ コミットデータ収集エラー: {e}")
            return pd.DataFrame()

    async def collect_sage_consultation_data(self) -> pd.DataFrame:
        """4賢者相談データ収集"""
        try:
            conn = sqlite3connect(str(self.db_path))

            query = """
                SELECT
                    sc.sage_name,
                    sc.approval,
                    sc.risk_score,
                    sc.advice,
                    sc.timestamp,
                    ph.protocol,
                    ph.complexity
                FROM sage_consultations sc
                JOIN protocol_history ph ON sc.protocol_id = ph.id
                ORDER BY sc.timestamp
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            df["timestamp"] = pd.to_datetime(df["timestamp"])

            logger.info(f"🧙‍♂️ {len(df)}件の賢者相談データを収集")
            return df

        except Exception as e:
            logger.error(f"❌ 賢者相談データ収集エラー: {e}")
            return pd.DataFrame()

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        metrics = {
            "timestamp": datetime.now(),
            "active_workers": 0,
            "error_logs": 0,
            "warning_logs": 0,
            "total_log_files": 0,
            "disk_usage_mb": 0,
        }

        try:
            # ログファイル統計
            log_files = list(self.logs_dir.glob("*.log"))
            metrics["total_log_files"] = len(log_files)

            # エラー・警告カウント（簡易版）
            for log_file in log_files[:10]:  # サンプリング
                try:
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        metrics["error_logs"] += content.count("ERROR")
                        metrics["warning_logs"] += content.count("WARNING")
                except:
                    pass

            # ディスク使用量
            total_size = sum(f.stat().st_size for f in log_files)
            metrics["disk_usage_mb"] = total_size / (1024 * 1024)

            logger.info(f"📈 システムメトリクス収集完了")
            return metrics

        except Exception as e:
            logger.error(f"❌ システムメトリクス収集エラー: {e}")
            return metrics


class PredictionModel:
    """高度な予測モデル"""

    def __init__(self):
        """初期化メソッド"""
        self.time_series_models = {}
        self.anomaly_detectors = {}
        self.trained = False

    async def train_time_series(
        self, df: pd.DataFrame, target_column: str, time_column: str = "timestamp"
    ):
        """時系列予測モデルの訓練"""
        if df.empty or target_column not in df.columns:
            logger.warning(f"⚠️ 時系列訓練用のデータが不足: {target_column}")
            return

        # データを時系列順にソート
        df_sorted = df.sort_values(time_column)

        # 移動平均モデル（簡易版）
        self.time_series_models[target_column] = {
            "type": "moving_average",
            "window_sizes": [3, 7, 14],
            "data": {},
        }

        # 各ウィンドウサイズで移動平均を計算
        for window in self.time_series_models[target_column]["window_sizes"]:
            if len(df_sorted) >= window:
                ma = df_sorted[target_column].rolling(window=window).mean()
                self.time_series_models[target_column]["data"][f"ma_{window}"] = (
                    ma.iloc[-1]
                )

        # トレンド分析
        if len(df_sorted) > 10:
            # 線形トレンドの計算
            x = np.arange(len(df_sorted))
            y = df_sorted[target_column].values
            if np.issubdtype(y.dtype, np.number):
                coeffs = np.polyfit(x, y, 1)
                self.time_series_models[target_column]["trend"] = {
                    "slope": coeffs[0],
                    "intercept": coeffs[1],
                    "direction": "increasing" if coeffs[0] > 0 else "decreasing",
                }

        logger.info(f"📈 時系列モデル訓練完了: {target_column}")

    async def detect_anomalies(
        self, df: pd.DataFrame, column: str, threshold: float = 2.0
    ):
        """異常検出"""
        if df.empty or column not in df.columns:
            return []

        anomalies = []
        values = df[column].dropna()

        if len(values) > 3:
            # 統計的異常検出（Zスコア法）
            mean = values.mean()
            std = values.std()

            if std > 0:
                z_scores = np.abs((values - mean) / std)
                anomaly_indices = z_scores[z_scores > threshold].index

                for idx in anomaly_indices:
                    anomalies.append(
                        {
                            "index": idx,
                            "value": values[idx],
                            "z_score": z_scores[idx],
                            "severity": "high" if z_scores[idx] > 3 else "medium",
                        }
                    )

                # 異常検出モデルを保存
                self.anomaly_detectors[column] = {
                    "mean": mean,
                    "std": std,
                    "threshold": threshold,
                    "anomaly_count": len(anomalies),
                }

        return anomalies

    async def forecast(self, column: str, periods: int = 5) -> List[float]:
        """将来値の予測"""
        predictions = []

        if column in self.time_series_models:
            model = self.time_series_models[column]

            # 移動平均ベースの予測
            if "data" in model and model["data"]:
                # 最新の移動平均値を使用
                latest_ma = list(model["data"].values())[-1]

                # トレンドを考慮
                if "trend" in model:
                    slope = model["trend"]["slope"]
                    for i in range(periods):
                        prediction = latest_ma + (slope * (i + 1))
                        predictions.append(prediction)
                else:
                    # トレンドがない場合は最新値を繰り返す
                    predictions = [latest_ma] * periods

        return predictions

    def get_model_summary(self) -> Dict[str, Any]:
        """モデルの概要を取得"""
        return {
            "time_series_models": list(self.time_series_models.keys()),
            "anomaly_detectors": list(self.anomaly_detectors.keys()),
            "total_models": len(self.time_series_models) + len(self.anomaly_detectors),
            "trained": self.trained,
        }


class AnalyticsEngine:
    """分析エンジン"""

    def __init__(self):
        """初期化メソッド"""
        self.ml_models = {}  # 機械学習モデル格納用
        self.prediction_model = PredictionModel()  # 予測モデル

    async def analyze_commit_patterns(self, df: pd.DataFrame) -> AnalyticsResult:
        """コミットパターン分析"""
        insights = []
        predictions = {}
        metrics = {}

        if df.empty:
            return self._empty_result(AnalyticsType.COMMIT_PATTERN)

        # 基本統計
        metrics["total_commits"] = len(df)
        metrics["approval_rate"] = df["approved"].mean() * 100
        metrics["avg_execution_time"] = df["execution_time"].mean()
        metrics["avg_complexity"] = df["complexity"].mean()

        # プロトコル別分析
        protocol_stats = (
            df.groupby("protocol")
            .agg(
                {
                    "approved": ["count", "mean"],
                    "execution_time": "mean",
                    "complexity": "mean",
                }
            )
            .round(2)
        )

        # MultiIndexを処理しやすい形に変換
        protocol_distribution = {}
        for protocol in protocol_stats.index:
            protocol_distribution[protocol] = {
                "count": int(protocol_stats.loc[protocol, ("approved", "count")]),
                "approval_rate": float(
                    protocol_stats.loc[protocol, ("approved", "mean")]
                ),
                "avg_execution_time": float(
                    protocol_stats.loc[protocol, ("execution_time", "mean")]
                ),
                "avg_complexity": float(
                    protocol_stats.loc[protocol, ("complexity", "mean")]
                ),
            }

        metrics["protocol_distribution"] = protocol_distribution

        # 時系列分析
        df["hour"] = df["timestamp"].dt.hour
        hourly_commits = df.groupby("hour").size()
        peak_hour = hourly_commits.idxmax()

        insights.append(f"📊 ピークコミット時間: {peak_hour}時台")
        insights.append(f"⚡ 平均実行時間: {metrics['avg_execution_time']:0.1f}秒")

        # 予測
        if len(df) > 10:
            # 簡易的な次回コミット時間予測
            commit_intervals = df["timestamp"].diff().dropna()
            avg_interval = commit_intervals.mean()
            next_commit = df["timestamp"].iloc[-1] + avg_interval
            predictions["next_commit_time"] = next_commit.isoformat()
            predictions["expected_protocol"] = df["protocol"].mode()[0]

        # 推奨事項
        recommendations = []
        if metrics["avg_execution_time"] > 10:
            recommendations.append(
                "🚀 実行時間が長いため、Lightning Protocol の活用を推奨"
            )
        if metrics["approval_rate"] < 90:
            recommendations.append("⚠️ 承認率が低下傾向。品質チェックの強化を推奨")

        return AnalyticsResult(
            type=AnalyticsType.COMMIT_PATTERN,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.85,
        )

    async def analyze_sage_performance(self, df: pd.DataFrame) -> AnalyticsResult:
        """4賢者パフォーマンス分析"""
        insights = []
        predictions = {}
        metrics = {}

        if df.empty:
            return self._empty_result(AnalyticsType.SAGE_PERFORMANCE)

        # 賢者別パフォーマンス
        sage_stats = (
            df.groupby("sage_name")
            .agg({"approval": ["count", "mean"], "risk_score": "mean"})
            .round(3)
        )

        # MultiIndexを処理しやすい形に変換
        sage_performance = {}
        for sage in sage_stats.index:
            sage_performance[sage] = {
                "consultation_count": int(sage_stats.loc[sage, ("approval", "count")]),
                "approval_rate": float(sage_stats.loc[sage, ("approval", "mean")]),
                "avg_risk_score": float(sage_stats.loc[sage, ("risk_score", "mean")]),
            }

        metrics["sage_performance"] = sage_performance

        # 賢者間の相関分析
        sage_approvals = df.pivot_table(
            index="timestamp", columns="sage_name", values="approval", aggfunc="mean"
        )

        if len(sage_approvals.columns) > 1:
            correlation = sage_approvals.corr()
            metrics["sage_correlation"] = correlation.to_dict()

            # 高相関ペアの検出
            high_corr_pairs = []
            for i in range(len(correlation.columns)):
                for j in range(i + 1, len(correlation.columns)):
                    corr_value = correlation.iloc[i, j]
                    if corr_value > 0.7:
                        high_corr_pairs.append(
                            {
                                "pair": f"{correlation.columns[i]} - {correlation.columns[j]}",
                                "correlation": corr_value,
                            }
                        )

            if high_corr_pairs:
                insights.append(f"🤝 高相関賢者ペア検出: {len(high_corr_pairs)}組")

        # プロトコル別の賢者承認率
        protocol_sage_approval = df.groupby(["protocol", "sage_name"])[
            "approval"
        ].mean()

        # MultiIndexを処理しやすい形に変換
        approval_dict = {}
        for (protocol, sage_name), approval_rate in protocol_sage_approval.items():
            if protocol not in approval_dict:
                approval_dict[protocol] = {}
            approval_dict[protocol][sage_name] = float(approval_rate)

        metrics["protocol_sage_approval"] = approval_dict

        # 推奨事項
        recommendations = []
        for sage, stats in sage_stats.iterrows():
            approval_rate = stats[("approval", "mean")] * 100
            if approval_rate < 80:
                recommendations.append(f"⚠️ {sage}の承認率が{approval_rate:0.1f}%と低い")

        return AnalyticsResult(
            type=AnalyticsType.SAGE_PERFORMANCE,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.90,
        )

    async def predict_system_health(
        self, commit_df: pd.DataFrame, system_metrics: Dict
    ) -> AnalyticsResult:
        """システムヘルス予測"""
        insights = []
        predictions = {}
        metrics = {}

        # 現在のヘルススコア計算
        health_score = 100.0

        # エラー率による減点
        if system_metrics["error_logs"] > 100:
            health_score -= 20
            insights.append("⚠️ エラーログが多数検出")

        # 警告率による減点
        if system_metrics["warning_logs"] > 500:
            health_score -= 10
            insights.append("⚠️ 警告ログが増加傾向")

        # コミット承認率による評価
        if not commit_df.empty:
            approval_rate = commit_df["approved"].mean() * 100
            if approval_rate < 80:
                health_score -= 15
                insights.append(f"📉 コミット承認率が{approval_rate:0.1f}%と低下")

        metrics["current_health_score"] = health_score
        metrics["error_rate"] = system_metrics["error_logs"] / max(
            system_metrics["total_log_files"], 1
        )
        metrics["warning_rate"] = system_metrics["warning_logs"] / max(
            system_metrics["total_log_files"], 1
        )

        # ヘルス予測（簡易版）
        if health_score >= 80:
            predictions["next_24h_health"] = "良好"
            predictions["maintenance_required"] = False
        elif health_score >= 60:
            predictions["next_24h_health"] = "注意"
            predictions["maintenance_required"] = True
            predictions["maintenance_type"] = "予防的メンテナンス"
        else:
            predictions["next_24h_health"] = "要対応"
            predictions["maintenance_required"] = True
            predictions["maintenance_type"] = "緊急メンテナンス"

        # 推奨事項
        recommendations = []
        if health_score < 80:
            recommendations.append("🔧 システムヘルスチェックの実行を推奨")
        if metrics["error_rate"] > 0.1:
            recommendations.append("🚨 エラーログの詳細分析が必要")

        return AnalyticsResult(
            type=AnalyticsType.SYSTEM_HEALTH,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.75,
        )

    async def analyze_protocol_efficiency(
        self, commit_df: pd.DataFrame
    ) -> AnalyticsResult:
        """プロトコル効率分析"""
        insights = []
        predictions = {}
        metrics = {}

        if commit_df.empty:
            return self._empty_result(AnalyticsType.PROTOCOL_EFFICIENCY)

        # プロトコル別の効率メトリクス
        protocol_efficiency = (
            commit_df.groupby("protocol")
            .agg(
                {
                    "execution_time": ["mean", "std", "min", "max"],
                    "approved": "mean",
                    "files_changed": "mean",
                    "complexity": "mean",
                }
            )
            .round(2)
        )

        # 効率スコアの計算（実行時間と承認率のバランス）
        efficiency_scores = {}
        for protocol in protocol_efficiency.index:
            exec_time = protocol_efficiency.loc[protocol, ("execution_time", "mean")]
            approval_rate = protocol_efficiency.loc[protocol, ("approved", "mean")]

            # 効率スコア = 承認率 / (1 + log(実行時間))
            efficiency_score = approval_rate / (1 + np.log1p(exec_time))
            efficiency_scores[protocol] = round(efficiency_score, 3)

        metrics["efficiency_scores"] = efficiency_scores
        # Convert protocol_efficiency to a JSON-serializable format
        protocol_stats_dict = {}
        for protocol in protocol_efficiency.index:
            protocol_stats_dict[protocol] = {
                "execution_time_mean": float(
                    protocol_efficiency.loc[protocol, ("execution_time", "mean")]
                ),
                "execution_time_std": float(
                    protocol_efficiency.loc[protocol, ("execution_time", "std")]
                ),
                "execution_time_min": float(
                    protocol_efficiency.loc[protocol, ("execution_time", "min")]
                ),
                "execution_time_max": float(
                    protocol_efficiency.loc[protocol, ("execution_time", "max")]
                ),
                "approved_mean": float(
                    protocol_efficiency.loc[protocol, ("approved", "mean")]
                ),
                "files_changed_mean": float(
                    protocol_efficiency.loc[protocol, ("files_changed", "mean")]
                ),
                "complexity_mean": float(
                    protocol_efficiency.loc[protocol, ("complexity", "mean")]
                ),
            }
        metrics["protocol_stats"] = protocol_stats_dict

        # 最も効率的なプロトコル
        best_protocol = max(efficiency_scores, key=efficiency_scores.get)
        insights.append(
            f"🏆 最も効率的なプロトコル: {best_protocol} (スコア: {efficiency_scores[best_protocol]})"
        )

        # 時系列での効率変化分析
        await self.prediction_model.train_time_series(commit_df, "execution_time")
        future_exec_times = await self.prediction_model.forecast(
            "execution_time", periods=5
        )

        if future_exec_times:
            predictions["execution_time_forecast"] = future_exec_times
            trend = "増加" if future_exec_times[-1] > future_exec_times[0] else "減少"
            insights.append(f"📈 実行時間は今後{trend}傾向と予測")

        # 推奨事項
        recommendations = []
        for protocol, score in efficiency_scores.items():
            if score < 0.5:
                recommendations.append(
                    f"⚡ {protocol}の効率改善が必要（現在のスコア: {score}）"
                )

        return AnalyticsResult(
            type=AnalyticsType.PROTOCOL_EFFICIENCY,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.82,
        )

    async def predict_errors(
        self, commit_df: pd.DataFrame, system_metrics: Dict
    ) -> AnalyticsResult:
        """エラー予測分析"""
        insights = []
        predictions = {}
        metrics = {}

        # エラー率の計算
        current_error_rate = system_metrics.get("error_logs", 0) / max(
            system_metrics.get("total_log_files", 1), 1
        )
        metrics["current_error_rate"] = round(current_error_rate, 4)

        # コミット複雑度とエラーの相関分析
        if not commit_df.empty and "complexity" in commit_df.columns:
            # 複雑度による異常検出
            anomalies = await self.prediction_model.detect_anomalies(
                commit_df, "complexity"
            )

            if anomalies:
                metrics["complexity_anomalies"] = len(anomalies)
                insights.append(f"⚠️ {len(anomalies)}件の複雑度異常を検出")

                # 高複雑度コミットの特定
                high_complexity_threshold = commit_df["complexity"].quantile(0.9)
                high_complexity_commits = commit_df[
                    commit_df["complexity"] > high_complexity_threshold
                ]

                if not high_complexity_commits.empty:
                    predictions["high_risk_protocols"] = (
                        high_complexity_commits["protocol"]
                        .value_counts()
                        .head(3)
                        .to_dict()
                    )

        # エラー発生予測
        error_probability = min(current_error_rate * 2 + 0.1, 1.0)  # 簡易予測
        predictions["error_probability_24h"] = round(error_probability, 2)

        if error_probability > 0.3:
            insights.append(
                f"🚨 24時間以内のエラー発生確率: {error_probability*100:0.0f}%"
            )

        # 推奨事項
        recommendations = []
        if current_error_rate > 0.05:
            recommendations.append("📋 エラーログの詳細分析を実施")
        if metrics.get("complexity_anomalies", 0) > 5:
            recommendations.append("🔍 高複雑度コミットのコードレビュー強化")

        return AnalyticsResult(
            type=AnalyticsType.ERROR_PREDICTION,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.78,
        )

    async def detect_bottlenecks(
        self, commit_df: pd.DataFrame, sage_df: pd.DataFrame
    ) -> AnalyticsResult:
        """ボトルネック検出"""
        insights = []
        predictions = {}
        metrics = {}

        bottlenecks = []

        # 実行時間のボトルネック検出
        if not commit_df.empty:
            # 実行時間の異常値検出
            exec_time_anomalies = await self.prediction_model.detect_anomalies(
                commit_df, "execution_time"
            )

            if exec_time_anomalies:
                bottlenecks.extend(
                    [
                        {
                            "type": "execution_time",
                            "severity": a["severity"],
                            "value": a["value"],
                        }
                        for a in exec_time_anomalies
                    ]
                )

                insights.append(
                    f"⏱️ {len(exec_time_anomalies)}件の実行時間ボトルネックを検出"
                )

        # 賢者承認のボトルネック検出
        if not sage_df.empty:
            # 賢者別の平均承認時間（リスクスコアを代理指標として使用）
            sage_bottlenecks = sage_df.groupby("sage_name").agg(
                {"risk_score": "mean", "approval": "count"}
            )

            # 高リスクスコアの賢者を特定
            high_risk_sages = sage_bottlenecks[sage_bottlenecks["risk_score"] > 0.7]

            if not high_risk_sages.empty:
                for sage in high_risk_sages.index:
                    bottlenecks.append(
                        {
                            "type": "sage_approval",
                            "sage": sage,
                            "avg_risk_score": float(
                                high_risk_sages.loc[sage, "risk_score"]
                            ),
                        }
                    )

                insights.append(f"🧙‍♂️ {len(high_risk_sages)}名の賢者で承認遅延の可能性")

        metrics["total_bottlenecks"] = len(bottlenecks)
        metrics["bottleneck_details"] = bottlenecks

        # ボトルネック解消の予測
        if bottlenecks:
            predictions["resolution_time_hours"] = len(bottlenecks) * 2  # 簡易推定
            predictions["impact_reduction"] = min(len(bottlenecks) * 0.15, 0.5)

        # 推奨事項
        recommendations = []
        if any(b["type"] == "execution_time" for b in bottlenecks):
            recommendations.append("⚡ Lightning Protocolの適用範囲拡大")
        if any(b["type"] == "sage_approval" for b in bottlenecks):
            recommendations.append("👥 賢者間の負荷分散を検討")

        return AnalyticsResult(
            type=AnalyticsType.BOTTLENECK_DETECTION,
            timestamp=datetime.now(),
            metrics=metrics,
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.85,
        )

    def _empty_result(self, analytics_type: AnalyticsType) -> AnalyticsResult:
        """空の結果を返す"""
        return AnalyticsResult(
            type=analytics_type,
            timestamp=datetime.now(),
            metrics={},
            insights=["データが不足しています"],
            predictions={},
            recommendations=["より多くのデータ収集が必要です"],
            confidence=0.0,
        )


class PredictiveAnalytics:
    """予測分析エンジン"""

    def __init__(self):
        """初期化メソッド"""
        self.models = {}

    async def train_models(self, commit_df: pd.DataFrame, sage_df: pd.DataFrame):
        """予測モデルの訓練"""
        logger.info("🤖 予測モデルの訓練開始")

        # ここでは簡易的な統計モデルを使用
        # 実際のプロジェクトではscikit-learn等を使用

        if not commit_df.empty:
            # コミット間隔予測モデル
            commit_intervals = commit_df["timestamp"].diff().dropna()
            self.models["commit_interval"] = {
                "mean": commit_intervals.mean(),
                "std": commit_intervals.std(),
            }

            # プロトコル選択予測モデル
            protocol_dist = commit_df["protocol"].value_counts(normalize=True)
            self.models["protocol_selection"] = protocol_dist.to_dict()

        logger.info("✅ 予測モデルの訓練完了")

    async def predict_next_commit(self) -> Dict[str, Any]:
        """次回コミット予測"""
        predictions = {}

        if "commit_interval" in self.models:
            model = self.models["commit_interval"]
            # 正規分布を仮定した予測
            next_interval = np.random.normal(
                model["mean"].total_seconds(), model["std"].total_seconds()
            )
            predictions["next_commit_in_seconds"] = max(0, next_interval)
            predictions["confidence"] = 0.7

        if "protocol_selection" in self.models:
            # 確率に基づくプロトコル予測
            protocols = list(self.models["protocol_selection"].keys())
            probabilities = list(self.models["protocol_selection"].values())
            predictions["likely_protocol"] = np.random.choice(
                protocols, p=probabilities
            )

        return predictions


class AnalyticsReporter:
    """分析レポート生成器"""

    def __init__(self, project_root: Path):
        """初期化メソッド"""
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "analytics_reports"
        self.reports_dir.mkdir(exist_ok=True)

    async def generate_comprehensive_report(
        self, results: List[AnalyticsResult]
    ) -> Path:
        """包括的レポート生成"""
        timestamp = datetime.now()
        report = {
            "title": "エルダーズギルド データアナリティクスレポート",
            "generated_at": timestamp.isoformat(),
            "summary": self._generate_summary(results),
            "detailed_results": [self._result_to_dict(r) for r in results],
            "executive_insights": self._generate_executive_insights(results),
            "action_items": self._generate_action_items(results),
        }

        # レポートファイル保存
        report_file = (
            self.reports_dir
            / f"analytics_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 包括的レポート生成: {report_file}")
        return report_file

    def _generate_summary(self, results: List[AnalyticsResult]) -> Dict[str, Any]:
        """サマリー生成"""
        return {
            "total_analyses": len(results),
            "average_confidence": np.mean([r.confidence for r in results]),
            "key_findings": sum(len(r.insights) for r in results),
            "recommendations": sum(len(r.recommendations) for r in results),
        }

    def _result_to_dict(self, result: AnalyticsResult) -> Dict[str, Any]:
        """結果を辞書に変換"""
        return {
            "type": result.type.value,
            "timestamp": result.timestamp.isoformat(),
            "metrics": result.metrics,
            "insights": result.insights,
            "predictions": result.predictions,
            "recommendations": result.recommendations,
            "confidence": result.confidence,
        }

    def _generate_executive_insights(self, results: List[AnalyticsResult]) -> List[str]:
        """エグゼクティブ向け洞察"""
        insights = []

        # 各分析結果から重要な洞察を抽出
        for result in results:
            if result.confidence > 0.8 and result.insights:
                insights.extend(result.insights[:2])  # 上位2つの洞察

        return insights[:5]  # 最大5つ

    def _generate_action_items(self, results: List[AnalyticsResult]) -> List[str]:
        """アクションアイテム生成"""
        action_items = []

        # 推奨事項を優先度付けして集約
        all_recommendations = []
        for result in results:
            for rec in result.recommendations:
                all_recommendations.append(
                    {
                        "recommendation": rec,
                        "confidence": result.confidence,
                        "type": result.type.value,
                    }
                )

        # 信頼度でソート
        all_recommendations.sort(key=lambda x: x["confidence"], reverse=True)

        # 上位のアクションアイテムを選択
        for item in all_recommendations[:5]:
            action_items.append(f"[{item['type']}] {item['recommendation']}")

        return action_items

    async def generate_html_report(self, results: List[AnalyticsResult]) -> Path:
        """インタラクティブHTMLレポート生成"""
        timestamp = datetime.now()

        # HTML テンプレート
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>エルダーズギルド アナリティクスレポート - {timestamp.strftime('%Y年%m月%d日')}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Orbitron', monospace;
            background: linear-gradient(135deg, #87CEEB 0%, #98FB98 50%, #FFB6C1 100%);
            color: #2F4F4F;
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        h1 {{
            background: linear-gradient(135deg, #4169E1, #00CED1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 30px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #f0f0f0, #e0e0e0);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #4169E1;
        }}

        .analysis-section {{
            margin: 30px 0;
            padding: 20px;
            background: rgba(255,255,255,0.8);
            border-radius: 10px;
            border-left: 5px solid #4169E1;
        }}

        .insights-list {{
            list-style: none;
            padding: 10px 0;
        }}

        .insights-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}

        .recommendations {{
            background: #f0f8ff;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}

        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .confidence-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4169E1, #00CED1);
            transition: width 1s ease-in-out;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}

        .live-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #32CD32;
            border-radius: 50%;
            animation: pulse 2s infinite;
            margin-right: 10px;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>エルダーズギルド アナリティクスレポート</h1>
        <p style="text-align: center; color: #666;">
            <span class="live-indicator"></span>
            生成日時: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        </p>

        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{len(results)}</div>
                <div>実行済み分析</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{sum(len(r.insights) for r in results)}</div>
                <div>検出された洞察</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{sum(len(r.recommendations) for r in results)}</div>
                <div>推奨アクション</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{np.mean([r.confidence for r in results]):0.1%}</div>
                <div>平均信頼度</div>
            </div>
        </div>
"""

        # 各分析結果をHTMLに追加
        for result in results:
            confidence_width = int(result.confidence * 100)
            html_content += f"""
        <div class="analysis-section">
            <h2>{result.type.value.replace('_', ' ').title()}</h2>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence_width}%"></div>
            </div>
            <p>信頼度: {result.confidence:0.1%}</p>

            <h3>主要な洞察</h3>
            <ul class="insights-list">
"""
            for insight in result.insights[:5]:
                html_content += f"                <li>{insight}</li>\n"

            html_content += """            </ul>

            <div class="recommendations">
                <h3>推奨事項</h3>
                <ul>
"""
            for rec in result.recommendations:
                html_content += f"                    <li>{rec}</li>\n"

            html_content += """                </ul>
            </div>
        </div>
"""

        # チャートセクション
        html_content += (
            """
        <div class="chart-container">
            <h2>分析結果サマリー</h2>
            <canvas id="confidenceChart" width="400" height="200"></canvas>
        </div>

        <script>
            // 信頼度チャート
            const ctx = document.getElementById('confidenceChart').getContext('2d');
            const confidenceData = {
                labels: ["""
            + ", ".join([f'"{r.type.value}"' for r in results])
            + """],
                datasets: [{
                    label: '信頼度',
                    data: ["""
            + ", ".join([str(r.confidence) for r in results])
            + """],
                    backgroundColor: 'rgba(65, 105, 225, 0.6)',
                    borderColor: 'rgba(65, 105, 225, 1)',
                    borderWidth: 2
                }]
            };

            new Chart(ctx, {
                type: 'bar',
                data: confidenceData,
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
        </script>
    </div>
</body>
</html>"""
        )

        # HTMLファイル保存
        html_file = (
            self.reports_dir
            / f"analytics_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        )
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"📊 インタラクティブHTMLレポート生成: {html_file}")
        return html_file

    async def generate_api_response(
        self, results: List[AnalyticsResult]
    ) -> Dict[str, Any]:
        """API用のレスポンスデータ生成"""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(results),
            "results": [self._result_to_dict(r) for r in results],
            "executive_insights": self._generate_executive_insights(results),
            "action_items": self._generate_action_items(results),
            "visualizations": {
                "confidence_scores": {r.type.value: r.confidence for r in results},
                "insights_count": {r.type.value: len(r.insights) for r in results},
                "recommendations_count": {
                    r.type.value: len(r.recommendations) for r in results
                },
            },
        }


class DataAnalyticsPlatform:
    """高度データアナリティクスプラットフォーム メインクラス"""

    def __init__(self, project_root: Path):
        """初期化メソッド"""
        self.project_root = Path(project_root)
        self.collector = DataCollector(self.project_root)
        self.analytics = AnalyticsEngine()
        self.predictive = PredictiveAnalytics()
        self.reporter = AnalyticsReporter(self.project_root)

        logger.info("📊 データアナリティクスプラットフォーム初期化完了")

    async def run_full_analysis(self) -> Path:
        """完全分析実行"""
        logger.info("🚀 完全分析開始")

        try:
            # データ収集フェーズ
            logger.info("📥 データ収集フェーズ")
            commit_df = await self.collector.collect_commit_data()
            sage_df = await self.collector.collect_sage_consultation_data()
            system_metrics = await self.collector.collect_system_metrics()

            # 予測モデル訓練
            await self.predictive.train_models(commit_df, sage_df)

            # 分析実行フェーズ
            logger.info("🔍 分析実行フェーズ")
            results = []

            # コミットパターン分析
            commit_analysis = await self.analytics.analyze_commit_patterns(commit_df)
            results.append(commit_analysis)

            # 4賢者パフォーマンス分析
            sage_analysis = await self.analytics.analyze_sage_performance(sage_df)
            results.append(sage_analysis)

            # システムヘルス予測
            health_prediction = await self.analytics.predict_system_health(
                commit_df, system_metrics
            )
            results.append(health_prediction)

            # プロトコル効率分析
            protocol_efficiency = await self.analytics.analyze_protocol_efficiency(
                commit_df
            )
            results.append(protocol_efficiency)

            # エラー予測
            error_prediction = await self.analytics.predict_errors(
                commit_df, system_metrics
            )
            results.append(error_prediction)

            # ボトルネック検出
            bottleneck_detection = await self.analytics.detect_bottlenecks(
                commit_df, sage_df
            )
            results.append(bottleneck_detection)

            # レポート生成フェーズ
            logger.info("📋 レポート生成フェーズ")
            json_report_path = await self.reporter.generate_comprehensive_report(
                results
            )
            html_report_path = await self.reporter.generate_html_report(results)

            logger.info("✅ 完全分析完了")
            return {
                "json_report": json_report_path,
                "html_report": html_report_path,
                "api_data": await self.reporter.generate_api_response(results),
            }

        except Exception as e:
            logger.error(f"❌ 分析中にエラー発生: {e}")
            raise


# テスト実行
async def main():
    """テスト実行"""
    platform = DataAnalyticsPlatform(Path("/home/aicompany/ai_co"))
    results = await platform.run_full_analysis()
    print(f"📊 分析レポート生成完了:")
    print(f"  - JSONレポート: {results['json_report']}")
    print(f"  - HTMLレポート: {results['html_report']}")
    print(f"  - API データ利用可能")


if __name__ == "__main__":
    asyncio.run(main())

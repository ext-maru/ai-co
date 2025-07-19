#!/usr/bin/env python3
"""
メトリクスアグリゲーター
4賢者システムからのメトリクス収集・統合
"""

import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsAggregator:
    """メトリクス収集・統合クラス"""

    def __init__(self):
        self.metrics_sources = {
            "knowledge_sage": self._get_knowledge_metrics,
            "task_sage": self._get_task_metrics,
            "incident_sage": self._get_incident_metrics,
            "rag_sage": self._get_rag_metrics,
            "system": self._get_system_metrics,
        }

        self.metric_definitions = {
            "sage_response_time": {
                "unit": "ms",
                "type": "gauge",
                "description": "賢者応答時間",
            },
            "sage_accuracy": {
                "unit": "percent",
                "type": "gauge",
                "description": "賢者精度",
            },
            "task_completion_rate": {
                "unit": "percent",
                "type": "gauge",
                "description": "タスク完了率",
            },
            "incident_resolution_time": {
                "unit": "minutes",
                "type": "gauge",
                "description": "インシデント解決時間",
            },
            "knowledge_queries_per_minute": {
                "unit": "qpm",
                "type": "counter",
                "description": "知識クエリ数/分",
            },
            "system_cpu_usage": {
                "unit": "percent",
                "type": "gauge",
                "description": "CPU使用率",
            },
            "system_memory_usage": {
                "unit": "percent",
                "type": "gauge",
                "description": "メモリ使用率",
            },
            "error_rate": {
                "unit": "percent",
                "type": "gauge",
                "description": "エラー率",
            },
        }

        # メトリクスキャッシュ
        self.cache = {}
        self.cache_ttl = 60  # 1分

    def get_metric_data(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "minute",
    ) -> List[Dict[str, Any]]:
        """メトリクスデータ取得"""
        try:
            # キャッシュチェック
            cache_key = f"{metric_name}_{start_date}_{end_date}_{granularity}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_ttl:
                    return cached_data

            # データ生成（実際の実装では各賢者のAPIから取得）
            data = self._generate_metric_data(
                metric_name, start_date, end_date, granularity
            )

            # キャッシュ保存
            self.cache[cache_key] = (data, datetime.now())

            return data

        except Exception as e:
            logger.error(f"メトリクスデータ取得エラー: {e}")
            return []

    def get_current_metrics(self, source: str = None) -> Dict[str, Any]:
        """現在のメトリクス取得"""
        try:
            if source and source in self.metrics_sources:
                return self.metrics_sources[source]()

            # 全ソースから収集
            all_metrics = {}
            for source_name, source_func in self.metrics_sources.items():
                all_metrics[source_name] = source_func()

            return all_metrics

        except Exception as e:
            logger.error(f"現在メトリクス取得エラー: {e}")
            return {}

    def aggregate_metrics(
        self, metrics: List[Dict[str, Any]], aggregation_type: str = "avg"
    ) -> Dict[str, Any]:
        """メトリクス集約"""
        if not metrics:
            return {}

        aggregated = {}

        # メトリクス名でグループ化
        metric_groups = {}
        for metric in metrics:
            name = metric.get("name")
            if name not in metric_groups:
                metric_groups[name] = []
            metric_groups[name].append(metric.get("value", 0))

        # 集約処理
        for name, values in metric_groups.items():
            if aggregation_type == "avg":
                aggregated[name] = np.mean(values)
            elif aggregation_type == "sum":
                aggregated[name] = np.sum(values)
            elif aggregation_type == "max":
                aggregated[name] = np.max(values)
            elif aggregation_type == "min":
                aggregated[name] = np.min(values)
            elif aggregation_type == "count":
                aggregated[name] = len(values)

        return aggregated

    def get_metric_metadata(self, metric_name: str) -> Dict[str, Any]:
        """メトリクスメタデータ取得"""
        return self.metric_definitions.get(
            metric_name,
            {"unit": "unknown", "type": "gauge", "description": "不明なメトリクス"},
        )

    # プライベートメソッド
    def _generate_metric_data(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str,
    ) -> List[Dict[str, Any]]:
        """メトリクスデータ生成（モック）"""
        data = []

        # 時間間隔計算
        if granularity == "minute":
            interval = timedelta(minutes=1)
        elif granularity == "hour":
            interval = timedelta(hours=1)
        elif granularity == "day":
            interval = timedelta(days=1)
        else:
            interval = timedelta(minutes=5)

        # ベース値とパターン設定
        base_values = {
            "sage_response_time": 50,
            "sage_accuracy": 95,
            "task_completion_rate": 85,
            "incident_resolution_time": 15,
            "knowledge_queries_per_minute": 100,
            "system_cpu_usage": 45,
            "system_memory_usage": 60,
            "error_rate": 0.5,
        }

        base_value = base_values.get(metric_name, 50)

        # データポイント生成
        current_time = start_date
        while current_time <= end_date:
            # 時間帯による変動
            hour_factor = 1 + 0.3 * np.sin(2 * np.pi * current_time.hour / 24)

            # 曜日による変動
            day_factor = 1 + 0.2 * np.sin(2 * np.pi * current_time.weekday() / 7)

            # ランダムノイズ
            noise = random.gauss(0, base_value * 0.1)

            # 最終値計算
            value = base_value * hour_factor * day_factor + noise

            # 異常値の挿入（5%の確率）
            if random.random() < 0.05:
                value *= random.choice([0.3, 2.5])

            data.append(
                {
                    "timestamp": current_time.isoformat(),
                    "value": float(max(0, value)),  # 明示的にfloatに変換
                    "name": metric_name,
                }
            )

            current_time += interval

        return data

    def _get_knowledge_metrics(self) -> Dict[str, float]:
        """ナレッジ賢者メトリクス"""
        return {
            "response_time": random.gauss(45, 5),
            "accuracy": random.gauss(98, 1),
            "queries_per_minute": random.gauss(120, 20),
            "cache_hit_rate": random.gauss(85, 5),
            "knowledge_base_size": 15420,
        }

    def _get_task_metrics(self) -> Dict[str, float]:
        """タスク賢者メトリクス"""
        return {
            "response_time": random.gauss(55, 8),
            "accuracy": random.gauss(96, 2),
            "active_tasks": random.randint(10, 50),
            "completion_rate": random.gauss(87, 5),
            "average_task_duration": random.gauss(25, 10),
        }

    def _get_incident_metrics(self) -> Dict[str, float]:
        """インシデント賢者メトリクス"""
        return {
            "response_time": random.gauss(30, 5),
            "accuracy": random.gauss(99, 0.5),
            "active_incidents": random.randint(0, 5),
            "resolution_time": random.gauss(12, 5),
            "false_positive_rate": random.gauss(2, 1),
        }

    def _get_rag_metrics(self) -> Dict[str, float]:
        """RAG賢者メトリクス"""
        return {
            "response_time": random.gauss(65, 10),
            "accuracy": random.gauss(94, 3),
            "retrieval_precision": random.gauss(92, 3),
            "retrieval_recall": random.gauss(88, 4),
            "index_size": 8750000,
        }

    def _get_system_metrics(self) -> Dict[str, float]:
        """システムメトリクス"""
        return {
            "cpu_usage": random.gauss(45, 15),
            "memory_usage": random.gauss(62, 10),
            "disk_io": random.gauss(78, 20),
            "network_throughput": random.gauss(125, 30),
            "active_connections": random.randint(50, 200),
            "error_rate": random.gauss(0.5, 0.3),
        }


if __name__ == "__main__":
    # テスト実行
    aggregator = MetricsAggregator()

    print("=== メトリクスアグリゲーター テスト ===")

    # 現在のメトリクス取得
    current = aggregator.get_current_metrics()
    print("\n現在のメトリクス:")
    for source, metrics in current.items():
        print(f"\n{source}:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.2f}")

    # 時系列データ取得
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)

    time_series = aggregator.get_metric_data(
        "sage_response_time", start_date, end_date, "hour"
    )

    print(f"\n過去24時間の sage_response_time データポイント数: {len(time_series)}")
    print(f"最初のデータ: {time_series[0] if time_series else 'なし'}")
    print(f"最後のデータ: {time_series[-1] if time_series else 'なし'}")

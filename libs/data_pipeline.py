#!/usr/bin/env python3
"""
データ処理パイプライン
リアルタイム・バッチ処理の統合フレームワーク
"""

import asyncio
import json
import logging
import queue
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessingPipeline:
    """データ処理パイプライン"""

    def __init__(self):
        """初期化メソッド"""
        # 処理ステージ
        self.stages = []

        # データキュー
        self.input_queue = queue.Queue(maxsize=10000)
        self.output_queue = queue.Queue(maxsize=10000)

        # リアルタイムバッファ
        self.realtime_buffer = deque(maxlen=1000)

        # バッチ設定
        self.batch_size = 10  # より小さなバッチサイズ
        self.batch_timeout = 1.0  # より短いタイムアウト

        # 処理スレッド
        self.processing_thread = None
        self.is_running = False

        # メトリクス
        self.metrics = {
            "processed_count": 0,
            "error_count": 0,
            "average_latency": 0,
            "throughput": 0,
        }

        # データ品質ルール
        self.quality_rules = []

        # 変換関数
        self.transformers = {}

    def add_stage(self, name: str, processor: Callable) -> "DataProcessingPipeline":
        """処理ステージ追加"""
        self.stages.append(
            {
                "name": name,
                "processor": processor,
                "metrics": {"processed": 0, "errors": 0, "latency": []},
            }
        )
        return self

    def add_quality_rule(
        self, name: str, validator: Callable
    ) -> "DataProcessingPipeline":
        """データ品質ルール追加"""
        self.quality_rules.append(
            {"name": name, "validator": validator, "violations": 0}
        )
        return self

    def add_transformer(
        self, name: str, transformer: Callable
    ) -> "DataProcessingPipeline":
        """データ変換関数追加"""
        self.transformers[name] = transformer
        return self

    def start(self):
        """パイプライン開始"""
        if self.is_running:
            logger.warning("パイプラインは既に実行中です")
            return

        self.is_running = True
        self.processing_thread = threading.Thread(target=self._process_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        logger.info("データ処理パイプラインを開始しました")

    def stop(self):
        """パイプライン停止"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=10)  # より長いタイムアウト

        logger.info("データ処理パイプラインを停止しました")

    def wait_for_processing(self, timeout: float = 5.0) -> bool:
        """処理完了待機"""
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.input_queue.empty() and self.output_queue.qsize() >= 0:
                time.sleep(0.1)  # 少し待機
                if self.input_queue.empty():  # 再確認
                    return True
            time.sleep(0.1)
        return False

    def submit(self, data: Dict[str, Any]) -> bool:
        """データ投入"""
        try:
            # タイムスタンプ追加
            data["_submitted_at"] = datetime.now().isoformat()

            # リアルタイムバッファに追加
            self.realtime_buffer.append(data)

            # キューに追加
            self.input_queue.put(data, block=False)
            return True

        except queue.Full:
            logger.error("入力キューが満杯です")
            return False

    def submit_batch(self, data_list: List[Dict[str, Any]]) -> int:
        """バッチデータ投入"""
        submitted = 0
        for data in data_list:
            if self.submit(data):
                submitted += 1
        return submitted

    def get_results(self, max_items: int = 100) -> List[Dict[str, Any]]:
        """処理結果取得"""
        results = []
        try:
            while len(results) < max_items:
                result = self.output_queue.get(block=False)
                results.append(result)
        except queue.Empty:
            pass
        return results

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクス取得"""
        stage_metrics = []
        for stage in self.stages:
            latencies = stage["metrics"]["latency"][-100:]  # 最新100件
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            stage_metrics.append(
                {
                    "name": stage["name"],
                    "processed": stage["metrics"]["processed"],
                    "errors": stage["metrics"]["errors"],
                    "average_latency_ms": avg_latency * 1000,
                }
            )

        quality_metrics = []
        for rule in self.quality_rules:
            quality_metrics.append(
                {"name": rule["name"], "violations": rule["violations"]}
            )

        return {
            "pipeline": self.metrics,
            "stages": stage_metrics,
            "quality": quality_metrics,
            "queue_sizes": {
                "input": self.input_queue.qsize(),
                "output": self.output_queue.qsize(),
            },
            "realtime_buffer_size": len(self.realtime_buffer),
        }

    def apply_transformation(
        self, data: Dict[str, Any], transformer_name: str
    ) -> Dict[str, Any]:
        """データ変換適用"""
        if transformer_name in self.transformers:
            return self.transformers[transformer_name](data)
        return data

    # プライベートメソッド
    def _process_loop(self):
        """処理ループ"""
        batch = []
        last_batch_time = time.time()

        while self.is_running:
            try:
                # バッチ収集
                timeout = max(0.1, self.batch_timeout - (time.time() - last_batch_time))

                try:
                    data = self.input_queue.get(timeout=timeout)
                    batch.append(data)
                except queue.Empty:
                    pass

                # バッチ処理実行
                should_process = (
                    len(batch) >= self.batch_size
                    or (time.time() - last_batch_time) >= self.batch_timeout
                )

                if should_process and batch:
                    self._process_batch(batch)
                    batch = []
                    last_batch_time = time.time()

            except Exception as e:
                logger.error(f"処理ループエラー: {e}")
                self.metrics["error_count"] += 1

    def _process_batch(self, batch: List[Dict[str, Any]]):
        """バッチ処理実行"""
        start_time = time.time()

        # データ品質チェック
        valid_data = []
        for data in batch:
            if self._validate_data(data):
                valid_data.append(data)

        # ステージ処理
        current_batch = valid_data
        for stage in self.stages:
            current_batch = self._process_stage(stage, current_batch)

        # 結果をキューに追加
        for result in current_batch:
            result["_processed_at"] = datetime.now().isoformat()
            try:
                self.output_queue.put(result, block=False)
            except queue.Full:
                logger.warning("出力キューが満杯です")

        # メトリクス更新
        processing_time = time.time() - start_time
        self.metrics["processed_count"] += len(batch)
        self.metrics["average_latency"] = processing_time / len(batch) if batch else 0
        self.metrics["throughput"] = (
            len(batch) / processing_time if processing_time > 0 else 0
        )

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """データ品質検証"""
        for rule in self.quality_rules:
            try:
                if not rule["validator"](data):
                    rule["violations"] += 1
                    logger.warning(f"データ品質違反: {rule['name']}")
                    return False
            except Exception as e:
                logger.error(f"品質検証エラー: {e}")
                return False
        return True

    def _process_stage(
        self, stage: Dict[str, Any], batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """ステージ処理実行"""
        results = []

        for data in batch:
            start_time = time.time()
            try:
                # 処理実行
                result = stage["processor"](data)
                if result:
                    results.append(result)

                # メトリクス更新
                stage["metrics"]["processed"] += 1
                latency = time.time() - start_time
                stage["metrics"]["latency"].append(latency)

                # 最新1000件のみ保持
                if len(stage["metrics"]["latency"]) > 1000:
                    stage["metrics"]["latency"] = stage["metrics"]["latency"][-1000:]

            except Exception as e:
                logger.error(f"ステージ処理エラー [{stage['name']}]: {e}")
                stage["metrics"]["errors"] += 1

        return results


# 標準的な処理関数
def enrich_with_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """メタデータ付与"""
    data["enriched"] = True
    data["enriched_at"] = datetime.now().isoformat()
    return data


def normalize_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """値の正規化"""
    if "value" in data:
        # 0-100の範囲に正規化
        data["normalized_value"] = max(0, min(100, data["value"]))
    return data


def aggregate_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """メトリクス集約"""
    if "metrics" in data and isinstance(data["metrics"], list):
        data["aggregated"] = {
            "sum": sum(data["metrics"]),
            "avg": (
                sum(data["metrics"]) / len(data["metrics"]) if data["metrics"] else 0
            ),
            "max": max(data["metrics"]) if data["metrics"] else 0,
            "min": min(data["metrics"]) if data["metrics"] else 0,
        }
    return data


# データ品質バリデーター
def has_required_fields(data: Dict[str, Any]) -> bool:
    """必須フィールドチェック"""
    required = ["timestamp", "value", "source"]
    return all(field in data for field in required)


def value_in_range(data: Dict[str, Any]) -> bool:
    """値範囲チェック"""
    if "value" in data:
        return 0 <= data["value"] <= 1000
    return True


def timestamp_valid(data: Dict[str, Any]) -> bool:
    """タイムスタンプ検証"""
    if "timestamp" in data:
        try:
            datetime.fromisoformat(data["timestamp"])
            return True
        except:
            return False
    return False


if __name__ == "__main__":
    # テスト実行
    pipeline = DataProcessingPipeline()

    # ステージ追加
    pipeline.add_stage("enrich", enrich_with_metadata)
    pipeline.add_stage("normalize", normalize_values)
    pipeline.add_stage("aggregate", aggregate_metrics)

    # 品質ルール追加
    pipeline.add_quality_rule("required_fields", has_required_fields)
    pipeline.add_quality_rule("value_range", value_in_range)
    pipeline.add_quality_rule("timestamp", timestamp_valid)

    # パイプライン開始
    pipeline.start()

    print("=== データ処理パイプライン テスト ===")

    # テストデータ投入
    test_data = [
        {
            "timestamp": datetime.now().isoformat(),
            "value": 75.5,
            "source": "test_sensor",
            "metrics": [10, 20, 30, 40, 50],
        },
        {
            "timestamp": datetime.now().isoformat(),
            "value": 150.0,
            "source": "test_api",
            "metrics": [5, 15, 25],
        },
    ]

    submitted = pipeline.submit_batch(test_data)
    print(f"\n投入データ数: {submitted}")

    # 処理待機
    time.sleep(2)

    # 結果取得
    results = pipeline.get_results()
    print(f"\n処理結果数: {len(results)}")

    for i, result in enumerate(results):
        print(f"\n結果 {i+1}:")
        print(f"  - enriched: {result.get('enriched')}")
        print(f"  - normalized_value: {result.get('normalized_value')}")
        print(f"  - aggregated: {result.get('aggregated')}")

    # メトリクス表示
    metrics = pipeline.get_metrics()
    print(f"\nパイプラインメトリクス:")
    print(f"  - 処理数: {metrics['pipeline']['processed_count']}")
    print(f"  - エラー数: {metrics['pipeline']['error_count']}")
    print(f"  - スループット: {metrics['pipeline']['throughput']:.2f} items/sec")

    # パイプライン停止
    pipeline.stop()

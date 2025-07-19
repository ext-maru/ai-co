#!/usr/bin/env python3
"""
ログ改善用Mixin
既存のワーカーに簡単に適用可能
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional


class ImprovedLoggingMixin:
    """改善されたログ出力を提供するMixin"""

    def __init__(self):
        # タスクの開始時刻を記録
        self._task_start_times: Dict[str, float] = {}
        self._task_metrics: Dict[str, Dict[str, Any]] = {}

    def log_task_start(self, task_id: str, task_type: str = None):
        """タスク開始をログ（シンプル）"""
        self._task_start_times[task_id] = time.time()

        message = f"Task started: {task_id}"
        if task_type:
            message += f" (type: {task_type})"

        self.logger.info(message)

    def log_task_complete(self, task_id: str, result_summary: str = None):
        """タスク完了をログ（データ付き）"""
        duration = None
        if task_id in self._task_start_times:
            duration = time.time() - self._task_start_times[task_id]
            del self._task_start_times[task_id]

        message = f"Task completed: {task_id}"

        # 実行時間を追加
        if duration:
            message += f" (duration: {duration:.2f}s)"

        # 結果の要約を追加（50文字まで）
        if result_summary:
            summary = (
                result_summary[:50] + "..."
                if len(result_summary) > 50
                else result_summary
            )
            message += f" - {summary}"

        # メトリクスがあれば追加
        if task_id in self._task_metrics:
            metrics = self._task_metrics[task_id]
            metric_parts = [f"{k}: {v}" for k, v in metrics.items()]
            message += f" | Metrics: {', '.join(metric_parts)}"
            del self._task_metrics[task_id]

        self.logger.info(message)

    def log_task_error(
        self,
        task_id: str,
        error: Exception,
        context: str = None,
        will_retry: bool = False,
    ):
        """タスクエラーをログ（技術的詳細）"""
        message = f"Task error: {task_id}"

        if context:
            message += f" in {context}"

        message += f" - {type(error).__name__}: {str(error)}"

        if will_retry:
            message += " (will retry)"
            self.logger.warning(message)
        else:
            self.logger.error(message)

    def log_metric(self, task_id: str, metric_name: str, value: Any):
        """タスクのメトリクスを記録"""
        if task_id not in self._task_metrics:
            self._task_metrics[task_id] = {}

        self._task_metrics[task_id][metric_name] = value

        # 即座にログにも出力
        self.logger.debug(f"Metric - {task_id}: {metric_name}={value}")

    def log_processing(self, action: str, target: str, count: Optional[int] = None):
        """処理中の操作をログ"""
        message = f"Processing: {action} {target}"

        if count is not None:
            message += f" (count: {count})"

        self.logger.info(message)

    def log_state_change(
        self, component: str, old_state: str, new_state: str, reason: str = None
    ):
        """状態変更をログ"""
        message = f"State change: {component} {old_state} -> {new_state}"

        if reason:
            message += f" (reason: {reason})"

        self.logger.info(message)

    def log_performance(
        self, operation: str, duration: float, items_processed: Optional[int] = None
    ):
        """パフォーマンスデータをログ"""
        message = f"Performance: {operation} took {duration:.3f}s"

        if items_processed:
            rate = items_processed / duration if duration > 0 else 0
            message += f" ({items_processed} items, {rate:.1f} items/s)"

        self.logger.info(message)


# 実装例
class ExampleWorker(ImprovedLoggingMixin):
    """改善されたログを使用するワーカーの例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_task(self, task_id: str, data: Dict):
        # タスク開始
        self.log_task_start(task_id, "example")

        try:
            # 処理の各段階をログ
            self.log_processing("validating", "input data")

            # メトリクスを記録
            self.log_metric(task_id, "input_size", len(str(data)))

            # 実際の処理
            start_time = time.time()
            result = self._do_work(data)
            process_time = time.time() - start_time

            # パフォーマンスログ
            self.log_performance(
                "data processing", process_time, items_processed=len(result)
            )

            # メトリクスを追加
            self.log_metric(task_id, "output_items", len(result))

            # 完了
            self.log_task_complete(task_id, f"Processed {len(result)} items")

        except Exception as e:
            # エラーログ
            self.log_task_error(task_id, e, "process_task", will_retry=True)
            raise

    def _do_work(self, data: Dict) -> list:
        # 実際の処理（例）
        time.sleep(0.1)  # 処理をシミュレート
        return list(data.values())


# 既存コードの移行ガイド
MIGRATION_GUIDE = """
# ログ改善移行ガイド

## Before（既存のログ）
```python
self.logger.info("🚀 素晴らしいタスクを開始します！")
self.logger.info(f"✨ {task_id} の処理中...")
self.logger.info("🎉 完璧に成功しました！")
```

## After（改善後のログ）
```python
self.log_task_start(task_id, "code")
self.log_processing("generating", "Python code", count=3)
self.log_task_complete(task_id, "Generated 3 files")
```

## 移行手順
1. ImprovedLoggingMixinを継承
2. 誇張表現を含むログを特定
3. 適切なログメソッドに置き換え
4. メトリクスとパフォーマンスデータを追加

## チェックリスト
- [ ] 絵文字を削除または最小化
- [ ] 主観的表現を客観的データに置換
- [ ] 実行時間などの数値データを追加
- [ ] エラー詳細を技術的に記述
"""

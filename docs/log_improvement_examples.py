#!/usr/bin/env python3
"""
ログ改善移行の実例
TaskWorkerの Before/After 比較
"""

# ========================================
# BEFORE: 既存のログスタイル
# ========================================


class TaskWorkerOld:
    def process_message(self, ch, method, properties, body):
        """既存のログスタイル（誇張的）"""
        task = json.loads(body)
        task_id = task.get("task_id")

        # 誇張的な開始ログ
        self.logger.info(f"🚀 革新的なAIタスク {task_id} を開始します！")
        self.logger.info(f"✨ 素晴らしい処理を実行中...")

        try:
            # 処理
            self.logger.info(f"💡 天才的なアイデアで処理中！")
            result = self.execute_task(task)

            # 誇張的な成功ログ
            self.logger.info(f"🎉 完璧に成功しました！")
            self.logger.info(f"🌟 {task_id} は究極の結果を達成！")

            # Slack通知（誇張的）
            self.slack.send_message(
                f"🚀✨ 革新的なタスク {task_id} が完璧に完了！🎉\n" f"素晴らしい結果を生み出しました！💪"
            )

        except Exception as e:
            # 誇張的なエラーログ
            self.logger.error(f"😱 大変！エラーが発生！💥")
            self.logger.error(f"🔥 {task_id} で問題発生: {str(e)}")


# ========================================
# AFTER: 改善されたログスタイル
# ========================================

from core import BaseWorker
from core.improved_logging_mixin import ImprovedLoggingMixin
from libs.improved_slack_notifier import ImprovedSlackNotifier


class TaskWorkerNew(BaseWorker, ImprovedLoggingMixin):
    def __init__(self):
        BaseWorker.__init__(self, worker_type="task")
        ImprovedLoggingMixin.__init__(self)
        self.slack = ImprovedSlackNotifier()

    def process_message(self, ch, method, properties, body):
        """改善されたログスタイル（客観的）"""
        task = json.loads(body)
        task_id = task.get("task_id")
        task_type = task.get("type", "general")

        # 客観的な開始ログ
        self.log_task_start(task_id, task_type)
        self.log_metric(
            task_id,
            "queue_delay_ms",
            int((time.time() - task.get("created_at", time.time())) * 1000),
        )

        try:
            # 処理の各段階を記録
            self.log_processing("executing", f"{task_type} task")

            start_time = time.time()
            result = self.execute_task(task)
            execution_time = time.time() - start_time

            # パフォーマンスデータ
            self.log_performance("task execution", execution_time)

            # 結果のメトリクス
            if isinstance(result, dict):
                self.log_metric(task_id, "output_files", result.get("files_created", 0))
                self.log_metric(
                    task_id, "output_size_bytes", result.get("total_size", 0)
                )

            # 客観的な完了ログ
            summary = f"Type: {task_type}, Duration: {execution_time:.2f}s"
            if result.get("files_created"):
                summary += f", Files: {result['files_created']}"

            self.log_task_complete(task_id, summary)

            # Slack通知（データ中心）
            self.slack.send_task_notification(
                task_id=task_id,
                status="completed",
                duration=execution_time,
                details={
                    "worker": self.worker_id,
                    "type": task_type,
                    "files_created": result.get("files_created", 0),
                },
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # 技術的なエラーログ
            self.log_task_error(
                task_id, e, context=f"{task_type} task execution", will_retry=True
            )

            # エラー通知（技術的詳細）
            self.slack.send_alert(
                alert_type="task_failure",
                message=f"Task {task_id} failed: {type(e).__name__}: {str(e)}",
                severity="error",
            )

            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


# ========================================
# ログ出力の比較例
# ========================================

LOG_COMPARISON = """
# ログ出力の比較

## タスク開始時

### Before:
2025-07-02 10:00:00 INFO: 🚀 革新的なAIタスク code_20250702_100000 を開始します！
2025-07-02 10:00:00 INFO: ✨ 素晴らしい処理を実行中...

### After:
2025-07-02 10:00:00 INFO: Task started: code_20250702_100000 (type: code)
2025-07-02 10:00:00 DEBUG: Metric - code_20250702_100000: queue_delay_ms=123


## 処理中

### Before:
2025-07-02 10:00:01 INFO: 💡 天才的なアイデアで処理中！

### After:
2025-07-02 10:00:01 INFO: Processing: executing code task
2025-07-02 10:00:03 INFO: Performance: task execution took 2.341s


## タスク完了時

### Before:
2025-07-02 10:00:03 INFO: 🎉 完璧に成功しました！
2025-07-02 10:00:03 INFO: 🌟 code_20250702_100000 は究極の結果を達成！

### After:
2025-07-02 10:00:03 INFO: Task completed: code_20250702_100000 (duration: 2.34s) - Type: code, Duration: 2.34s, Files: 3


## Slack通知

### Before:
🚀✨ 革新的なタスク code_20250702_100000 が完璧に完了！🎉
素晴らしい結果を生み出しました！💪

### After:
Task completed: code_20250702_100000 | Duration: 2.34s | Worker: task-1 | Files: 3


## エラー時

### Before:
2025-07-02 10:05:00 ERROR: 😱 大変！エラーが発生！💥
2025-07-02 10:05:00 ERROR: 🔥 code_20250702_100500 で問題発生: Connection timeout

### After:
2025-07-02 10:05:00 WARNING: Task error: code_20250702_100500 in code task execution - ConnectionTimeout: Connection timeout (will retry)
2025-07-02 10:05:00 INFO: [ERROR] task_failure: Task code_20250702_100500 failed: ConnectionTimeout: Connection timeout
"""


# 移行チェックリスト
MIGRATION_CHECKLIST = """
# TaskWorker ログ改善チェックリスト

## 1. 依存関係の更新
- [ ] ImprovedLoggingMixinをインポート
- [ ] ImprovedSlackNotifierをインポート
- [ ] 多重継承の設定

## 2. ログメソッドの置換
- [ ] logger.info("🚀...") → log_task_start()
- [ ] logger.info("✨...") → log_processing()
- [ ] logger.info("🎉...") → log_task_complete()
- [ ] logger.error("😱...") → log_task_error()

## 3. メトリクスの追加
- [ ] 実行時間の計測
- [ ] 処理件数の記録
- [ ] エラー率の追跡
- [ ] リソース使用量

## 4. Slack通知の改善
- [ ] 絵文字を最小化
- [ ] 技術的データを含める
- [ ] モバイル対応フォーマット

## 5. テストと検証
- [ ] ログ出力の確認
- [ ] Slack通知のテスト
- [ ] パフォーマンスへの影響確認
"""
